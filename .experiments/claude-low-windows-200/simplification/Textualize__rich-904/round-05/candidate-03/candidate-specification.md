# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range: maximum is the widest label plus indentation; minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align, vertically centering wrapped content within console height.
- Give Align and VerticalCenter a repr.
- Make Align constrain wrapped renderables to their measured maximum width, so shrink-to-fit renderables such as trees center as one block.
- Make Console.print render collected renderables with justify "default".

## Scope

In scope: Tree measurement (rich/tree.py); VerticalCenter, reprs, and the Align width constraint (rich/align.py); justify (rich/console.py); CHANGELOG; tests.

Out of scope: ConsoleOptions height, version bumps, CONTRIBUTORS.md, main-guard demonstrations.

## Assumptions

- Console size supplies height in lines, falling back to terminal size, then 25 lines. ConsoleOptions has no height member.
- Measurement's get class method accepts strings, rich-cast objects, and measurable renderables. It returns zeros when maximum width is below 1, and uses console width when no maximum width is passed.
- Every Tree has a label. The root is at indent level 0; each deeper level adds four cells.

## Workflows

**Tree measurement**

1. Walk depth-first from the root with an explicit stack of iterators and a level counter starting at 0.
2. Measure each node's label with the given max_width, without reducing it by indentation.
3. Let indent be four times the level. Minimum becomes the larger of its value and label minimum plus indent; maximum likewise uses label maximum plus indent.
4. Descend into children only when the node is expanded and has children, increasing the level. Decrease it when a child list is exhausted.
5. Start both values at 0; return a Measurement of the final values.

**VerticalCenter rendering**

1. Render the wrapped renderable to lines with the given options, padding to line width off.
2. Read console height from the console size property.
3. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
4. If top space is positive, emit one segment of exactly that many newlines. Then emit each line's segments followed by one newline segment. Finally, if bottom space is positive, emit one segment of exactly that many newlines.

**VerticalCenter measurement**

Delegate to the wrapped renderable's measurement with the given max_width, returning its Measurement unchanged.

**Align width constraint** (rendering only; Align's measurement is unchanged)

1. Measure the wrapped renderable without a maximum width to get its maximum.
2. With no explicit width, constrain the wrapped renderable to the measured maximum. With explicit width W, constrain to the smaller of the two.
3. Apply existing alignment, padding, and style steps unchanged.

**Console print justify**

Pass print's justify into renderable collection unchanged; set render options justify to "default" for collected renderables.

## API contracts

- Tree gains a measurement method taking a console and a maximum width and returning a Measurement. Its fields, constructor, and add method are unchanged.
- VerticalCenter is a public class in rich.align with one attribute, renderable, typed with the renderable type alias, constructed from one positional parameter. It implements the render, measurement, and repr protocols and inherits the Jupyter mixin as Align does.
- Align gains a repr with no new state.
- Align's repr is the class name, then in parentheses the wrapped renderable's repr and the alignment's repr, comma-separated. VerticalCenter's repr omits the alignment.
- Console.print keeps its signature; only the justify value in render options changes.

## Module architecture

- Tree measurement: a Tree method in rich/tree.py, after the render method.
- VerticalCenter: rich/align.py, after Align and before the main-guard block. Do not register it in rich/__init__.py.
- No new modules, files, imports, or dependencies.

## Implementation constraints

- Read console height only from the console size property, never a height attribute or render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement Tree measurement iteratively with an explicit stack and no depth cap.
- Pass max_width unchanged to child labels; add indentation only to measured widths.
- Tree.__rich_console__ stays unchanged; Align rendering changes only by the width constraint.
- Use the exact class name VerticalCenter.
- No new exception types or validation. Skip negative padding counts. Propagate wrapped-renderable errors unchanged.

## Documentation

- VerticalCenter docstring: a one-line summary and an Args section naming renderable and its type, as Align does.
- CHANGELOG.md: under 9.8.0, mark the heading unreleased; add an Added subheading listing rich_measure for tree and rich.align.VerticalCenter; keep the existing markdown entry.
- Format with black defaults; keep existing import order.

## Behavioral acceptance criteria

- A Tree with root "foo" and children "bar" and "musroom risotto", measured on a default console, returns minimum 11 and maximum 19. A single-node Tree returns its label's own measurement.
- repr works on Align for left, center, and right alignments. repr on VerticalCenter wrapping "foo" returns its repr text.
- Rendering VerticalCenter of "foo" on a height-6 console, color disabled, yields two newlines, "foo", and three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3. Rendering never raises an attribute error.
- Empty or single-node trees return a valid Measurement; content at least as tall as the console gets no padding.

## Test requirements

- tests/test_align.py: import VerticalCenter; add repr, rendering, and measurement tests for the criteria above.
- tests/test_tree.py: import Measurement after console; add a measurement test for the acceptance-example tree.
- Existing tests must pass; no other test files change.
