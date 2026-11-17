# Add rich_measure to Tree and VerticalCenter

## Goals

- Let Tree report its natural width range through the measurement protocol. The maximum is the widest label plus nesting indentation. The minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align. It vertically centers wrapped content within the console's current height and emits only content and newline characters.
- Give Align and VerticalCenter a repr.
- Make Align constrain its wrapped renderable to that renderable's measured maximum width, so a shrink-to-fit renderable (such as a tree or a panel without explicit width) is centered as one block instead of stretched to full width.
- Make Console.print render collected renderables with the justify option set to "default", while the justify argument still goes into renderable collection.

## Scope

In scope: Tree measurement in rich/tree.py; VerticalCenter and the repr methods of Align and VerticalCenter in rich/align.py; the width constraint in Align rendering; the justify option in Console.print in rich/console.py; a CHANGELOG entry; tests.

Out of scope:
- Adding a height field to ConsoleOptions. The reference CHANGELOG line claiming this has no code change behind it; do not add it.
- Bumping the version in pyproject.toml.
- Editing CONTRIBUTORS.md.
- Changing the demonstration block under the main guard in either module.

## Assumptions

- Console.size exposes width and height in lines. With no explicit height, it falls back to the terminal size, then to 25 lines.
- ConsoleOptions has no height member. Read height from the console, never from options.
- The existing Measurement get class method accepts strings, rich-cast objects, and renderables with a measurement method. It returns zeros when the maximum width is below 1, and uses the console width when no maximum width is passed.
- A Tree always has its own label. The root is at indent level 0.

## Terminology

- Measurement: a two-field named tuple (minimum, maximum) of character cell widths.
- Measured maximum: the maximum field of a renderable's measurement, taken at console width when no maximum width is passed.
- Measurement method: a renderable method taking a console and a maximum width and returning a Measurement. Use the name already used across rich.
- Indent level: depth of a tree node below the root. Each level adds four cells.
- Padding newlines: newline characters emitted as one segment to move content to the vertical center. They are not spaces.

## Workflows

Tree measurement:
1. Walk depth-first from the root using an explicit stack of iterators, not recursion. Start a level counter at 0.
2. For each node, measure its label through the measurement entry point, passing the max_width given to Tree measurement. Do not reduce max_width by indentation.
3. Let indent be 4 times the level. Minimum becomes the larger of the current minimum and label minimum plus indent. Maximum becomes the larger of the current maximum and label maximum plus indent.
4. Descend into children only when the node is expanded and has children. Increase the level on descent and decrease it when a child list is exhausted.
5. Start minimum and maximum at 0. Return a Measurement of the final values.

VerticalCenter rendering:
1. Render the wrapped renderable to a list of lines using the given options, with padding to line width turned off.
2. Read console height from the console size property.
3. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
4. If top space is positive, emit one segment containing exactly that many newline characters.
5. For each line, emit its segments followed by one newline segment.
6. If bottom space is positive, emit one segment containing exactly that many newline characters.

When content fits, the total newlines emitted equal height minus 1. When content is as tall as or taller than the console, no padding is emitted and all lines still render.

VerticalCenter measurement: delegate to the measurement entry point on the wrapped renderable with the given max_width, and return that Measurement unchanged.

Align repr: the class name Align, an opening parenthesis, the repr of the wrapped renderable, a comma and space, the repr of the alignment value, and a closing parenthesis.

VerticalCenter repr: the class name VerticalCenter, an opening parenthesis, the repr of the wrapped renderable, and a closing parenthesis.

Align width constraint (rendering path only; Align measurement is unchanged):
1. Measure the wrapped renderable through the measurement entry point with no maximum width, so the console width is used. Take its maximum as the measured maximum.
2. With no explicit width, constrain the wrapped renderable to the measured maximum.
3. With explicit width W, constrain it to the smaller of the measured maximum and W.
4. Render the constrained renderable with the given options, then apply the existing alignment, padding, and style steps unchanged.

Console print justify: keep passing the justify argument into renderable collection unchanged. For the render options used to render the collected renderables, set justify to "default" instead of the argument. All other option values are unchanged.

## Data model

- Tree: existing label, style, guide style, children list, expanded flag, and highlight flag. Measurement reads label, children, and expanded only.
- VerticalCenter: one attribute, renderable, holding the wrapped object.
- Align: existing fields (renderable, alignment, style, pad, width). No new fields.
- Measurement: unchanged.
- Console size: a named tuple with width and height in lines.
- No new persistent data and no new state on Console or ConsoleOptions.

## API contracts

- Tree: gains a measurement method taking a console and a maximum width and returning a Measurement. The constructor and add method are unchanged.
- VerticalCenter: public class in rich.align. The constructor takes one positional renderable parameter, typed with the renderable type alias, and no other required parameters. It implements the render protocol (console and options in, iterable of segments out), the measurement protocol, and repr. It inherits the Jupyter mixin, as Align does.
- Align: gains a repr method returning a string. The constructor and alignment shortcut methods are unchanged.
- Console.print: signature unchanged. Only the justify value in the render options changes.

## Module architecture

- Tree measurement: a method of Tree in rich/tree.py, placed after the render method.
- VerticalCenter: in rich/align.py, after the Align class and before the main-guard block. Do not add it to rich/__init__.py or any registry.
- Align repr and width constraint: methods of Align in rich/align.py.
- Justify change: the print method of Console in rich/console.py. Add no new Console methods.
- No new modules or files beyond existing modules and test files.

## Implementation constraints

- Read console height only from the console size property. Do not read a height attribute from the console or from render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement Tree measurement iteratively with an explicit stack. No recursion and no depth cap.
- Do not change the max_width passed to child labels; indentation is added to measured widths only.
- Keep Tree.__rich_console__ behavior unchanged. Keep Align rendering unchanged apart from the width constraint.

## Dependencies

- rich/tree.py imports Measurement from the measure module. The measure module does not import tree, so no cycle arises.
- rich/align.py already imports Measurement, Segment, JupyterMixin, and Constrain. No new imports.
- rich/console.py needs no new imports. No new third-party dependencies.

## Naming

- The class is named VerticalCenter, exactly.
- Method names follow the existing protocol names used by Align and Tree.
- Parameter names follow existing ones: renderable, console, options, max_width.

## Validation

- Add no extra validation to VerticalCenter. Argument problems surface through the existing render and measure paths.
- Add no alignment-value checks to Align beyond existing ones.

## Error handling

- The feature adds no new exception types. Negative padding counts are skipped, not raised.
- Errors from rendering or measuring the wrapped renderable propagate unchanged.

## Documentation

- VerticalCenter class docstring: a one-line summary, then an Args section naming the renderable parameter and its type. Follow the Align docstring style.
- CHANGELOG.md: under the 9.8.0 section, mark the heading as unreleased. Add an Added subheading with two entries: added rich_measure for tree, and added rich.align.VerticalCenter. Keep the existing entry about markdown over standard input. Add no ConsoleOptions height line.

## Performance

- Tree measurement visits each node once, so cost is linear in node count.
- VerticalCenter renders the wrapped renderable once and emits segments without re-rendering.

## Reliability

- Negative padding counts never produce output and never raise.
- Content at least as tall as the console renders in full with no padding.
- An empty or single-node tree still returns a valid Measurement.

## Maintainability

- Format new code with black defaults.
- Keep imports in the order each file already uses. In tests/test_tree.py, import the console, measure, and tree modules in that order.
- Place test imports at module top, not inside test functions.
- Match the file's existing iterative tree-walking style.

## Compatibility

- Tree rendering output is unchanged.
- Align output changes only where the wrapped renderable's measured maximum is narrower than the width that would otherwise apply, for example auto-width renderables. This is the required width behavior.
- Console.print keeps its signature.

## Behavioral acceptance criteria

- A Tree with root "foo" and two children, "bar" and "musroom risotto", measured with a default console, returns minimum 11 and maximum 19.
- A single-node Tree returns its label's own measurement.
- repr on Align succeeds for each of the three alignment values and returns the text in the Align repr workflow.
- repr on a VerticalCenter wrapping "foo" returns the text in the VerticalCenter repr workflow.
- Rendering VerticalCenter of "foo" on a console of height 6, with color disabled and output captured, yields two newlines, then "foo", then one newline, then two newlines.
- Measuring VerticalCenter of "foo" with a default console returns minimum 3 and maximum 3.
- Rendering VerticalCenter never raises an attribute error.
- When wrapped content is at least as tall as the console, no padding newlines are emitted.
- Align with no explicit width constrains the wrapped renderable to its measured maximum before alignment padding is computed.
- Align with explicit width W constrains the wrapped renderable to the smaller of the measured maximum and W.
- Console.print with a justify argument still passes it into renderable collection, and the render options carry justify "default".

## Test requirements

- tests/test_align.py: import VerticalCenter at module top alongside Align. Add a repr test calling repr on Align with the left, center, and right values, and on a VerticalCenter instance. Add a VerticalCenter rendering test and a measurement test matching the acceptance criteria.
- tests/test_tree.py: import Measurement at module top, after the console import and before the tree import. Add a test that builds the acceptance tree, measures it with a default console, and compares the result to the expected Measurement.
- Existing tests in both files must still pass. No other test files change.
