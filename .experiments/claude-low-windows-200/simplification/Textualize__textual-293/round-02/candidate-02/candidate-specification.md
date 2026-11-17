## Goals

- Provide a horizontal tab-bar widget, Tabs, in the public module textual.widgets.tabs, built from a list of Tab items. Users select a tab by keyboard or mouse; the selection is shown by an animated underline bar.
- Each Tab has a label and a name. Selection and activation identify tabs by name, not position.
- Build from existing Textual mechanisms: default styles, @click action metadata and the event broker, reactive attributes with watchers, the animation facility, and rich renderables.

## Scope

In scope: the Tab and Tabs classes in textual.widgets.tabs; clickable-range support in the UnderlineBar renderable; a style-preserving change to the Opacity renderable; minimum-size support in the layout resolver's edge description; docstrings, a docs reference page, an optional sandbox demo, and tests.

Out of scope: behavior changes to other widgets, new third-party dependencies, and changes to base Widget behavior. Pull request body content (video, screenshots, demo command, checklist) is not a requirement.

## Assumptions

- The target is the Textual repository at the base commit. Widget, reactive, animation, event broker, and rich renderable facilities exist as they do there.
- Widths are terminal cell widths, not character counts.
- The base App provides set_focus as a coroutine and has no method named focus; the focus coroutine belongs to Widget. A coroutine called without await never runs.
- Message dispatch awaits an awaitable event handler's result, so asynchronous key handlers work.

## Terminology

- Label range: columns occupied by a tab's label text, excluding padding.
- Selection range: columns of a tab's padded span (left padding, label, right padding). Clicks use this range.
- Displayed tabs: one entry per distinct name, placed where that name first appears, showing the label of the last Tab with that name.
- Bar position: a fractional index into the displayed tabs placing the underline. The highlight spans the interpolated label range between the floor index and the next index, wrapping at the end.
- Clickable range: a named column span on the underline bar that carries a click action.
- Click action: the text range_clicked followed by the tab name in single quotes, in parentheses. The name is always quoted. It is attached as @click style metadata.

## Workflows

Rendering:
- Tabs occupies two rows: labels, then the underline bar. A line break separates them, even with no tabs.
- Labels span the widget width. Each displayed tab contributes three edges: left padding, label (sized to the label's cell width), and right padding. When tab_padding is absent or zero, padding edges are flexible with a minimum of one cell; they share the remaining width through the shared layout resolver, each taking the whole-cell part of its share and carrying the fractional leftover forward. When tab_padding is positive, each padding edge has that fixed size.
- A padded span is one text run, so its padding cells share the label's style and click action.
- Every label span, active or inactive, uses resolved style objects: each configured style is resolved against the console before attachment. No span carries a raw style string.
- The active tab's padded span uses the active tab style and no click action. Each inactive tab's padded span uses the inactive tab style, carries the click action for its own name, and is dimmed by inactive_text_opacity.
- The underline row highlights the interpolated bar position in the active bar style and uses the inactive bar style elsewhere. Its clickable ranges are the selection range of every displayed tab, keyed by name in display order, including the active tab. So the active tab's underline cells carry its click action even though its label does not.
- With no tabs, the first row is empty and the second row is the full-width inactive underline with no highlight, without error.

Initial state:
- The active tab name is active_tab when given and non-empty, otherwise the first tab's name. An active_tab matching no name is kept as given, and the bar sits at index 0. With no tabs there is no active tab.
- The bar position starts at the find_tab_by_name index of the active tab name.

Keyboard (while Tabs receives key events):
- With no tabs, mark the event handled and do nothing else.
- Escape awaits the app's set_focus with None as target, then marks the event handled. Add no lookup or guard. The reference's un-awaited call does nothing; follow the documented intent instead.
- Right and left move to the next or previous tab over the full list, wrapping. The starting point is the find_tab_by_name index, so with duplicate names the first occurrence counts.
- Digits are only the characters 0 through 9. Other Unicode digits, such as superscript or circled numerals, are not digit keys; they go to letter search when enabled, otherwise they are ignored.
- Keys 1 through 9 activate the tab at that 1-based position in the full list. The 0 key uses the number rule of activate_tab_by_number. Numbers above the tab count are ignored. Digit handling takes precedence over letter search.
- When search_by_first_character is true, any other key activates the next tab after the active one, wrapping, whose label begins with that character, compared case-insensitively. The search covers the full list and never selects the active tab. With no match, nothing changes. When the flag is false, the search is skipped.
- Mark every key event handled by preventing its default action only. Never stop propagation, so application bindings still receive keys.

Mouse:
- A click on any cell of a tab's selection range activates that tab, on either row.
- Where clickable spans overlap, the span applied later in display order receives the click.
- Clicks outside every range do nothing. Clicking the active label or the active tab's underline cells has no effect.

Animation:
- When the active tab changes, the bar position animates from its current value to the new active tab's index, using the configured easing and duration. A watcher on the active tab name drives this.

## Data model

- Tab: label (text, required) and name (text, optional, defaulting to the label).
- Names are not unique. Only displayed tabs render, so a duplicated name appears once.
- The full tab list keeps every tab. Navigation, digit activation, first-character search, and find_tab_by_name use it.
- Tabs state: the full ordered tab list; the active tab name (private reactive; none when there are no tabs); the bar position (private reactive float); the style values; inactive opacity; animation duration and easing name; tab_padding; and the search flag.
- Label and selection ranges, keyed by name, are computed during rendering from the same width arithmetic and feed the underline bar's clickable ranges. Do not keep a separate hit-test computation.

## API contracts

- Module textual.widgets.tabs exports Tab and Tabs through its export list.
- Tab: data holder with label and name, name defaulting to label. Two Tabs are equal when label and name match. Its representation shows both fields; its text form is the label.
- Tabs is a Widget subclass. Constructor inputs, in order:
  - tabs: list of Tab (required).
  - active_tab: optional tab name. Default none.
  - active_tab_style: style value. Default "#f0f0f0 on #021720".
  - active_bar_style: style value. Default "#1BB152".
  - inactive_tab_style: style value. Default "#f0f0f0 on #021720".
  - inactive_bar_style: style value. Default "#455058".
  - inactive_text_opacity: float blend ratio. Default 0.5.
  - animation_duration: float seconds. Default 0.3.
  - animation_function: easing name string. Default "out_cubic".
  - tab_padding: optional integer cell count. Default none (auto-fit).
  - search_by_first_character: boolean. Default true.
- Tabs default style: one bare declaration string setting height to two rows, with no selector and no braces, declared through the class attribute for default styles.
- Public Tabs methods, with these parameter names:
  - on_key, parameter event: the asynchronous keyboard handler described above.
  - activate_next_tab and activate_previous_tab: no parameters, synchronous. Move the active tab by one over the full list, wrapping.
  - activate_tab_by_first_char, parameter char: synchronous. Applies the search rule.
  - activate_tab_by_number, parameter tab_number: synchronous. Mapping, so direct calls and key presses match:
    - A number above the tab count returns with no change and no error.
    - 0 with at least ten tabs activates the 10th tab.
    - 0 with fewer than ten tabs activates the last tab by negative indexing.
    - Otherwise activate the tab at 1-based position tab_number.
  - find_tab_by_name, parameter tab_name: synchronous. Returns the index of the first tab in the full list with that name, or 0 if none.
  - action_range_clicked, parameter target_tab_name: synchronous. Sets the named tab as active.
- Tabs.render returns an internal class, TabsRenderable, in the same module. It is not exported.
- UnderlineBar: add an optional clickable_ranges input, a mapping from tab name to a (start, end) column pair with exclusive end. Default empty. It goes before width, which moves to the fifth position, so callers pass width by keyword. Other inputs keep names, order, defaults, and meanings.
  - Rendering: the bar yields exactly one rich text object, not a sequence of segments. Styled runs are built as before. Then, for each clickable range in mapping order, the bar attaches that name's click action to the span from start to end. These click spans are the last spans, in mapping order.
  - Zero-width early path: after the highlight range is clamped to the bar width (start raised to at least 0, end lowered to at most the width), the early path is taken when start and end are both zero, when end is negative, or when start exceeds end. It yields only the full-width background run, which still has its own style span, with no click metadata. Click spans are added only when the early path is not taken. Any other range, including a zero-width range at a non-zero position, renders its highlight and receives click spans.
- Opacity: parameters unchanged. The blended color merges into each segment's existing style, preserving other attributes, including click metadata.
- Layout resolver edge: carries size (optional, default none), min_size (default 1), and fraction (default 1). Existing callers keep their results.
- Click dispatch: the action string resolves to Tabs.action_range_clicked through the existing broker, with the widget as default namespace.

## Module architecture

- textual/widgets/tabs.py holds Tab, TabsRenderable, and Tabs. The module name is tabs, with no underscore prefix.
- Do not re-export Tabs from the textual.widgets package initializer.
- textual/renderables/underline_bar.py owns clickable-range metadata. The bar, not the widget, attaches click actions.
- textual/renderables/opacity.py gets the style-merge change; the layout resolver module gets the edge minimum-size change.
- Tabs owns state, keyboard handling, and animation. TabsRenderable owns width arithmetic and produces the label row and bar. Tabs.render delegates to it.
- Widgets may import renderables and the layout helper. Renderables must not import widgets.
- The optional sandbox demo lives under the sandbox directory, not the library package. It must run: mount Tabs widgets directly on the App, use a stylesheet with only properties the builder supports, and do not call docking helpers that exist only on dock views.

## Implementation constraints

- Set the two-row height only through the default style declaration. Do not set a sizing attribute on the instance, because layouts read the style value.
- Every construction parses the default style as bare declarations. A selector block makes the tokenizer raise, failing every Tabs construction, including empty lists.
- Call the base Widget initializer first, then assign tab state, styles, and other attributes.
- Do not hit-test coordinates in an on_click handler or post custom click messages. Attach @click metadata to spans and let the broker dispatch to action_range_clicked.
- Implement on_key as an asynchronous method so Escape can await set_focus. Check for no tabs first. Compare keys against constants in textual.keys. Treat only 0 through 9 as digits. Always prevent the default action; never stop propagation.
- Drive animation from a reactive bar position and a watcher on the active tab name. Never move the bar instantly.
- Every style reaching the bar or a label span must be resolved. Never pass a null style into the bar.
- Keep existing UnderlineBar output identical for existing inputs. The new metadata is additive.
- Keep lines within 88 columns (black style). Use Google-style docstring Args sections.

## Dependencies

- Use existing rich helpers for text, style, segments, and cell width; the Textual Widget, events, key constants, reactive values, and animation; and the Opacity, UnderlineBar, and layout resolver modules.
- No new third-party packages.

## Naming

- Classes: Tab, Tabs, TabsRenderable. Module: tabs.
- Methods: activate_next_tab, activate_previous_tab, activate_tab_by_first_char, activate_tab_by_number, find_tab_by_name, action_range_clicked. Do not use next_tab or previous_tab.
- Parameters: char, tab_number, tab_name, target_tab_name.
- Reactive attributes are private, with leading underscores, for the active tab name and bar position. The active-tab watcher follows the watcher naming convention for that private name.
- Action string: range_clicked. Bar input: clickable_ranges.
- snake_case for functions and attributes; PascalCase for classes.

## Validation

- An empty tab list is supported.
- An unknown active_tab is accepted; the bar position falls back to index 0.
- tab_padding of zero is treated as absent (auto-fit), matching the reference's truthiness check.
- Digit keys outside the tab count are ignored without error.

## Error handling

- A null style makes style resolution raise on every bar render, including the no-tabs path.
- Keyboard paths check for an empty tab list before any index arithmetic, so no key press raises.
- Clicks matching no range do nothing and do not raise.
- Direct calls to next, previous, first-character search, and activate_tab_by_number with 0 on an empty list are unguarded; callers must not make them.
- Do not guard framework calls with attribute lookups or callability checks. Call the framework API directly so a mismatch fails visibly.

## Documentation

- Docstrings for Tab and Tabs in Args format. Each Tabs parameter is described, including its default.
- The on_key docstring describes key behavior, including that Escape removes focus from the widget.
- Source comments describe what the code does. Do not cite the reference implementation, a pull request, or external artifacts.
- The UnderlineBar Args section documents clickable_ranges and must not claim they apply on the zero-width early path.
- A docs reference page for the module with a single directive targeting the Tabs class in textual.widgets.tabs.
- An optional sandbox demo with a stylesheet; tests do not require it.

## Maintainability

- Tabs module annotations use the union form with a None alternative, not Optional, and postponed annotation evaluation, matching the reference tabs module.

## Compatibility

- Existing UnderlineBar callers keep identical rendered output for existing inputs. The bar's rich item changes from a sequence of segments to one text object, so callers passing width by position must switch to keyword passing.
- Existing Opacity callers keep identical color output; other segment attributes are now preserved.
- Existing layout resolver callers keep identical results, and existing tests pass without modification.
- Minimum version is Python 3.7. Every new library and test module must import under 3.7, so annotations use the postponed-annotation import or typing generics, not builtin generic subscripts.

## Behavioral acceptance criteria

1. Labels render on the first row and the underline on the second, highlighting the active tab's span.
2. The initial active tab is active_tab when given, otherwise the first tab.
3. Right and left keys cycle with wrap-around. Escape awaits set_focus with no target.
4. Digit keys activate by position; the 0 key follows the reference rule for key presses and direct calls alike. Superscript and circled numerals are not digit keys.
5. Letter search is case-insensitive, starts after the active tab, wraps, never selects the active tab, and is disabled when the flag is false.
6. A click inside an inactive tab's selection range activates it; a click outside every range does nothing.
7. A change of active tab animates the bar position.
8. With no tabs, the first row is empty and the second shows only the full-width inactive underline, without error.
9. Inactive labels, including padding cells, are dimmed by the configured opacity and carry the tab's click action.
10. A Tab without a name uses its label as its name.
11. Duplicate names display once, at the first occurrence's position, with the last tab's label. find_tab_by_name returns the first index for a duplicated name.
12. Key events are marked handled without stopping propagation.
13. Constructing Tabs with any tab list, including an empty one, succeeds without a style parsing error.
14. An UnderlineBar whose highlight takes the zero-width early path yields one text object whose spans carry no click metadata. A zero-width highlight at a non-zero position yields click metadata on its spans.

## Test requirements

- In tests/renderables/test_underline_bar.py, add a test that passes two clickable ranges with a small width, renders with console and options doubles, and takes the first yielded item. It checks that the item is one text object whose last two spans have the given start and end columns and quoted click metadata for each tab name, in mapping order.
- Add a zero-width early-path test: a bar with no highlight, or one the early-path rule rejects, yields one text object whose spans carry no click metadata. Do not assert that the spans list is empty, because the background run adds a style span. Check each span's click metadata instead.
- Select spans of the tab under test by text position. Do not assert on the active tab's span. Before reading click metadata, confirm the style is a resolved style object; a raw style string has no metadata attribute, and reading it raises.
- Do not add trivial assertions about constants, such as a character's absence from the default style string. Cover the default style through construction behavior.
- Do not assert rendered-string equality between bars with and without clickable ranges, and do not pin a fixed ANSI string where a click boundary splits a run. Check spans or per-cell metadata instead.
- Underline-row assertions check the highlight's cells and the half-cell glyphs at its edges, not an exact uniform bar string. Half-cell glyphs appear at fractional edges and at whole-number edges that are not the bar's ends: the background cell just before a highlight starting after cell zero shows a right-half glyph, and the background cell at a highlight end before the bar's width shows a left-half glyph. Example: a highlight from 2 to 4 on a bar of width 6 has plain text of one heavy bar, a right-half glyph, two heavy bars, a left-half glyph, and one heavy bar.
- Do not assert that the active tab's underline cells lack a click action; the reference attaches click actions to every displayed tab's underline cells.
- Rendered label rows must derive from the layout rule in Workflows, or the test passes an explicit tab_padding. Do not hand-write an auto-fit label row without computing the flexible shares.
- Tests must not call asyncio.run, create or replace event loops, or otherwise change the thread's event-loop state. Test find_tab_by_name, the activate methods, action_range_clicked, and rendered output through the render helper directly. Do not drive on_key unless the repository has an established key-event harness.
- Import every name a test module uses at the top of the module, never inside test functions.
- Existing underline tests pass unchanged. Use the existing render helper from the tests utilities for rendered-text checks.
- Tabs behavior tests are encouraged, following the repository's renderable and widget test pattern: duplicate names, no-tabs row layout, padded-cell styling, first-index lookup, and construction with default styles. New test modules satisfy the Python 3.7 annotation rule.
