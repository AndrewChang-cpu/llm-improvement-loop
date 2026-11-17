# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range through the measurement protocol: maximum is the widest label plus indentation; minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align, which vertically centers wrapped content within the console's current height using only content and newline characters.
- Give Align and VerticalCenter a repr.
- Make Align constrain its wrapped renderable to that renderable's measured maximum width, so shrink-to-fit renderables (such as a tree) center as one block instead of stretching to full width.
- Make Console.print render collected renderables with justify set to "default", while the justify argument still goes into renderable collection.

## Scope

In scope: Tree measurement in rich/tree.py; VerticalCenter, the repr methods, and the Align width constraint in rich/align.py; the justify option in Console.print's render options in rich/console.py; a CHANGELOG entry; tests.

Out of scope: a height field on ConsoleOptions (the reference CHANGELOG line describing one has no code behind it), version bumps, CONTRIBUTORS.md edits, and changes to main-guard demonstration blocks.

## Assumptions

- Console.size (a named tuple of width and height in lines) supplies height; without explicit height it falls back to terminal size, then 25 lines. ConsoleOptions has no height member.
- Measurement.get accepts strings, rich-cast objects, and renderables with a measurement method; it returns zeros when maximum width is below 1 and uses console width when no maximum width is passed.
- A Tree always has its own label; the root is at indent level 0.

## Terminology

- Measurement: a two-field named tuple (minimum, maximum) of character cell widths.
- Measured maximum: a renderable's measurement maximum, taken at console width when no maximum width is passed.
- Indent level: depth of a tree node below the root; each level adds four cells.
- Padding newlines: newline characters emitted as one segment to move content to vertical center, not spaces.

## Workflows

Tree measurement:

1. Walk depth-first from the root using an explicit stack of iterators (no recursion), with a level counter starting at 0.
2. For each visited node, measure its label with the max_width given to the Tree measurement, unreduced by indentation.
3. Let indent be 4 times the level. Minimum becomes the larger of its value and label minimum plus indent; maximum likewise with label maximum plus indent.
4. Descend into children only when the node is expanded and has children; adjust the level on descent and when a child list is exhausted.
5. Start minimum and maximum at 0; return a Measurement of the final values.

VerticalCenter rendering:

1. Render the wrapped renderable to lines with the given options, with padding to line width turned off.
2. Read height from the console size property.
3. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
4. If top space is positive, emit one segment of exactly that many newline characters.
5. For each line, emit its segments followed by one newline segment.
6. If bottom space is positive, emit one segment of that many newline characters.

When content fits, total newlines equal height minus 1. When content is at least as tall as the console, no padding is emitted and all lines still render.

VerticalCenter measurement: return the wrapped renderable's Measurement for the given max_width, unchanged.

Align repr: the class name, an opening parenthesis, the repr of the wrapped renderable, a comma and space, the repr of the alignment value, and a closing parenthesis. VerticalCenter repr: the same pattern with only the wrapped renderable's repr.

Align width constraint (rendering path only; Align's measurement is unchanged):

1. Measure the wrapped renderable with no maximum width, so console width applies; its maximum is the measured maximum.
2. With no explicit width, constrain the wrapped renderable to the measured maximum.
3. With explicit width W, constrain it to the smaller of the measured maximum and W.
4. Render the constrained renderable with the given options, then apply the existing alignment, padding, and style steps unchanged.

Console print justify: keep passing print's justify argument into renderable collection unchanged. For the render options used to render collected renderables, set justify to "default". All other values are unchanged.

## Data model

- Tree: existing fields unchanged; the new measurement reads only label, children, and expanded.
- VerticalCenter: one attribute, renderable, holding the wrapped object.
- Align: existing fields unchanged. No new state on Console, ConsoleOptions, or Measurement.

## API contracts

- Tree gains a measurement method taking a console and a maximum width and returning a Measurement. Constructor and add method unchanged.
- VerticalCenter: public class in rich.align. Constructor takes one positional renderable, typed with the renderable type alias. Implements the render protocol (console and options in; iterable of segments out), the measurement protocol, and repr. Inherits the Jupyter mixin, as Align does.
- Align gains a repr method returning a string. Other Align members unchanged.
- Console.print: signature unchanged; only the justify value in its render options changes.

## Module architecture

- Tree measurement: method of Tree in rich/tree.py, after the render method.
- VerticalCenter: rich/align.py, after Align and before the main-guard block. Not registered in rich/__init__.py.
- Align repr and width constraint: methods of Align. Justify change: the print method of Console; add no methods to Console.
- No new modules or files.

## Implementation constraints

- Read console height only from the console size property, never from a console height attribute or render options.
- Emit vertical padding as newline segments, never space-filled lines.
- Tree measurement is iterative with an explicit stack; no recursion, no depth cap.
- Pass unchanged max_width to child labels; add indentation only to measured widths.
- Tree.__rich_console__ and Align rendering stay unchanged apart from the width constraint.

## Dependencies

- rich/tree.py imports Measurement from the measure module; measure does not import tree, so no cycle is created.
- No new imports in rich/align.py or rich/console.py beyond existing ones, and no third-party dependencies.

## Naming

- Class name VerticalCenter, exactly. Method names follow the protocol names used by Align and Tree.
- Parameter names: renderable, console, options, max_width.

## Validation and error handling

No extra validation in VerticalCenter or Align; argument problems surface through existing render and measure paths. No new exception types. Negative padding counts are skipped, not raised. Errors from rendering or measuring the wrapped renderable propagate unchanged.

## Documentation

- VerticalCenter docstring: one-line summary and an Args section naming renderable with its type, following Align's docstring style.
- CHANGELOG.md, under the 9.8.0 section: mark the heading unreleased; add an Added subheading with two entries (rich_measure for tree; rich.align.VerticalCenter). Keep the existing markdown-over-standard-input entry. Add no ConsoleOptions height line.

## Performance

Tree measurement visits each node once, so cost is linear in node count. VerticalCenter renders the wrapped renderable once.

## Reliability

Empty or single-node trees return a valid Measurement. Content at least as tall as the console renders in full with no padding.

## Maintainability

Format with black defaults. Keep each file's existing import order. Match the file's iterative tree-walking style.

## Compatibility

Tree rendering output is unchanged. Align output changes only where the measured maximum is narrower than the otherwise applicable width (for example auto-width renderables). Console.print keeps its signature.

## Behavioral acceptance criteria

- A Tree with root "foo" and children "bar" and "musroom risotto" on a default console measures minimum 11 and maximum 19.
- A single-node Tree measures as that label does.
- repr on Align succeeds for left, center, and right alignments, returning the Align repr text.
- repr on VerticalCenter wrapping "foo" returns the VerticalCenter repr text.
- Rendering VerticalCenter of "foo" on a console of height 6, color disabled, output captured, yields two newlines, "foo", and three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3.
- Rendering VerticalCenter never raises an attribute error.
- Align without explicit width constrains the wrapped renderable to its measured maximum before alignment padding is computed; with explicit width W, to the smaller of that maximum and W.
- Console.print with a justify argument still passes it into renderable collection, and render options carry justify "default".

## Test requirements

- tests/test_align.py: import VerticalCenter beside Align at module top. Add a repr test covering Align with left, center, and right, and VerticalCenter; add rendering and measurement tests matching the acceptance criteria.
- tests/test_tree.py: import Measurement at module top after console and before tree. Add a test measuring the acceptance-example tree on a default console against the expected Measurement.
- Existing tests in both files must still pass. No other test files change.
