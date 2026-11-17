# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range: maximum is the widest label plus indentation; minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align, vertically centering wrapped content within console height.
- Make Align constrain its wrapped renderable to the measured maximum width, so shrink-to-fit renderables such as trees center as one block.
- Make Console.print render collected renderables with justify "default"; the justify argument still goes into renderable collection.

## Scope

In scope: the files named in the sections below. Out of scope: a height field on ConsoleOptions, version bumps, CONTRIBUTORS.md, main-guard demonstrations.

## Assumptions

- Console size supplies height, falling back to terminal size, then 25 lines. ConsoleOptions has no height member.
- Measurement's get class method accepts strings, rich-cast objects, and measurable renderables; it returns zeros for maximum width below 1.
- A Tree always has its own label. The root is at indent level 0; each deeper level adds four cells.

## Workflows

**Tree measurement**

1. Walk depth-first from the root with an explicit stack of iterators and a level counter starting at 0.
2. Measure each label with the given max_width, without reducing it by indentation.
3. Let indent be four times the level. Minimum becomes the larger of its value and label minimum plus indent; maximum likewise uses label maximum plus indent.
4. Descend into children only when the node is expanded and has children, increasing the level; decrease it when a child list is exhausted.
5. Start both values at 0 and return a Measurement of the final values.

**VerticalCenter rendering**

1. Render the wrapped renderable to lines with the given options, padding to line width off. Read height from the console size property.
2. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
3. If top space is positive, emit one segment of exactly that many newlines.
4. For each line, emit its segments followed by one newline segment.
5. If bottom space is positive, emit one segment of exactly that many newlines.

**VerticalCenter measurement**

Return the wrapped renderable's Measurement for the given max_width, unchanged.

**Align width constraint** (rendering only; measurement unchanged)

1. Measure the wrapped renderable with no maximum width; its maximum is the measured maximum. With no explicit width, constrain the wrapped renderable to that maximum. With explicit width W, constrain it to the smaller of the maximum and W.
2. Apply existing alignment, padding, and style steps unchanged.

**Console print justify**

Pass print's justify into renderable collection unchanged. For collected renderables' render options, set justify to "default".

## Data model

Tree gains a measurement method taking a console and maximum width and returning a Measurement. Other members are unchanged.

## API contracts

- VerticalCenter is a public class in rich.align with one attribute, renderable, typed with the renderable type alias. Its constructor takes that renderable as one positional parameter. It implements render, measurement, and repr, and inherits the Jupyter mixin as Align does.
- Align gains a repr returning a string, with no new state.
- Reprs: Align's is the class name, then in parentheses the wrapped renderable's repr and the alignment's repr, separated by a comma and space. VerticalCenter's repr omits the alignment.
- Console.print keeps its signature; only the justify value in render options changes.

## Module architecture

- Tree measurement: a Tree method in rich/tree.py, after the render method.
- VerticalCenter: rich/align.py, after Align and before the main-guard block. Do not register it in rich/__init__.py.
- No new modules, files, imports, or dependencies.

## Implementation constraints

- Read console height only from the console size property, never from a height attribute or render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement Tree measurement iteratively with an explicit stack and no depth cap.
- Pass max_width unchanged to child labels; add indentation only to measured widths.
- Tree.__rich_console__ and Align rendering stay unchanged apart from the width constraint.
- No new exception types or validation. Skip negative padding counts. Propagate wrapped-renderable errors unchanged.

## Documentation

- VerticalCenter docstring: a one-line summary and an Args section naming renderable with its type, following Align's style.
- CHANGELOG.md: mark the 9.8.0 heading unreleased; add an Added subheading listing rich_measure on tree and VerticalCenter; keep the markdown-over-standard-input entry.
- Format with black defaults; keep existing import order.

## Behavioral acceptance criteria

- A Tree with root "foo" and children "bar" and "musroom risotto", measured on a default console, returns minimum 11 and maximum 19. A single-node Tree returns its label's own measurement.
- repr works on Align for left, center, and right alignments. repr on VerticalCenter wrapping "foo" returns its repr text.
- Rendering VerticalCenter of "foo" on a height-6 console, color disabled, yields two newlines, "foo", and three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3. Rendering never raises an attribute error.
- Empty or single-node trees return a valid Measurement; content at least as tall as the console gets no padding.

## Test requirements

- tests/test_align.py: import VerticalCenter beside Align; add repr, rendering, and measurement tests matching the acceptance criteria.
- tests/test_tree.py: import Measurement after console and before tree; add a measurement test for the acceptance-example tree.
- Existing tests must still pass; change no other test files.
