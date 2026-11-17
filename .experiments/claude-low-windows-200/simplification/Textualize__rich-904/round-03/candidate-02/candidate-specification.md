# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range through the measurement protocol. Maximum is the widest label plus its indentation. Minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align, which vertically centers wrapped content within the console height.
- Give Align and VerticalCenter a repr.
- Make Align constrain its wrapped renderable to the measured maximum width, so shrink-to-fit renderables such as trees center as one block.
- Make Console.print render collected renderables with justify set to "default". The justify argument still goes into renderable collection.

## Scope

In scope: Tree measurement in rich/tree.py; VerticalCenter, reprs, and the Align width constraint in rich/align.py; the justify option in rich/console.py; a CHANGELOG entry; tests.

Out of scope: a height field on ConsoleOptions, despite the reference CHANGELOG mentioning one; version bumps; CONTRIBUTORS.md; main-guard demonstrations.

## Assumptions

- The Console size property (width and height in lines) supplies height. Without an explicit height it falls back to terminal size, then to 25 lines. ConsoleOptions has no height member.
- The Measurement get class method accepts strings, rich-cast objects, and renderables with a measurement method. It returns zeros when maximum width is below 1, and uses console width when no maximum width is passed.
- A Tree always has its own label. The root is at indent level 0.

## Terminology

- Measurement: a two-field named tuple (minimum, maximum) of character cell widths.
- Measured maximum: the maximum field of a renderable's measurement, taken at console width when no maximum width is passed.
- Indent level: depth of a tree node below the root. Each level adds four cells.
- Padding newlines: newline characters emitted as one segment, not spaces.

## Workflows

### Tree measurement

1. Walk depth-first from the root using an explicit stack of iterators, with a level counter starting at 0.
2. For each node, measure its label with the given max_width, without reducing it by indentation.
3. Let indent be four times the level. Minimum becomes the larger of its current value and label minimum plus indent. Maximum likewise uses label maximum plus indent.
4. Descend into children only when the node is expanded and has children. Increase the level on descent and decrease it when a child list is exhausted.
5. Start minimum and maximum at 0. Return a Measurement of the final values.

### VerticalCenter rendering

1. Render the wrapped renderable to lines with the given options, with padding to line width turned off.
2. Read console height from the console size property.
3. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
4. If top space is positive, emit one segment of exactly that many newline characters.
5. For each line, emit its segments followed by one newline segment.
6. If bottom space is positive, emit one segment of exactly that many newline characters.

### VerticalCenter measurement

Delegate to the wrapped renderable's measurement with the given max_width. Return its Measurement unchanged.

### Reprs

Align's repr is the class name, then in parentheses the repr of the wrapped renderable and the repr of the alignment value, separated by a comma and a space. VerticalCenter's repr omits the alignment part.

### Align width constraint

This applies only to rendering. Align's measurement method is unchanged.

1. Measure the wrapped renderable with no maximum width. Take its maximum as the measured maximum.
2. With no explicit width, constrain the wrapped renderable to the measured maximum. With explicit width W, constrain it to the smaller of the measured maximum and W.
3. Render the constrained renderable, then apply the existing alignment, padding, and style steps unchanged.

### Console print justify

Pass print's justify argument into renderable collection unchanged. In the render options for collected renderables, set justify to "default".

## Data model and API contracts

- Tree gains a measurement method taking a console and a maximum width and returning a Measurement. Its fields, constructor, and add method are unchanged. The measurement reads only label, children, and expanded.
- VerticalCenter is a public class in rich.align with one attribute, renderable. Its constructor takes one positional renderable parameter, typed with the renderable type alias. It implements the render protocol (receives console and options, returns an iterable of segments), the measurement protocol, and repr. It inherits the Jupyter mixin, as Align does.
- Align gains a repr method returning a string and gains no state. Its other methods are unchanged.
- Console.print keeps its signature. Only the justify value in its render options changes.

## Module architecture

- Tree measurement: a Tree method in rich/tree.py, after the render method. Importing Measurement from the measure module creates no cycle, because measure does not import tree.
- VerticalCenter: rich/align.py, after Align and before the main-guard block. Do not register it in rich/__init__.py.
- No new modules, files, imports, or dependencies.

## Implementation constraints

- Read console height only from the console size property, never from a height attribute or from render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement Tree measurement iteratively with an explicit stack and no depth cap.
- Pass max_width unchanged to child labels. Indentation is added only to measured widths.
- Tree.__rich_console__ and Align rendering stay unchanged apart from the width constraint.
- The class name is VerticalCenter, exactly. Method names follow the protocol names used by Align and Tree.
- No new exception types or validation. Negative padding counts are skipped. Errors from the wrapped renderable propagate unchanged.

## Documentation

- VerticalCenter docstring: a one-line summary and an Args section naming renderable with its type, following Align's style.
- CHANGELOG.md: under the 9.8.0 section, mark the heading unreleased. Add an Added subheading with two entries: rich_measure for tree, and rich.align.VerticalCenter. Keep the existing markdown-over-standard-input entry.
- Format with black defaults and keep existing import order.

## Behavioral acceptance criteria

- A Tree with root "foo" and children "bar" and "musroom risotto", measured on a default console, returns minimum 11 and maximum 19. A single-node Tree returns that label's own measurement.
- repr on Align succeeds for left, center, and right alignments. repr on VerticalCenter wrapping "foo" returns its repr text.
- Rendering VerticalCenter of "foo" on a console of height 6, color disabled, with output captured, yields two newlines, "foo", and three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3. Rendering VerticalCenter never raises an attribute error.
- Align without explicit width constrains the wrapped renderable to its measured maximum before padding is computed. With explicit width W, it constrains to the smaller of the measured maximum and W.
- Empty or single-node trees return a valid Measurement. Content at least as tall as the console renders with no padding.

## Test requirements

- tests/test_align.py: import VerticalCenter beside Align. Add repr, rendering, and measurement tests matching the acceptance criteria.
- tests/test_tree.py: import Measurement after console and before tree. Add a test measuring the acceptance-example tree on a default console.
- Existing tests in both files must still pass. No other test files change.
