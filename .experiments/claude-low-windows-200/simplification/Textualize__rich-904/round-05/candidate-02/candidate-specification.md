# Add rich_measure to Tree and VerticalCenter

## Goals

- Tree reports its natural width range: maximum is the widest label plus indentation; minimum is the widest unbreakable label content plus indentation.
- Add public VerticalCenter in rich.align, centering wrapped content vertically within the console height.
- Give Align and VerticalCenter a repr.
- Make Align constrain its wrapped renderable to the measured maximum width, so shrink-to-fit renderables such as trees center as one block.

## Scope

In scope: Tree measurement in rich/tree.py; VerticalCenter, reprs, and the Align width constraint in rich/align.py; the justify option in rich/console.py; CHANGELOG; tests.

Out of scope: a ConsoleOptions height field, version bumps, CONTRIBUTORS.md, main-guard demonstrations.

## Assumptions

- Console size supplies height in lines, falling back to terminal size, then 25 lines. ConsoleOptions has no height member.
- Measurement's get class method accepts strings, rich-cast objects, and measurable renderables. It returns zeros when maximum width is below 1, and uses console width when no maximum is passed.
- A Tree always has its own label. The root is at indent level 0; each deeper level adds four cells.

## Workflows

**Tree measurement**

1. Walk depth-first from the root using an explicit stack of iterators, with a level counter starting at 0.
2. For each node, measure its label with the given max_width, without reducing it by indentation.
3. Let indent be four times the level. Minimum becomes the larger of its current value and label minimum plus indent; maximum likewise uses label maximum.
4. Descend into children only when the node is expanded and has children, increasing the level; decrease it when a child list is exhausted.
5. Start both values at 0 and return a Measurement of the final values.

**VerticalCenter rendering**

1. Render the wrapped renderable to lines with the given options, padding to line width turned off.
2. Read console height from the console size property.
3. Top space is the floor of (height minus line count) divided by 2. Bottom space is height minus top space minus line count minus 1.
4. Emit top space as one newline segment when positive.
5. For each line, emit its segments followed by one newline segment.
6. Emit bottom space as one newline segment when positive.

**VerticalCenter measurement**

Delegate to the wrapped renderable's measurement with the given max_width, returning its Measurement unchanged.

**Align width constraint** (rendering only)

1. Measure the wrapped renderable with no maximum width; its maximum is the measured maximum.
2. With no explicit width, constrain the wrapped renderable to that maximum. With explicit width W, use the smaller of that maximum and W.
3. Apply the existing alignment, padding, and style steps unchanged.

**Console print justify**

Pass print's justify argument into renderable collection unchanged. For collected renderables, set render-option justify to "default".

## Data model

- Tree gains a measurement method taking a console and maximum width and returning a Measurement. Its fields, constructor, and add method are unchanged.

## API contracts

- VerticalCenter is a public class in rich.align with one attribute, renderable, typed with the renderable type alias. Its constructor takes that renderable positionally. It implements render, measurement, and repr, and inherits the Jupyter mixin as Align does.
- Align gains a repr with no new state: the class name, then the wrapped renderable's repr and the alignment's repr in parentheses. VerticalCenter's repr omits the alignment.
- Console.print keeps its signature.

## Module architecture

- Tree measurement: a Tree method in rich/tree.py, after the render method. Importing Measurement creates no cycle.
- VerticalCenter: rich/align.py, after Align and before the main-guard block. Do not register it in rich/__init__.py.
- No new modules, files, imports, or dependencies.

## Implementation constraints

- Read console height only from the console size property, never from a height attribute or render options.
- Emit vertical padding as newline segments, never as space-filled lines.
- Implement Tree measurement iteratively with an explicit stack and no depth cap.
- Pass max_width unchanged to child labels; add indentation only to measured widths.
- Leave Tree and Align rendering unchanged apart from the width constraint.
- Use the exact name VerticalCenter; protocol method names match Align and Tree.
- No new exception types or validation. Skip negative padding counts. Propagate wrapped-renderable errors unchanged.

## Documentation

- VerticalCenter docstring: one-line summary and an Args section naming renderable with its type, following Align's style.
- CHANGELOG.md: under 9.8.0, mark the heading unreleased; add an Added subheading with entries for rich_measure on tree and rich.align.VerticalCenter. Keep the existing markdown entry.
- Format with black defaults; keep import order.

## Behavioral acceptance criteria

- A Tree with root "foo" and children "bar" and "musroom risotto", measured on a default console, returns minimum 11 and maximum 19. A single-node Tree returns its label's measurement.
- repr works on Align for left, center, and right alignments; repr on VerticalCenter wrapping "foo" returns its repr text.
- Rendering VerticalCenter of "foo" on a height-6 console, color disabled, yields two newlines, "foo", and three newlines.
- Measuring VerticalCenter of "foo" on a default console returns minimum 3 and maximum 3.
- Empty or single-node trees return a valid Measurement; content at least as tall as the console gets no padding.

## Test requirements

- tests/test_align.py: import VerticalCenter beside Align; add repr, rendering, and measurement tests matching the criteria.
- tests/test_tree.py: import Measurement after console and before tree; add a measurement test for the acceptance tree.
- Existing tests in both files must still pass; no other test files change.
