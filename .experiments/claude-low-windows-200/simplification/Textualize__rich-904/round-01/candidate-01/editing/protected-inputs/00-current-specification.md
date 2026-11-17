# Add rich_measure to Tree and VerticalCenter

## Goals

- Let the Tree renderable report its natural width range through the measurement protocol. Measuring a tree returns the widest label plus its nesting indentation as the maximum, and the widest unbreakable label content plus indentation as the minimum.
- Add a public renderable, VerticalCenter, in the rich.align module. It vertically centers its wrapped content within the console's current height, and it emits only content and newline characters.
- Give Align and VerticalCenter a repr text, as described in the workflows.
- Make Align constrain its wrapped renderable to that renderable's measured maximum width, so that a shrink-to-fit renderable (for example a tree or a panel without an explicit width) is centered as one block instead of being stretched to the full available width.
- Make Console.print render the collected renderables with the justify option set to "default", while the justify argument still goes into renderable collection.

## Scope

In scope:
- Tree measurement (the Tree class in rich/tree.py).
- The VerticalCenter class and the repr methods of Align and VerticalCenter (in rich/align.py).
- The width constraint applied when Align renders its wrapped renderable (in rich/align.py).
- The justify option of the render options that Console.print builds for rendering (in rich/console.py).
- A CHANGELOG entry and tests for the above.

Out of scope:
- Adding a height field to ConsoleOptions. The CHANGELOG line in the reference that says so is not backed by any code change; do not add it.
- Bumping the package version in pyproject.toml.
- Editing CONTRIBUTORS.md.
- Changing the demonstration block that runs under the main guard in either module.

## Assumptions

- The Console already exposes a size property. Its height member gives the console height in lines. When no explicit height is set, it falls back to the terminal size and then to a default of 25 lines.
- ConsoleOptions has no height member. Height is read from the console, not from the options.
- The existing measurement entry point, the get class method of Measurement, accepts strings, rich-cast objects, and renderables that have a measurement method. It returns zeros when the maximum width is below 1. When no maximum width is passed, it uses the console width.
- A Tree always has its own label. The root node is at indent level 0.

## Terminology

- Measurement: a two-field named tuple (minimum, maximum) of character cell widths.
- Measured maximum: the maximum field of a renderable's measurement, taken at the console width when no maximum width is passed.
- Measurement method: a method on a renderable that takes the console and a maximum width and returns a Measurement. The method name is the one already used across rich.
- Indent level: the depth of a tree node below the root. Each level adds four cells of indentation.
- Padding newlines: newline characters emitted as a single segment to move content to the vertical center. They are not space characters.

## Workflows

### Tree measurement

1. Start a depth-first walk from the root node, using an explicit stack of iterators (not recursion) and a level counter that starts at 0.
2. For each visited node, measure its label through the measurement entry point, passing the max_width that was given to the Tree measurement. Do not reduce max_width by indentation.
3. Let indent be 4 times the current level. Update minimum as the larger of the current minimum and (label minimum plus indent). Update maximum as the larger of the current maximum and (label maximum plus indent).
4. Descend into a node's children only when that node is expanded and has children. Increase the level when descending, and decrease it when a child list is exhausted.
5. Start minimum and maximum at 0. Return a Measurement built from the final minimum and maximum.

### VerticalCenter rendering

1. Render the wrapped renderable to a list of lines using the options given to the renderable, with padding to the line width turned off.
2. Read the console height from the console size property.
3. Compute top space as the floor of (height minus line count) divided by 2. Compute bottom space as height minus top space minus line count minus 1.
4. If top space is greater than 0, emit one segment that contains exactly top space newline characters.
5. For each line, emit that line's segments followed by one newline segment.
6. If bottom space is greater than 0, emit one segment that contains exactly bottom space newline characters.

When content fits, the total number of newline characters emitted is height minus 1. When content is as tall as or taller than the console, top and bottom space are not positive, so no padding is emitted and all lines still render.

### VerticalCenter measurement

Delegate to the measurement entry point on the wrapped renderable with the given max_width, and return that Measurement unchanged.

### Align repr

Return text made of the class name Align, an opening parenthesis, the repr of the wrapped renderable, a comma and a space, the repr of the alignment value, and a closing parenthesis.

### VerticalCenter repr

Return text made of the class name VerticalCenter, an opening parenthesis, the repr of the wrapped renderable, and a closing parenthesis.

### Align width constraint

This applies only to the rendering path of Align. Align's measurement method is unchanged.

1. Measure the wrapped renderable through the measurement entry point with no maximum width passed, so that the console width is used, and take its maximum as the measured maximum.
2. If the Align has no explicit width, constrain the wrapped renderable to the measured maximum.
3. If the Align has an explicit width, constrain the wrapped renderable to the smaller of the measured maximum and the explicit width.
4. Render the constrained renderable with the given options, then apply the existing alignment, padding, and style steps unchanged.

### Console print justify

Keep passing the justify argument of print into renderable collection, unchanged. For the render options used to render the collected renderables, set the justify option to the value "default" instead of the justify argument. All other render option values are unchanged.

## Data model

- Tree: the existing label, style, guide style, children list, expanded flag, and highlight flag. The new measurement reads label, children, and expanded only.
- VerticalCenter: one attribute, renderable, holding the wrapped object.
- Align: its existing fields (renderable, alignment, style, pad, width). No new fields.
- Measurement: a two-field named tuple (minimum, maximum). It is not modified.
- Console size: a named tuple with width and height. Height is in lines.
- No new persistent data and no new state on Console or ConsoleOptions.

## API contracts

- Tree measurement: the Tree class gains a measurement method that takes a console and a maximum width and returns a Measurement. Its public constructor and its add method are unchanged.
- VerticalCenter: a public class in rich.align. Its constructor takes one positional renderable parameter, typed as the renderable type alias, and no other required parameters. It implements the render protocol (it receives a console and options and returns an iterable of segments), the measurement protocol described above, and a repr method as described in the VerticalCenter repr workflow. It inherits the Jupyter mixin, as Align does.
- Align: the Align class gains a repr method that returns a string, as described in the Align repr workflow. The Align constructor and its alignment shortcut methods are unchanged.
- Console.print: the signature is unchanged. The only change is the justify value in the render options it builds for rendering.

## Module architecture

- The Tree measurement lives in rich/tree.py as a method of Tree, placed after the render method.
- VerticalCenter lives in rich/align.py, placed after the Align class and before the main-guard block. It is not added to rich/__init__.py or to any registry.
- The Align repr method is a method of the Align class. The Align width constraint is in the rendering method of Align, in rich/align.py.
- The print justify change is in the print method of Console in rich/console.py. Do not add new methods to Console.
- No new modules or files are created outside the existing modules and the test files.

## Implementation constraints

- Read the console height only from the console size property. Do not read a height attribute from the console or from the render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement the Tree measurement iteratively with an explicit stack. Do not use recursion and do not add a depth cap.
- Do not change the max_width value passed to child labels; indentation is added to the measured widths only.
- Keep Tree.__rich_console__ behavior unchanged.
- Keep Align rendering unchanged apart from the required width constraint described in the workflows.

## Dependencies

- rich/tree.py imports the Measurement class from the measure module. The measure module does not import tree, so no import cycle is created.
- rich/align.py already imports Measurement, Segment, JupyterMixin, and Constrain; it needs no new imports.
- rich/console.py needs no new imports.
- No new third-party dependencies.

## Naming

- The class is named VerticalCenter, exactly.
- Method names follow the existing protocol names used by Align and Tree.
- Parameter names follow the existing ones: renderable, console, options, max_width.
- The repr text uses the class name and the reprs of the wrapped renderable and the alignment value, as described in the workflows.

## Validation

- Do not add extra validation to VerticalCenter. Argument problems surface through the existing render and measure paths.
- Do not add alignment-value checks to Align beyond the existing ones.

## Error handling

- The feature adds no new exception types.
- Negative padding counts are skipped, not raised.
- Errors from rendering or measuring the wrapped renderable propagate unchanged.

## Documentation

- VerticalCenter has a class docstring that begins with a one-line summary and has an Args section naming the renderable parameter with the renderable type. Follow the style of the Align docstring.
- CHANGELOG.md: under the 9.8.0 section, mark the heading as unreleased. Add an Added subheading with two entries: added rich_measure for tree, and added rich.align.VerticalCenter. Keep the existing entry about markdown over standard input. Do not add a line about ConsoleOptions height.

## Performance

- Tree measurement visits each node once, so its cost is linear in the number of nodes.
- VerticalCenter renders the wrapped renderable once and emits segments without re-rendering.

## Reliability

- Negative padding counts never produce output and never raise.
- Content taller than the console is rendered in full with no padding.
- An empty or single-node tree still returns a valid Measurement.

## Maintainability

- Format new code with black using default arguments.
- Keep imports in each file sorted in the same order the file already uses. In tests/test_tree.py, the imports are the console, measure, and tree modules, in that order.
- Place test imports at module top, not inside test functions.
- Match the file's existing iterative style for tree walking.

## Compatibility

- Tree rendering output is unchanged.
- The Align constructor and its shortcut methods are unchanged. Align output changes only where the wrapped renderable's measured maximum is narrower than the width that would otherwise apply, for example auto-width renderables. This is the required width behavior.
- Console.print keeps its signature.

## Behavioral acceptance criteria

- Measuring a Tree whose root label is "foo" with two children, "bar" and "musroom risotto", using a default console returns minimum 11 and maximum 19.
- Measuring a single-node Tree returns the label's own measurement.
- Calling repr on Align objects with each of the three alignment values succeeds and returns the text described in the Align repr workflow.
- Calling repr on a VerticalCenter wrapping "foo" returns the text described in the VerticalCenter repr workflow.
- Rendering VerticalCenter of "foo" on a console whose height is 6, with color disabled and output captured, produces exactly two newline characters, then "foo", then one newline, then two newline characters. In other words the captured text is two newlines, foo, and three newlines.
- Measuring VerticalCenter of "foo" with a default console returns minimum 3 and maximum 3.
- Rendering VerticalCenter never raises an attribute error.
- When the wrapped content is at least as tall as the console, no padding newlines are emitted.
- Align with no explicit width constrains its wrapped renderable to that renderable's measured maximum before alignment padding is computed.
- Align with an explicit width W constrains its wrapped renderable to the smaller of the measured maximum and W.
- Console.print with a justify argument still passes that argument into renderable collection, and the render options used to render the collected renderables carry the justify value "default".

## Test requirements

- tests/test_align.py: import VerticalCenter at module top alongside Align. Add a repr test that calls repr on Align with the left, center, and right values, and calls repr on a VerticalCenter instance. Add a VerticalCenter rendering test and a VerticalCenter measurement test matching the acceptance criteria.
- tests/test_tree.py: import the Measurement class at module top, after the console import and before the tree import. Add a test that builds the tree from the acceptance example, measures it with a default console, and compares the result with the expected Measurement.
- Existing tests in both files must still pass.
- No other test files need to change.
