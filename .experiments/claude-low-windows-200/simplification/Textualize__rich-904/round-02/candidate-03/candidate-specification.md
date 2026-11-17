# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range through the measurement protocol: maximum is the widest label plus its indentation; minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align. It vertically centers wrapped content within the console's current height, emitting only content and newline characters.
- Give Align and VerticalCenter a repr.
- Make Align constrain its wrapped renderable to that renderable's measured maximum width, so shrink-to-fit renderables (such as a tree or a panel without explicit width) center as one block instead of stretching to full width.
- Make Console.print render collected renderables with justify set to "default", while the justify argument still goes into renderable collection.

## Scope

In scope: the files named under Module architecture, a CHANGELOG entry, and tests.

Out of scope: a height field on ConsoleOptions (do not add one, despite the reference CHANGELOG line); the pyproject.toml version; CONTRIBUTORS.md; the main-guard demonstration blocks.

## Assumptions

- Console.size (a named tuple of width and height in lines) supplies height. Without an explicit height it falls back to terminal size, then to 25 lines.
- ConsoleOptions has no height member; height comes only from the console.
- Measurement.get accepts strings, rich-cast objects, and renderables with a measurement method. It returns zeros when maximum width is below 1, and uses console width when no maximum width is passed.
- A Tree always has its own label; the root is at indent level 0.

## Terminology

- Measurement: a two-field named tuple (minimum, maximum) of character cell widths.
- Measured maximum: the maximum field of a renderable's measurement, taken at console width when no maximum width is passed.
- Indent level: depth of a tree node below the root. Each level adds four cells.

## Workflows

### Tree measurement

1. Walk depth-first from the root using an explicit stack of iterators (no recursion), with a level counter starting at 0.
2. For each visited node, measure its label through the measurement entry point with the max_width given to the Tree measurement. Do not reduce max_width by indentation.
3. Let indent be 4 times the level. Minimum becomes the larger of its current value and label minimum plus indent; maximum likewise with label maximum plus indent.
4. Descend into children only when the node is expanded and has children. Increase the level on descent; decrease it when a child list is exhausted.
5. Start minimum and maximum at 0; return a Measurement of the final values.

### VerticalCenter rendering

1. Render the wrapped renderable to a list of lines with the given options, with padding to line width turned off.
2. Read console height from the console size property.
3. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
4. If top space is positive, emit one segment of exactly that many newline characters.
5. For each line, emit its segments followed by one newline segment.
6. If bottom space is positive, emit one segment of exactly that many newline characters.

When content fits, total newlines emitted equal height minus 1. Content at least as tall as the console gets no padding and still renders in full.

### VerticalCenter measurement

Delegate to the measurement entry point on the wrapped renderable with the given max_width and return its Measurement unchanged.

### Align repr

Return "Align(", the repr of the wrapped renderable, ", ", the repr of the alignment value, and ")".

### VerticalCenter repr

Return "VerticalCenter(", the repr of the wrapped renderable, and ")".

### Align width constraint

Applies only to Align's rendering path; Align's measurement method is unchanged.

1. Measure the wrapped renderable through the measurement entry point with no maximum width, so console width applies; take its maximum as the measured maximum.
2. With no explicit width, constrain the wrapped renderable to the measured maximum.
3. With explicit width W, constrain it to the smaller of the measured maximum and W.
4. Render the constrained renderable with the given options, then apply the existing alignment, padding, and style steps unchanged.

### Console print justify

Keep passing print's justify argument into renderable collection unchanged. For the render options used to render the collected renderables, set justify to "default". All other values are unchanged.

## Data model

- Tree: existing fields unchanged. The new measurement reads only label, children, and expanded.
- VerticalCenter: one attribute, renderable, holding the wrapped object.
- Align: existing fields (renderable, alignment, style, pad, width). No new fields.
- Measurement is not modified. No new state on Console, ConsoleOptions, or Measurement.

## API contracts

- Tree gains a measurement method taking a console and a maximum width and returning a Measurement. Constructor and add method unchanged.
- VerticalCenter: public class in rich.align. Constructor takes one positional renderable parameter, typed with the renderable type alias. Implements the render protocol (receives console and options, returns an iterable of segments), the measurement protocol, and repr. Inherits the Jupyter mixin, as Align does.
- Align gains a repr method returning a string. Constructor and alignment shortcut methods unchanged.
- Console.print: signature unchanged; only the justify value in its render options changes.

## Module architecture

- Tree measurement: a method of Tree in rich/tree.py, placed after the render method.
- VerticalCenter: rich/align.py, after Align and before the main-guard block. Not added to rich/__init__.py or any registry.
- Align repr and width constraint: methods of Align in rich/align.py.
- Justify change: in the print method of Console in rich/console.py. Do not add methods to Console.
- No new modules or files.

## Implementation constraints

- Read console height only from the console size property; never from a console height attribute or from render options.
- Emit vertical padding as newline segments, never space-filled lines.
- Implement the Tree measurement iteratively with an explicit stack. No recursion, no depth cap.
- Pass unchanged max_width to child labels; indentation is added only to measured widths.
- Tree.__rich_console__ and Align rendering stay unchanged apart from the required width constraint.

## Dependencies

- rich/tree.py imports Measurement from the measure module. The measure module does not import tree, so no cycle is created.
- rich/align.py already imports Measurement, Segment, JupyterMixin, and Constrain; no new imports.
- rich/console.py needs no new imports or third-party dependencies.

## Naming

Class name VerticalCenter, exactly. Method names follow the existing protocol names used by Align and Tree.

## Validation

No extra validation in VerticalCenter or Align; argument problems surface through existing render and measure paths.

## Error handling

No new exception types. Negative padding counts are skipped, not raised. Errors from rendering or measuring the wrapped renderable propagate unchanged.

## Documentation

- VerticalCenter class docstring: a one-line summary and an Args section naming renderable with its type, following the Align docstring style.
- CHANGELOG.md: under the 9.8.0 section, mark the heading unreleased. Add an Added subheading with two entries: rich_measure for tree, and rich.align.VerticalCenter. Keep the existing markdown-over-standard-input entry. Add no ConsoleOptions height line.

## Performance

Tree measurement visits each node once, so cost is linear in node count. VerticalCenter renders the wrapped renderable once.

## Maintainability

Format with black defaults. Keep imports sorted in each file's existing order. In tests/test_tree.py, imports are console, measure, then tree. Match the file's iterative tree-walking style.

## Behavioral acceptance criteria

- Measuring a Tree with root "foo" and children "bar" and "musroom risotto" on a default console returns minimum 11 and maximum 19.
- Measuring a single-node Tree returns that label's own measurement; empty or single-node trees return a valid Measurement.
- repr on Align succeeds for each of the three alignment values, returning the Align repr text.
- repr on VerticalCenter wrapping "foo" returns the VerticalCenter repr text.
- Rendering VerticalCenter of "foo" on a console of height 6, color disabled, output captured, yields two newlines, "foo", and three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3.
- Rendering VerticalCenter never raises an attribute error.
- Content at least as tall as the console emits no padding newlines; negative padding counts never produce output or raise.
- Align without explicit width constrains the wrapped renderable to its measured maximum before alignment padding is computed.
- Align with explicit width W constrains to the smaller of the measured maximum and W.
- Console.print with a justify argument still passes it into renderable collection, and render options carry justify "default".

## Test requirements

- tests/test_align.py: import VerticalCenter at module top beside Align. Add a repr test covering Align with left, center, and right, and a VerticalCenter. Add rendering and measurement tests matching the acceptance criteria.
- tests/test_tree.py: import Measurement at module top after console and before tree. Add a test building the acceptance-example tree, measuring it on a default console, and comparing with the expected Measurement.
- Existing tests in both files must still pass. No other test files change.
