# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range through the measurement protocol: maximum is the widest label plus indentation; minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align, which vertically centers wrapped content within the console height.
- Give Align and VerticalCenter a repr.
- Make Align constrain its wrapped renderable to the measured maximum width, so shrink-to-fit renderables such as trees center as one block.
- Make Console.print render collected renderables with justify set to "default", while still passing the justify argument into renderable collection.

## Scope

In scope: Tree measurement in rich/tree.py; VerticalCenter, reprs, and the width constraint in rich/align.py; justify handling in rich/console.py; a CHANGELOG entry; tests.

Out of scope: a ConsoleOptions height field (despite the reference CHANGELOG line), version bumps, CONTRIBUTORS.md, and main-guard demonstration blocks.

## Assumptions

- The Console size property (width and height in lines) supplies height. Without an explicit height it falls back to terminal size, then 25 lines.
- ConsoleOptions has no height member.
- Measurement.get accepts strings, rich-cast objects, and renderables with a measurement method. It returns zeros when maximum width is below 1 and uses console width when no maximum width is passed.
- A Tree always has its own label. The root is at indent level 0.

## Terminology

- Measurement: a two-field named tuple (minimum, maximum) of character cell widths.
- Measured maximum: a renderable's measurement maximum, taken at console width when no maximum width is passed.
- Indent level: depth of a tree node below the root. Each level adds four cells.

## Workflows

Tree measurement:

1. Walk depth-first from the root with an explicit stack of iterators (no recursion), tracking a level counter starting at 0.
2. Measure each node's label with the max_width given to Tree measurement, without reducing it by indentation.
3. Let indent be four times the level. Minimum becomes the larger of its current value and label minimum plus indent; maximum likewise uses label maximum plus indent.
4. Descend into children only when the node is expanded and has children. Increase the level on descent; decrease it when a child list is exhausted.
5. Start minimum and maximum at 0. Return a Measurement of the final values.

VerticalCenter rendering:

1. Render the wrapped renderable to lines with the given options, with padding to line width turned off.
2. Read height from the console size property.
3. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
4. If top space is positive, emit one segment of exactly that many newlines.
5. Emit each line's segments followed by one newline segment.
6. If bottom space is positive, emit one segment of that many newlines.

VerticalCenter measurement: delegate to the wrapped renderable's measurement with the given max_width and return its Measurement unchanged.

Reprs: Align's repr is the class name, an opening parenthesis, the wrapped renderable's repr, a comma and space, the alignment value's repr, and a closing parenthesis. VerticalCenter's repr omits the alignment part.

Align width constraint (rendering path only; measurement is unchanged):

1. Measure the wrapped renderable with no maximum width. Its maximum is the measured maximum.
2. With no explicit width, constrain the wrapped renderable to the measured maximum. With explicit width W, constrain it to the smaller of the measured maximum and W.
3. Render the constrained renderable, then apply the existing alignment, padding, and style steps unchanged.

Console print justify: pass print's justify argument into renderable collection unchanged. In the render options for collected renderables, set justify to "default".

## Data model

- Tree: existing fields unchanged. Measurement reads only label, children, and expanded.
- VerticalCenter: one attribute, renderable, holding the wrapped object.

## API contracts

- Tree gains a measurement method taking a console and a maximum width and returning a Measurement. Constructor and add are unchanged.
- VerticalCenter is a public class in rich.align, named exactly that. Its constructor takes one positional renderable parameter, typed with the renderable type alias. It implements render (receives console and options, returns an iterable of segments), measurement, and repr. It inherits the Jupyter mixin, as Align does.
- Align gains a repr method. Other methods are unchanged.
- Console.print keeps its signature; only the justify value in render options changes.

## Module architecture

- Tree measurement is a Tree method in rich/tree.py, placed after the render method.
- VerticalCenter goes in rich/align.py after Align and before the main-guard block. Do not register it in rich/__init__.py. No new modules or files.

## Implementation constraints

- Read console height only from the console size property, never from a height attribute or render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement Tree measurement iteratively with an explicit stack; no recursion, no depth cap.
- Pass max_width unchanged to child labels; add indentation only to measured widths.
- Format with black defaults. Tree.__rich_console__ and Align rendering stay unchanged apart from the width constraint.

## Dependencies

- rich/tree.py imports Measurement from the measure module. The measure module does not import tree, so no cycle forms.
- No new imports in rich/align.py or rich/console.py, and no third-party dependencies.

## Error handling

No new exception types or validation. Negative padding counts are skipped, not raised. Errors from the wrapped renderable propagate unchanged.

## Documentation

- VerticalCenter docstring: a one-line summary and an Args section naming renderable with its type, following the Align docstring style.
- CHANGELOG.md: under the 9.8.0 section, mark the heading unreleased. Add an Added subheading with entries for rich_measure for tree and rich.align.VerticalCenter. Keep the existing markdown-over-standard-input entry. Add no height line.

## Performance

Tree measurement visits each node once, so cost is linear in node count. Empty or single-node trees return a valid Measurement. Content at least as tall as the console renders in full with no padding.

## Behavioral acceptance criteria

- A Tree with root "foo" and children "bar" and "musroom risotto", measured on a default console, returns minimum 11 and maximum 19.
- A single-node Tree returns that label's own measurement.
- repr on Align succeeds for left, center, and right alignments. repr on VerticalCenter wrapping "foo" returns its repr text.
- Rendering VerticalCenter of "foo" on a console of height 6, color disabled, with output captured, yields two newlines, "foo", and three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3.
- Align without explicit width constrains the wrapped renderable to its measured maximum before alignment padding is computed. With explicit width W, it constrains to the smaller of the measured maximum and W.
- Console.print with a justify argument passes it into renderable collection, and render options carry justify "default".

## Test requirements

- tests/test_align.py: import VerticalCenter at module top beside Align. Add repr, rendering, and measurement tests matching the acceptance criteria.
- tests/test_tree.py: import Measurement at module top after console and before tree. Add a test measuring the acceptance-example tree on a default console.
- Existing tests in both files must still pass. No other test files change.
