## Goals

- Provide a horizontal tab-bar widget, Tabs, in the public module textual.widgets.tabs, built from a list of Tab items. Users select a tab by keyboard or mouse, and the selection is shown by an animated underline bar.
- Each Tab has a display label and a name. Selection and activation identify tabs by name, not position.
- Build the feature from existing Textual mechanisms: widget default styles, @click action metadata and the event broker, reactive attributes with watchers, the animation facility, and rich-based renderables.

## Scope

In scope:
- The Tab data holder and the Tabs widget, both in textual.widgets.tabs.
- Clickable-range support in the existing UnderlineBar renderable.
- A style-preserving change to the existing Opacity renderable.
- Minimum-size support in the existing layout resolver's edge description.
- Docstrings, a docs reference page for the module, an optional sandbox demo, and tests.

Out of scope:
- Behavior changes to other widgets, new third-party dependencies, and changes to base Widget behavior.

Pull request body content (video, screenshots, demo command, checklist) is not a requirement. Clicks never select the "nearest" tab. A click activates the tab whose clickable span contains the clicked cell.

## Assumptions

- The target is the Textual repository at the base commit. Widget, reactive, animation, event broker, and rich renderable facilities exist there as they are.
- Widths are measured in terminal cells using cell-width functions, not character counts.
- The base App provides set_focus as a coroutine and has no method named focus; focus is a coroutine method of Widget. A coroutine called without await never runs, so a bare set_focus call has no effect.
- The message dispatch awaits an event handler's result when it is awaitable, so asynchronous key handlers are supported.

## Terminology

- Tab: a label and name pair.
- Label range: the columns occupied by a tab's label text, excluding padding.
- Selection range: the columns of a tab's padded span: left padding, label, and right padding. Clicks use this range.
- Displayed tabs: the tabs rendered, one per distinct name. Each sits where its name first appears and carries the label of the last Tab with that name (see Data model).
- Bar position: a fractional index into the displayed tabs that places the underline. The highlight spans the interpolated label range between the floor index and the next index, wrapping at the end.
- Clickable range: a named column span on the underline bar that carries a click action.
- Click action: the text range_clicked, followed by the tab name in single quotes, enclosed in parentheses. The name is always quoted, even when it is a plain word. It is attached as @click style metadata.

## Workflows

Rendering:
- The widget occupies two rows: labels on the first, the underline bar on the second. A line break always separates them, including when there are no tabs.
- Labels are laid out across the widget width. Each displayed tab contributes three edges: a left padding edge, a label edge sized to the label's cell width, and a right padding edge. When tab_padding is absent or zero, padding edges are flexible with a minimum of one cell. Flexible edges share the remaining width through the shared layout resolver: each gets the whole-cell part of its share, and the fractional leftover carries forward to the following flexible edges. When tab_padding is positive, each padding edge has that fixed size.
- A tab's padded span renders as one run of text, so padding cells share the label's style and click action.
- Every label span, active or inactive, is built from resolved style objects: each configured style is resolved against the console before it is attached. No label span carries a raw style string.
- The active tab's padded span uses the active tab style and carries no click action. Each inactive tab's padded span uses the inactive tab style, carries the click action for its own name, and is dimmed by inactive_text_opacity.
- The underline bar's highlight uses the active bar style over the interpolated bar position; the rest uses the inactive bar style. Its clickable ranges are the selection range of every displayed tab, keyed by name, in display order, including the active tab. Underline cells beneath the active tab therefore carry its click action even though its label does not.
- With no tabs, no labels are drawn. The first row is empty, and the second row is the full-width inactive underline with no highlight. This renders without error.

Initial state:
- The active tab name is active_tab if given and non-empty; otherwise it is the first tab's name. An active_tab matching no name is kept as given, and the bar sits at index 0. With no tabs, there is no active tab.
- The bar position starts at the find_tab_by_name index of the active tab name, which is 0 when not found.

Keyboard (while the Tabs widget receives key events; see Implementation constraints for the handler's form):
- With no tabs, mark the event handled and do nothing else.
- Escape awaits the app's set_focus with None as the target, releasing focus. Add no lookup or guard. Then mark the event handled. The reference's call is not awaited and therefore does nothing; this specification intentionally follows the documented intent that Escape removes focus.
- Right and left move to the next or previous tab over the full tab list, wrapping at either end. The current position is the find_tab_by_name index of the active tab name, so with duplicate names the first occurrence is the start.
- A digit key is one of the characters 0 through 9 only. Other characters that Unicode-aware checks report as digits, such as superscript or circled numerals, are not digit keys. They go to letter search when enabled, and are otherwise ignored.
- Digit keys 1 through 9 activate the tab at that 1-based position in the full list. The 0 key uses the number rule of activate_tab_by_number. A digit larger than the tab count is ignored. Digit handling takes precedence over letter search.
- When search_by_first_character is true, any other key activates the next tab after the active one, wrapping, whose label begins with that character, compared case-insensitively. Search covers the full list and never selects the active tab itself. With no other match, the active tab does not change. Search is skipped when the flag is false.
- Every key event is marked handled, including unhandled keys, by preventing its default action only. Propagation is never stopped, so application-level bindings still receive keys.

Mouse:
- A click on any cell within a tab's selection range activates that tab. This applies on both the label row and the underline row, since the click action is attached to both.
- Where clickable spans overlap, the span applied later in display order receives the click.
- A click outside every range does nothing.
- Clicking the active tab's label has no effect, because it carries no click action. Its underline cells do carry the action, so clicking them also changes nothing.

Animation:
- When the active tab changes, the bar position animates from its current value to the find_tab_by_name index of the new active tab, using the configured easing function and duration. A watcher on the active tab name drives the animation.

## Data model

- Tab: label (text, required) and name (text, optional, defaulting to label).
- Names are not unique. Displayed tabs: one entry per distinct name, positioned where that name first appears, with the label of the last Tab carrying that name. Duplicated names render once.
- The full tab list keeps every tab. Navigation, digit activation, first-character search, and find_tab_by_name use the full list.
- Tabs state: the full ordered tab list; the active tab name (a private reactive value, none when there are no tabs); the bar position (a private reactive float); the style values; the inactive opacity; the animation duration and easing name; tab_padding; and the search flag.
- Label ranges and selection ranges, keyed by name, are computed during rendering from the same width arithmetic and are the source for the underline bar's clickable ranges. Do not keep a separate hit-test computation.

## API contracts

- Module textual.widgets.tabs exports Tab and Tabs through its export list.
- Tab: a data holder with label and name, where name defaults to label. Two Tabs are equal when label and name match. Its representation shows both fields. Its text form is the label.
- Tabs is a Widget subclass. Its constructor takes these inputs, in order:
  - tabs: list of Tab (required).
  - active_tab: optional tab name, default none.
  - active_tab_style: style value, default "#f0f0f0 on #021720".
  - active_bar_style: style value, default "#1BB152".
  - inactive_tab_style: style value, default "#f0f0f0 on #021720".
  - inactive_bar_style: style value, default "#455058".
  - inactive_text_opacity: float, default 0.5.
  - animation_duration: float in seconds, default 0.3.
  - animation_function: easing name string, default "out_cubic".
  - tab_padding: optional integer cell count, default none, meaning auto-fit.
  - search_by_first_character: boolean, default true.
- Tabs default style: a single bare declaration string, with no selector and no braces, that sets the height to two rows. It is declared through the class attribute for default styles.
- Public Tabs methods and handlers, with these parameter names:
  - on_key, with one parameter named event: an asynchronous keyboard handler described in Workflows. On Escape it awaits the app's set_focus with no target. Its other paths await nothing.
  - activate_next_tab and activate_previous_tab: no parameters, synchronous. They move the active tab by one over the full list, with wrap-around.
  - activate_tab_by_first_char, with parameter char: synchronous. Applies the search rule in Workflows to one character.
  - activate_tab_by_number, with parameter tab_number: synchronous. Applies this mapping inside the method, so direct calls and key presses behave the same:
    - If tab_number is greater than the tab count, return with no change and no error.
    - If tab_number is 0 and there are at least ten tabs, activate the 10th tab.
    - If tab_number is 0 and there are fewer than ten tabs, activate the last tab through negative indexing.
    - Otherwise, activate the tab at the 1-based position tab_number.
  - find_tab_by_name, with parameter tab_name: synchronous. Returns the index of the first tab in the full list with that name, or 0 when none has it.
  - action_range_clicked, with parameter target_tab_name: synchronous. Sets the named tab as the active tab.
  - A watcher on the active tab name that animates the bar position.
- Tabs.render returns an internal renderable class in the same module, named TabsRenderable. It is not in the public export list.
- UnderlineBar: add an optional clickable_ranges input, a mapping from tab name to a (start, end) column pair. The end is exclusive. The default is empty. It is placed before the width input, which moves to the fifth position, so callers pass width by keyword. Existing style and highlight inputs keep their names, order, defaults, and meanings.
  - Rendering: the bar yields exactly one rich text object, not a sequence of segments. Its styled runs are built as before. Then, for each clickable range in mapping order, the bar attaches that name's click action to the span from start to end. These click spans are the last spans on the text object, in mapping order.
  - Zero-width early path: after the highlight range is clamped to the bar width (start raised to at least 0, end lowered to at most the width), the bar takes the early path when start and end are both zero, when end is negative, or when start is greater than end. The early path yields only the full-width background run, with no click-metadata spans. That run still has its own style span, so the spans list is not empty. The click step is reached only when the early path is not taken. Any other range, including a zero-width range at a non-zero position, renders its highlight and receives the click spans.
- Opacity: parameters unchanged. The blended color is merged into each segment's existing style, so other attributes, including click metadata, are preserved.
- Layout resolver edge: the edge description carries size (optional, default none), min_size (default 1), and fraction (default 1). Existing callers keep their results.
- Click dispatch: the action string resolves to action_range_clicked on the Tabs widget through the existing broker, with the widget as the default namespace.

## Module architecture

- textual/widgets/tabs.py holds Tab, TabsRenderable, and Tabs. Use the public module name tabs, not an underscore-prefixed module.
- Do not re-export Tabs from the textual.widgets package initializer.
- textual/renderables/underline_bar.py owns clickable-range metadata. The bar, not the widget, attaches click actions to spans.
- textual/renderables/opacity.py gets the style-merge change. The layout resolver module gets the edge minimum-size change.
- Responsibilities: Tabs owns state, keyboard handling, and animation. TabsRenderable owns the width arithmetic and produces the label row and the bar. Tabs.render delegates to TabsRenderable.
- Dependency direction: widgets may import renderables and the layout helper. Renderables must not import widgets.
- The optional sandbox demo lives under the sandbox directory, not in the library package. It must load and run: mount the example Tabs widgets directly on the App, use a stylesheet containing only CSS properties the builder supports, and do not call docking helpers that exist only on dock views.

## Implementation constraints

- Sizing: set the two-row height through the default style declaration. Do not set a sizing attribute on the instance, because layouts read the style value and ignore instance attributes.
- Default style parsing: every widget parses its default style string as bare declarations at construction. A selector block makes the tokenizer raise during construction, so every Tabs construction fails. Keep the default style bare.
- Constructor order: in Tabs.__init__, call the base Widget initializer first, then assign tab state, styles, and other attributes.
- Clicks: no coordinate hit-testing in an on_click handler and no custom click messages. Attach @click metadata to spans and let the existing broker dispatch to action_range_clicked.
- Keyboard: implement on_key as an asynchronous method so the Escape path can await set_focus. Check for no tabs first. For Escape, await the app's set_focus with no target, without a lookup or guard. Never leave a set_focus coroutine un-awaited. Compare keys against the key constants in textual.keys. Treat only the characters 0 through 9 as digits. Always mark the event handled by preventing its default action. Never stop propagation.
- Label styles: resolve every configured style value against the console into a style object before building any label span, for both active and inactive tabs. Never attach a raw style string to a label span.
- Animation: drive it from a reactive bar position and a watcher on the active tab name. Never move the bar instantly.
- Style values reaching the bar and label segments must always be resolved. Never pass a null style into the bar.
- Separate the label row from the underline row with a line break, including when there are no tabs.
- Existing UnderlineBar rendered output stays identical for existing inputs. The new metadata is additive.
- Keep lines within 88 columns (the repository's black style). Follow the repository's Google-style docstring Args format.

## Dependencies

- Use existing rich helpers for text, style, segments, and cell width; the Textual Widget, events, key constants, reactive values, and animation; and the Opacity, UnderlineBar, and layout resolver modules.
- No new third-party packages.

## Naming

- Classes: Tab, Tabs, TabsRenderable. Module: tabs.
- Methods: activate_next_tab, activate_previous_tab, activate_tab_by_first_char, activate_tab_by_number, find_tab_by_name, action_range_clicked. Do not use next_tab or previous_tab.
- Parameter names: char, tab_number, tab_name, target_tab_name.
- Reactive attributes are private: the active tab name and the bar position are private reactives with leading underscores. The active-tab watcher follows the watcher naming convention for that private name.
- Action string: range_clicked. Clickable-range input: clickable_ranges.
- Use snake_case for functions and attributes, and PascalCase for classes.

## Validation

- tabs may be empty. An empty list is supported.
- active_tab is matched by name. An unknown name is accepted without error, and the bar position falls back to index 0.
- inactive_text_opacity is used as a blend ratio.
- tab_padding of zero is treated the same as absent (auto-fit), matching the reference's truthiness check.
- Only the characters 0 through 9 are digit keys. Digit keys outside the tab count are ignored without error.

## Error handling

- Every style input to the bar must be resolved. A null style makes style resolution raise on every bar render, including the no-tabs path.
- A default style with a selector block makes construction raise a tokenizer error, so every Tabs construction fails, including with an empty list. Use the bare-declaration default style.
- Keyboard paths check for an empty tab list before any index arithmetic, so no key press raises.
- The Escape path must await set_focus. An un-awaited call is silently discarded, so Escape would appear ignored with no error.
- Clicks that match no range do nothing and do not raise.
- activate_tab_by_number with a tab number greater than the tab count returns without error or change.
- Direct calls to next, previous, first-character search, and activate_tab_by_number with 0 on an empty list are unguarded. Callers are not expected to make them.
- Framework calls are not guarded by lookups. Do not probe for a framework method with an attribute lookup followed by a callability or None check, because that silently skips a missing API. Call the framework API directly so that a mismatch fails visibly.

## Documentation

- Docstrings for Tab and Tabs in the repository's Args format. Each Tabs parameter is described, including its default.
- The on_key docstring describes the key behavior, including that Escape removes focus from the widget.
- Source comments describe what the code does. Do not cite the reference implementation, a pull request, or other external artifacts.
- The UnderlineBar Args section documents clickable_ranges. It must not state that clickable ranges are applied on the zero-width early path.
- A docs reference page for the module, containing a single directive whose target is the Tabs class in textual.widgets.tabs.
- An optional sandbox demo under the sandbox directory, with a stylesheet. Tests do not require it.

## Maintainability

- Tabs module annotations use the union form with a None alternative, not Optional, and postponed annotation evaluation, matching the reference tabs module.

## Compatibility

- Existing UnderlineBar callers keep identical rendered output for existing inputs. The yielded item changes from a sequence of segments to one text object. Callers passing width by position must switch to keyword passing.
- Existing Opacity callers keep identical color output. Other segment attributes are now preserved.
- Existing layout resolver callers with size and fraction values keep identical results.
- Existing tests pass without modification.
- The project's minimum is Python 3.7. Every new library and test module must import under 3.7. Annotations use the postponed-annotation import or typing generics, because a builtin generic subscript in an unguarded annotation fails at import on 3.7.

## Behavioral acceptance criteria

1. A Tabs widget built from a tab list renders labels on the first row and the underline on the second. The underline highlights the active tab's span.
2. The initial active tab is active_tab when given, otherwise the first tab.
3. Right and left keys cycle with wrap-around. Escape awaits the app's set_focus with no target, releasing focus.
4. Digit keys activate by position. The 0 key follows the reference rule for fewer than ten and for ten or more tabs, and direct calls to activate_tab_by_number follow the same rule. Characters outside 0 through 9, including superscript or circled numerals, are not digit keys.
5. Letter search is case-insensitive, starts after the active tab, wraps, never selects the active tab, and is disabled when the flag is false.
6. A click inside an inactive tab's selection range activates that tab. A click outside every range does nothing.
7. A change of active tab animates the bar position.
8. With no tabs, the first row is empty and only the full-width inactive underline is drawn, with no error.
9. Inactive labels, including their padding cells, are dimmed by the configured opacity and carry the tab's click action.
10. A Tab without a name uses its label as its name.
11. Duplicate names display once, at the first occurrence's position, with the last tab's label. find_tab_by_name returns the first index, and the underline sits under the displayed tab with the active name.
12. Key events are marked handled without stopping propagation.
13. Constructing a Tabs widget with any tab list, including an empty one, succeeds without a style parsing error.
14. An UnderlineBar whose highlight takes the zero-width early path yields one text object whose spans carry no click metadata. A zero-width highlight at a non-zero position yields click metadata on its spans.

## Test requirements

- In tests/renderables/test_underline_bar.py, add a required test that passes two clickable ranges with a small width, renders the bar's rich output with console and options doubles, and takes the first yielded item. It must check that the item is one text object whose last two spans have the given start and end columns and the click metadata for the tab name in the quoted form described in Terminology, in mapping order.
- Add a zero-width early-path test: a bar with no highlight, or a highlight the early-path rule rejects, yields one text object whose spans carry no click metadata. Do not assert that the spans list is empty, because the background run adds its own style span. Check each span's click metadata instead.
- Span-metadata tests select the spans of the tab under test by text position. Do not assert on every span, because the active label intentionally carries no click action. Before reading click metadata from a span's style, confirm the style is a resolved style object; a raw style string has no metadata attribute, and reading it raises.
- Do not add trivial assertions about constants, such as checking that a character is absent from the default style string. Cover the default style through construction behavior instead.
- Do not assert rendered-string equality between a bar with clickable ranges and one without, and do not pin a fixed ANSI string where a click boundary splits a run. Check spans or per-cell metadata instead.
- Underline-row assertions check the highlight's cells and the half-cell glyphs at its edges, not an exact uniform bar string. Half-cell glyphs appear whenever highlight edges are fractional, and also when they are whole numbers not at the bar's ends: the background cell just before a highlight that starts after cell zero shows a right-half glyph, and the background cell at a highlight end before the bar's width shows a left-half glyph. For example, a highlight from 2 to 4 on a bar of width 6 has plain text of one heavy bar, a right-half glyph, two heavy bars, a left-half glyph, and one heavy bar. Do not expect six heavy bars.
- Do not assert that the active tab's underline cells lack a click action. The reference attaches the click action to the underline cells of every displayed tab, including the active one.
- Expected label rows must be derived from the layout rule in Workflows, or the test must pass an explicit tab_padding. Do not hand-write an auto-fit label row without computing the flexible shares.
- Tests must not call asyncio.run, create or replace event loops, or otherwise change the thread's event-loop state, because that breaks later widget construction. Test the synchronous methods and the rendered label and bar output through the render helper directly. Do not drive on_key from tests unless the repository has an established key-event harness.
- Import every name a test module uses at the top of that module, not inside test functions.
- Existing underline tests pass unchanged. New rendered-text checks use the existing render helper from the tests utilities.
- Tabs behavior tests are encouraged, following the repository's renderable and widget test pattern. Useful cases include duplicate names, the no-tabs row layout, padded-cell styling, first-index lookup, and construction with default styles. New test modules satisfy the Python 3.7 annotation rule in Compatibility.
