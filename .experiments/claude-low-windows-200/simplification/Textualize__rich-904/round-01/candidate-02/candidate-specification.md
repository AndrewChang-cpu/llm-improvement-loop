# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range through the measurement protocol. Its maximum is the widest label plus nesting indentation. Its minimum is the widest unbreakable label content plus indentation.
- Add public class VerticalCenter in the rich.align module. It vertically centers its wrapped content within the console's current height and emits only content and newline characters.
- Give Align and VerticalCenter a repr text, as described in the workflows.
- Make Align constrain its wrapped renderable to that renderable's measured maximum width, so a shrink-to-fit renderable (such as a tree or an auto-width panel) is centered as one block instead of stretched to full width.
- Make Console.print render collected renderables with the justify option set to "default", while the justify argument still goes into renderable collection.

## Scope

In scope:
- Tree measurement in rich/tree.py.
- VerticalCenter, and the repr methods of Align and VerticalCenter, in rich/align.py.
- The width constraint in the Align rendering path, in rich/align.py.
- The justify option of the render options built by Console.print, in rich/console.py.
- A CHANGELOG entry and tests.

Out of scope:
- Adding a height field to ConsoleOptions. The reference CHANGELOG line about it has no code behind it; do not add it.
- Changing the package version in pyproject.toml or editing CONTRIBUTORS.md.
- Changing the demonstration block under the main guard in either module.

## Assumptions

- The Console size property provides width and height in lines. Without an explicit height, it falls back to the terminal size, then to 25 lines.
- ConsoleOptions has no height member. Height is read from the console only.
- The existing measurement entry point (the get class method of Measurement) accepts strings, rich-cast objects, and renderables with a measurement method. It returns zeros when the maximum width is below 1, and uses the console width when no maximum width is passed.
- A Tree always has its own label. The root node is at indent level 0.

## Terminology

- Measurement: a two-field named tuple (minimum, maximum) of character cell widths.
- Measured maximum: the maximum field of a renderable's measurement, taken at the console width when no maximum width is passed.
- Indent level: the depth of a tree node below the root. Each level adds four cells.
- Padding newlines: newline characters emitted as one segment to move content to the vertical center. They are not spaces.

## Workflows

### Tree measurement

1. Walk the tree depth-first from the root, using an explicit stack of iterators (not recursion) and a level counter that starts at 0.
2. For each visited node, measure its label through the measurement entry point with the max_width given to the Tree measurement. Do not reduce max_width by indentation.
3. Let indent be 4 times the current level. Set minimum to the larger of the current minimum and (label minimum plus indent). Set maximum to the larger of the current maximum and (label maximum plus indent).
4. Descend into a node's children only when the node is expanded and has children. Increase the level when descending and decrease it when a child list is exhausted.
5. Start minimum and maximum at 0. Return a Measurement built from the final values.

### VerticalCenter rendering

1. Render the wrapped renderable to a list of lines using the given options, with padding to the line width turned off.
2. Read the console height from the console size property.
3. Set top space to the floor of (height minus line count) divided by 2. Set bottom space to height minus top space minus line count minus 1.
4. If top space is greater than 0, emit one segment containing exactly that many newline characters.
5. For each line, emit its segments followed by one newline segment.
6. If bottom space is greater than 0, emit one segment containing exactly that many newline characters.

When content fits, the total newline count is height minus 1. When content is as tall as the console or taller, no padding is emitted and all lines still render.

### VerticalCenter measurement

Delegate to the measurement entry point of the wrapped renderable with the given max_width and return its Measurement unchanged.

### Align repr

Return the text Align, an opening parenthesis, the repr of the wrapped renderable, a comma and a space, the repr of the alignment value, and a closing parenthesis.

### VerticalCenter repr

Return the text VerticalCenter, an opening parenthesis, the repr of the wrapped renderable, and a closing parenthesis.

### Align width constraint

This applies only to Align's rendering path. Align's measurement method is unchanged.

1. Measure the wrapped renderable through the measurement entry point with no maximum width, so the console width is used. Take its maximum as the measured maximum.
2. With no explicit width, constrain the wrapped renderable to the measured maximum.
3. With an explicit width W, constrain it to the smaller of the measured maximum and W.
4. Render the constrained renderable with the given options, then apply the existing alignment, padding, and style steps unchanged.

### Console print justify

Pass print's justify argument into renderable collection unchanged. For the render options used to render the collected renderables, set justify to "default" instead. All other option values are unchanged.

## Data model

- Tree: existing fields. The new measurement reads label, children, and expanded only.
- VerticalCenter: one attribute, renderable, holding the wrapped object.
- Align: existing fields (renderable, alignment, style, pad, width). No new fields.
- Measurement: unchanged.
- Console size: a named tuple with width and height in lines.
- No new persistent data and no new state on Console or ConsoleOptions.

## API contracts

- Tree: gains a measurement method taking a console and a maximum width and returning a Measurement. Its constructor and add method are unchanged.
- VerticalCenter: a public class in rich.align. Its constructor takes one positional renderable parameter, typed with the renderable type alias. It implements the render protocol (console and options in, iterable of segments out), the measurement protocol, and repr. It inherits the Jupyter mixin, as Align does.
- Align: gains a repr method returning a string. Its constructor and alignment shortcut methods are unchanged.
- Console.print: signature unchanged. Only the justify value in the render options changes.

## Module architecture

- Tree measurement is a method of Tree in rich/tree.py, placed after the render method.
- VerticalCenter is in rich/align.py, after the Align class and before the main-guard block. Do not register it in rich/__init__.py or any registry.
- Align repr and the Align width constraint are methods of Align in rich/align.py.
- The justify change is in Console.print in rich/console.py. Do not add methods to Console.
- Create no new modules or files beyond the test files.

## Implementation constraints

- Read console height only from the console size property. Never read a height from the console or the render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement the Tree measurement iteratively with an explicit stack. No recursion and no depth cap.
- Pass the unchanged max_width to child labels; indentation is added to measured widths only.
- Keep Tree.__rich_console__ and all other Align rendering unchanged apart from the width constraint.

## Dependencies

- rich/tree.py imports Measurement from the measure module. The measure module does not import tree, so no cycle arises.
- rich/align.py already imports Measurement, Segment, JupyterMixin, and Constrain. rich/console.py needs no new imports.
- No new third-party dependencies.

## Naming

- The class name is exactly VerticalCenter.
- Method names follow the existing protocol names used by Align and Tree. Parameter names are renderable, console, options, and max_width.

## Error handling

- Add no new exception types and no extra validation to VerticalCenter or Align beyond existing checks.
- Negative padding counts are skipped, not raised.
- Errors from rendering or measuring the wrapped renderable propagate unchanged.

## Documentation

- VerticalCenter has a class docstring with a one-line summary and an Args section naming the renderable parameter and its type. Follow the Align docstring style.
- CHANGELOG.md: under the 9.8.0 section, mark the heading as unreleased. Add an Added subheading with two entries: added rich_measure for tree, and added rich.align.VerticalCenter. Keep the existing markdown-over-standard-input entry. Add no ConsoleOptions height line.

## Performance

- Tree measurement visits each node once, so its cost is linear in the node count.
- VerticalCenter renders the wrapped renderable once and emits segments without re-rendering.

## Reliability

- Negative padding counts never produce output and never raise.
- An empty or single-node tree still returns a valid Measurement.

## Maintainability

- Format new code with black defaults.
- Keep imports sorted in the file's existing order. In tests/test_tree.py, import the console, measure, and tree modules in that order.
- Place test imports at module top.

## Compatibility

- Tree rendering output is unchanged.
- Align output changes only where the measured maximum is narrower than the width that would otherwise apply, for example auto-width renderables. This is the required width behavior.
- Console.print keeps its signature.

## Behavioral acceptance criteria

- Measuring a Tree with root label "foo" and two children, "bar" and "musroom risotto", on a default console returns minimum 11 and maximum 19.
- Measuring a single-node Tree returns the label's own measurement.
- repr on Align with each of the three alignment values returns the text described in the Align repr workflow.
- repr on VerticalCenter wrapping "foo" returns the text described in the VerticalCenter repr workflow.
- Rendering VerticalCenter of "foo" on a console of height 6, with color disabled and output captured, yields two newlines, "foo", then three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3.
- Rendering VerticalCenter never raises an attribute error.
- Content at least as tall as the console gets no padding newlines.
- Align with no explicit width constrains its wrapped renderable to the measured maximum before alignment padding is computed.
- Align with explicit width W constrains it to the smaller of the measured maximum and W.
- Console.print with a justify argument still passes it into renderable collection, and the render options carry justify "default".

## Test requirements

- tests/test_align.py: import VerticalCenter at module top beside Align. Add a repr test covering Align with left, center, and right, and a VerticalCenter instance. Add VerticalCenter rendering and measurement tests matching the acceptance criteria.
- tests/test_tree.py: import Measurement at module top after the console import and before the tree import. Add a test that builds the acceptance tree, measures it on a default console, and compares the result with the expected Measurement.
- Existing tests in both files must still pass. No other test files change.
