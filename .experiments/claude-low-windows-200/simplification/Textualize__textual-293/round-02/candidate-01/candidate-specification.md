## Goals

- Provide a horizontal tab-bar widget, Tabs, in textual.widgets.tabs, built from a list of Tab items. Users select a tab by keyboard or mouse; the selection is shown by an animated underline bar.
- Each Tab has a label and a name. Selection and activation identify tabs by name, not position.
- Build from existing Textual mechanisms: widget default styles, @click action metadata with the event broker, reactive attributes with watchers, the animation facility, and rich renderables.

## Scope

In scope: the Tab and Tabs classes in textual.widgets.tabs; clickable-range support in UnderlineBar; a style-preserving change to Opacity; minimum-size support in the layout resolver's edge description; docstrings; a docs reference page; an optional sandbox demo; tests.

Out of scope: behavior changes to other widgets, new third-party dependencies, and base Widget changes. Pull request body content (video, screenshots, demo command, checklist) is not a requirement.

## Assumptions

- The target is the Textual repository at the base commit, with the widget, reactive, animation, event broker, and rich renderable facilities as they exist there.
- Widths are terminal cell widths, not character counts.
- The base App provides set_focus as a coroutine and has no method named focus; the coroutine named focus belongs to Widget. A coroutine called without await never runs.
- Message dispatch awaits an event handler's result when it is awaitable, so asynchronous key handlers work.

## Terminology

- Label range: columns occupied by a tab's label text, excluding padding.
- Selection range: columns of a tab's padded span (left padding, label, right padding). Clicks use this range.
- Displayed tabs: one entry per distinct name, placed at that name's first occurrence and showing the label of the last Tab with that name.
- Bar position: a fractional index into the displayed tabs that places the underline. The highlight spans the interpolated label range between the floor index and the next index, wrapping at the end.
- Clickable range: a named column span on the underline bar that carries a click action.
- Click action: the text range_clicked followed by the tab name in single quotes, in parentheses. The name is always quoted. It is attached as @click style metadata.

## Workflows

Rendering:
- Tabs occupies two rows: labels on the first, the underline bar on the second. A line break separates the rows, even with no tabs.
- Each displayed tab contributes three edges: left padding, a label edge sized to the label's cell width, and right padding. When tab_padding is absent or zero, padding edges are flexible with a minimum of one cell. Flexible edges share the remaining width through the shared layout resolver: each gets the whole-cell part of its share, and the fractional leftover carries forward to later flexible edges. When tab_padding is positive, each padding edge has that fixed size.
- A padded span is one run of text, so padding cells share the label's style and click action.
- Every label span, active or inactive, uses resolved style objects: each configured style is resolved against the console before it is attached. No label span carries a raw style string.
- The active tab's padded span uses the active tab style and carries no click action. Each inactive tab's padded span uses the inactive tab style, carries the click action for its own name, and is dimmed by inactive_text_opacity.
- The underline row highlights the interpolated bar position in the active bar style and uses the inactive bar style elsewhere. Its clickable ranges are the selection range of every displayed tab, keyed by name, in display order. This includes the active tab, so its underline cells carry its click action even though its label does not.
- With no tabs, the first row is empty and the second row is the full-width inactive underline with no highlight, rendered without error.

Initial state:
- The active tab name is active_tab when given and non-empty; otherwise it is the first tab's name. An active_tab matching no name is kept as given, and the bar sits at index 0. With no tabs, there is no active tab.
- The bar position starts at the find_tab_by_name index of the active tab name.

Keyboard (while Tabs receives key events):
- With no tabs, mark the event handled and do nothing else.
- Escape awaits the app's set_focus with None as the target, releasing focus, then marks the event handled. Add no lookup or guard. The reference's un-awaited call does nothing; this specification follows the documented intent.
- Right and left move to the next or previous tab over the full list, wrapping at either end. The starting point is the find_tab_by_name index, so the first occurrence counts with duplicate names.
- Digit keys are only the characters 0 through 9. Other characters Unicode treats as digits, such as superscript or circled numerals, are not digit keys; they go to letter search when enabled, and are otherwise ignored.
- Keys 1 through 9 activate the tab at that 1-based position in the full list. Key 0 follows the rule of activate_tab_by_number. Numbers above the tab count are ignored. Digit handling takes precedence over letter search.
- When search_by_first_character is true, any other key activates the next tab after the active one, wrapping, whose label begins with that character, compared case-insensitively. The search covers the full list and never selects the active tab. With no match, the active tab is unchanged. When the flag is false, the search is skipped.
- Mark every key event handled by preventing its default action only. Never stop propagation, so application bindings still receive keys.

Mouse:
- A click on any cell in a tab's selection range activates that tab, on both the label row and the underline row.
- Where clickable spans overlap, the span applied later in display order receives the click.
- A click outside every range does nothing. Clicking the active label, or the active tab's underline cells, has no effect.

Animation:
- When the active tab changes, the bar position animates from its current value to the new active tab's index, using the configured easing and duration. A watcher on the active tab name drives this.

## Data model

- Tab: label (required text) and name (optional text, defaulting to the label).
- Names are not unique. Only displayed tabs are rendered, so a duplicated name appears once.
- The full tab list keeps every tab. Navigation, digit activation, first-character search, and find_tab_by_name use the full list.
- Tabs state: the full ordered tab list; the active tab name (a private reactive value, none when there are no tabs); the bar position (a private reactive float); the style values; the inactive opacity; the animation duration and easing name; tab_padding; and the search flag.
- Label ranges and selection ranges, keyed by name, are computed during rendering from the same width arithmetic and feed the underline bar's clickable ranges. Do not keep a separate hit-test computation.

## API contracts

- Module textual.widgets.tabs exports Tab and Tabs through its export list.
- Tab: data holder with label and name; name defaults to label. Two Tabs are equal when label and name are equal. Its representation shows both fields. Its text form is the label.
- Tabs is a Widget subclass. Constructor inputs, in order:
  - tabs: list of Tab (required).
  - active_tab: optional tab name. Default none.
  - active_tab_style: style value. Default "#f0f0f0 on #021720".
  - active_bar_style: style value. Default "#1BB152".
  - inactive_tab_style: style value. Default "#f0f0f0 on #021720".
  - inactive_bar_style: style value. Default "#455058".
  - inactive_text_opacity: float blend ratio. Default 0.5.
  - animation_duration: float in seconds. Default 0.3.
  - animation_function: easing name string. Default "out_cubic".
  - tab_padding: optional integer cell count. Default none, meaning auto-fit.
  - search_by_first_character: boolean. Default true.
- Tabs default style: a single bare declaration string that sets the height to two rows, with no selector and no braces, supplied through the class attribute for default styles.
- Public Tabs methods, with these parameter names:
  - on_key(event): the asynchronous keyboard handler in Workflows.
  - activate_next_tab() and activate_previous_tab(): synchronous, no parameters. Move the active tab by one over the full list, wrapping.
  - activate_tab_by_first_char(char): synchronous. Applies the search rule.
  - activate_tab_by_number(tab_number): synchronous. Direct calls and key presses share this mapping:
    - tab_number above the tab count: return with no change and no error.
    - tab_number 0 with at least ten tabs: activate the 10th tab.
    - tab_number 0 with fewer than ten tabs: activate the last tab, through negative indexing.
    - Otherwise: activate the tab at 1-based position tab_number.
  - find_tab_by_name(tab_name): synchronous. Returns the index of the first tab in the full list with that name, or 0 when none has it.
  - action_range_clicked(target_tab_name): synchronous. Sets the named tab as active.
  - A watcher on the active tab name animates the bar position.
- Tabs.render returns an internal renderable class, TabsRenderable, in the same module. It is not exported.
- UnderlineBar: add an optional clickable_ranges input, a mapping from tab name to a (start, end) column pair with an exclusive end. Default empty. It goes before the width input, which moves to fifth position, so callers pass width by keyword. Existing style and highlight inputs keep their names, order, defaults, and meanings.
  - Rendering yields exactly one rich text object, not a sequence of segments. Styled runs are built as before. Then, for each clickable range in mapping order, the bar attaches that name's click action to the span from start to end. These click spans are the last spans, in mapping order.
  - Zero-width early path: after the highlight range is clamped to the bar width (start raised to at least 0, end lowered to at most the width), the early path is taken when start and end are both zero, when end is negative, or when start exceeds end. It yields only the full-width background run, which still has its own style span, and no click metadata. Click spans are added only when the early path is not taken. Any other range, including a zero-width range at a non-zero position, renders its highlight and receives click spans.
- Opacity: parameters unchanged. The blended color merges into each segment's existing style, so other attributes, including click metadata, are preserved.
- Layout resolver edge: carries size (optional, default none), min_size (default 1), and fraction (default 1). Existing callers keep their results.
- Click dispatch: the action string resolves to Tabs.action_range_clicked through the existing broker, with the widget as the default namespace.

## Module architecture

- textual/widgets/tabs.py holds Tab, TabsRenderable, and Tabs. Use the public module name tabs. Do not re-export Tabs from the textual.widgets package initializer.
- textual/renderables/underline_bar.py owns clickable-range metadata. The bar, not the widget, attaches click actions to spans.
- textual/renderables/opacity.py gets the style-merge change. The layout resolver module gets the edge minimum-size change.
- Tabs owns state, keyboard handling, and animation. TabsRenderable owns width arithmetic and produces the label row and the bar. Tabs.render delegates to TabsRenderable.
- Widgets may import renderables and the layout helper. Renderables must not import widgets.
- The optional sandbox demo lives under the sandbox directory, not the library package. It must run: mount the example Tabs widgets directly on the App, use a stylesheet with only properties the builder supports, and do not call docking helpers that exist only on dock views.

## Implementation constraints

- Sizing: set the two-row height only through the default style declaration. Do not set a sizing attribute on the instance, because layouts read the style value.
- Default style parsing: every construction parses the default style as bare declarations. A selector block makes the tokenizer raise during construction, failing every Tabs construction, including with an empty list.
- Constructor order: call the base Widget initializer first, then assign tab state, styles, and other attributes.
- Clicks: do not hit-test coordinates in an on_click handler and do not post custom click messages. Attach @click metadata to spans and let the broker dispatch to action_range_clicked.
- Keyboard: on_key is asynchronous so the Escape path can await set_focus. Check for no tabs first. Compare keys against the constants in textual.keys. Treat only 0 through 9 as digits. Always mark the event handled by preventing its default action. Never stop propagation.
- Label styles: resolve every configured style into a style object before building any label span. Never pass a null style into the bar.
- Animation: drive it from a reactive bar position and a watcher on the active tab name. Never move the bar instantly.
- Keep existing UnderlineBar output identical for existing inputs. The new metadata is additive.
- Keep lines within 88 columns (black style). Use Google-style docstring Args sections.
- Use existing rich helpers for text, style, segments, and cell width; the Textual Widget, events, key constants, reactive values, and animation; and the Opacity, UnderlineBar, and layout resolver modules. Add no third-party packages.

## Naming

- Classes: Tab, Tabs, TabsRenderable. Module: tabs.
- Methods: activate_next_tab, activate_previous_tab, activate_tab_by_first_char, activate_tab_by_number, find_tab_by_name, action_range_clicked. Do not use next_tab or previous_tab.
- Parameters: char, tab_number, tab_name, target_tab_name.
- Reactive attributes are private, with leading underscores, for the active tab name and the bar position. The active-tab watcher follows the watcher naming convention for that private name.
- Action string: range_clicked. Bar input: clickable_ranges.

## Error handling

- Keyboard paths check for an empty tab list before any index arithmetic, so no key press raises.
- Escape must await set_focus; an un-awaited call is silently discarded.
- Clicks matching no range do nothing and do not raise.
- Direct calls to next, previous, first-character search, and activate_tab_by_number with 0 on an empty list are not guarded. Callers are not expected to make them.
- Do not guard framework calls with attribute lookups or callability checks. Call the framework API directly so a mismatch fails visibly.

## Documentation

- Docstrings for Tab and Tabs in Args format. Each Tabs parameter is described, including its default. The on_key docstring describes the key behavior, including that Escape removes focus from the widget.
- Source comments describe what the code does. Do not cite the reference implementation, a pull request, or external artifacts.
- The UnderlineBar Args section documents clickable_ranges and must not claim that they apply on the zero-width early path.
- A docs reference page for the module, containing a single directive targeting the Tabs class in textual.widgets.tabs.
- The sandbox demo and its stylesheet are optional; tests do not require them.

## Maintainability

- Annotations in the Tabs module use the union form with a None alternative, not Optional, and postponed annotation evaluation, matching the reference tabs module.

## Compatibility

- Existing UnderlineBar callers keep identical rendered output for existing inputs. The item yielded by the bar's rich rendering changes from a sequence of segments to one text object. Callers passing width by position must switch to keyword passing.
- Existing Opacity callers keep identical color output. Other segment attributes are now preserved.
- Existing layout resolver callers keep identical results, and existing tests pass without modification.
- The minimum version is Python 3.7. Every new library and test module must import under 3.7. Use the postponed-annotation import or typing generics, because a builtin generic subscript in an unguarded annotation fails at import on 3.7.

## Behavioral acceptance criteria

1. Labels render on the first row and the underline on the second; the underline highlights the active tab's span.
2. The initial active tab is active_tab when given, otherwise the first tab.
3. Right and left keys cycle with wrap-around. Escape awaits set_focus with no target.
4. Digit keys activate by position, and key 0 follows the same rule for keys and direct calls. Superscript and circled numerals are not digit keys.
5. Letter search is case-insensitive, starts after the active tab, wraps, never selects the active tab, and is disabled when the flag is false.
6. A click inside an inactive tab's selection range activates it. A click outside every range does nothing.
7. A change of active tab animates the bar position.
8. With no tabs, the first row is empty and the second row shows only the full-width inactive underline, with no error.
9. Inactive labels, including padding cells, are dimmed by the configured opacity and carry the tab's click action.
10. A Tab without a name uses its label as its name. Duplicate names display once, at the first occurrence, with the last tab's label.
11. find_tab_by_name returns the first index for a duplicated name, and the underline sits under the displayed tab with the active name.
12. Key events are marked handled without stopping propagation.
13. Constructing Tabs with any tab list, including an empty one, succeeds without a style parsing error.
14. An UnderlineBar whose highlight takes the zero-width early path yields one text object whose spans carry no click metadata. A zero-width highlight at a non-zero position yields click metadata on its spans.

## Test requirements

- In tests/renderables/test_underline_bar.py, add a test that passes two clickable ranges with a small width, renders the bar with console and options doubles, and takes the first yielded item. Check that it is one text object whose last two spans have the given start and end columns and click metadata for the tab name in quoted form, in mapping order.
- Add a zero-width early-path test: a bar with no highlight, or a highlight the rule rejects, yields one text object whose spans carry no click metadata. Check each span's click metadata rather than asserting that the spans list is empty, since the background run adds a style span.
- Select spans of the tab under test by text position. Do not assert on the active tab's span. Before reading click metadata, confirm the style is a resolved style object, because a raw style string has no metadata attribute and reading it raises.
- Do not add trivial constant assertions, such as a character's absence from the default style string. Cover the default style through construction behavior.
- Do not assert rendered-string equality between bars with and without clickable ranges, and do not pin a fixed ANSI string where a click boundary splits a run. Check spans or per-cell metadata.
- Underline-row assertions check the highlight's cells and half-cell glyphs at its edges, not an exact uniform bar string. Half-cell glyphs also appear at whole-number edges that are not the bar's ends: the background cell before a highlight starting after cell zero shows a right-half glyph, and the background cell at a highlight end before the bar's width shows a left-half glyph. For example, a highlight from 2 to 4 on a bar of width 6 has plain text of one heavy bar, a right-half glyph, two heavy bars, a left-half glyph, and one heavy bar.
- Do not assert that the active tab's underline cells lack a click action. The reference attaches click actions to every displayed tab's underline cells, including the active one.
- Rendered label rows must follow the Workflows layout rule, or the test must pass an explicit tab_padding.
- Tests must not call asyncio.run, create or replace event loops, or otherwise change the thread's event-loop state. Test find_tab_by_name, the activate methods, action_range_clicked, and rendered output through the render helper directly. Do not drive on_key from tests unless the repository has an established key-event harness.
- Import every name a test module uses at the top of the module, never inside test functions.
- Existing underline tests pass unchanged. Use the existing render helper from the tests utilities for rendered-text checks.
- Tabs behavior tests are encouraged, following the repository's renderable and widget test pattern: duplicate names, the no-tabs row layout, padded-cell styling, first-index lookup, and construction with default styles. New test modules satisfy the Python 3.7 annotation rule.
