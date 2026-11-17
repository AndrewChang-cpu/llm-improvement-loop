## Goals

- Provide a horizontal tab-bar widget, Tabs, in the public module textual.widgets.tabs. It is built from a list of Tab items. A user can select a tab by keyboard or mouse, and the selection is shown by an animated underline bar.
- Each Tab has a display label and a name. Selection and activation are identified by name, not by position.
- Build the feature from existing Textual mechanisms: widget default styles, the @click action metadata and event broker, reactive attributes with watchers, the animation facility, and rich-based renderables.

## Scope

In scope:
- The Tab data holder and the Tabs widget, both in textual.widgets.tabs.
- Clickable-range support in the existing UnderlineBar renderable.
- A style-preserving change to the existing Opacity renderable.
- Minimum-size support in the existing layout resolver's edge description.
- Docstrings, a docs reference page for the module, an optional sandbox demo, and tests.

Out of scope:
- Behavior changes to other widgets. Import cleanups elsewhere are incidental, not part of the feature, and not required.
- New third-party dependencies.
- Changes to the base Widget behavior.

Non-normative content from the pull request body (video, screenshots, demo command, and the checklist) is not a requirement. Clicks do not select the "nearest" tab. A click activates the tab whose clickable span contains the clicked cell.

## Assumptions

- The target is the Textual repository at the base commit. Widget, reactive, animation, event broker, and rich renderable facilities are available as they exist there.
- Widths are measured in terminal cells. Wide characters are measured with cell-width functions, not character counts.
- The base App provides set_focus as a coroutine and has no method named focus. The coroutine method named focus belongs to Widget, not App. Calls to set_focus that are not awaited do not run (see Workflows, Keyboard).

## Terminology

- Tab: a label and a name pair.
- Label range: the columns occupied by a tab's label text, not including padding.
- Selection range: the columns occupied by a tab's padded span, which is its left padding, its label, and its right padding. Clicks use this range.
- Displayed tabs: the tabs that are rendered. There is one displayed tab per distinct name. It takes the position of the first tab with that name and the label of the last tab with that name (see Data model).
- Bar position: a fractional index into the displayed tabs that places the underline. The highlight spans the interpolated label range between the floor index and the next index, wrapping at the end.
- Clickable range: a named column span on the underline bar that carries a click action.
- Click action: the action string made of the text range_clicked, followed by the tab name enclosed in single quotes and then in parentheses. The name is always quoted, even when it is a plain word. The action is attached as @click style metadata.

## Workflows

Rendering:
- The Tabs widget occupies two rows. The first row holds the labels. The second row holds the underline bar. A line break always separates the two rows, including when there are no tabs.
- Labels are laid out across the widget width. Each displayed tab contributes three edges: a left padding edge, a label edge sized to the label's cell width, and a right padding edge. When tab_padding is absent or zero, the padding edges are flexible with a minimum of one cell. Flexible edges share the remaining width through the shared layout resolver: each flexible edge gets the whole-cell part of its share, and the fractional leftover is carried forward to the following flexible edges. When tab_padding is a positive value, each padding edge is that fixed size.
- A tab's padded span (left padding, label, and right padding) is rendered as one run of text, so the padding cells take the same style and click action as the label.
- The active tab's padded span uses the active tab style and carries no click action. Each inactive tab's padded span uses the inactive tab style, carries the click action for its own name, and is dimmed by inactive_text_opacity.
- The underline row is an underline bar. Its highlight spans the active bar style over the interpolated bar position. The rest uses the inactive bar style. Its clickable ranges are the selection range of every displayed tab, keyed by tab name, in display order. This includes the active tab, so the underline cells beneath the active tab carry that tab's click action even though its label does not.
- With no tabs, no labels are drawn. The first row is empty, and the second row is the full-width inactive underline with no highlight. This must render without error.

Initial state:
- The active tab name is active_tab if it is given and non-empty. Otherwise it is the name of the first tab. An active_tab that matches no name is kept as given, and the bar then sits at index 0. With no tabs, there is no active tab.
- The bar position starts at the index returned by find_tab_by_name for the active tab name. A name that is not found gives 0.

Keyboard (applies while the Tabs widget receives key events; the key handler is synchronous, see API contracts):
- With no tabs, the key event is marked handled and nothing else happens.
- Escape makes a bare call to the app's set_focus with None as the target. The call has no lookup, no guard, and no await, matching the reference. Because set_focus is a coroutine, the call does not run, so Escape does not currently remove focus. This is an inherited limitation of the reference. The widget adds no other focus handling, and its docstrings and comments must not claim that focus is removed.
- Right and left move to the next and previous tab, wrapping at either end. They operate on the full tab list. The current position is the index returned by find_tab_by_name for the active tab name, so with duplicate names the first occurrence is the starting point.
- A key is a digit key only when it is one of the characters 0 through 9. Other characters that some Unicode-aware checks report as digits, such as superscript or circled numerals, are not digit keys. They go to letter search when it is enabled, and are otherwise ignored.
- Digit keys 1 through 9 activate the tab at that 1-based position in the full tab list. The 0 key uses the number rule of activate_tab_by_number (see API contracts). A digit larger than the tab count is ignored.
- Digit handling takes precedence over letter search.
- When search_by_first_character is true, any other key activates the next tab after the active one, wrapping, whose label begins with that character, compared case-insensitively. The search covers the full tab list and never selects the active tab itself. If no other tab matches, the active tab does not change. The search is skipped when the flag is false.
- Every key event is marked handled, including unhandled keys. Handling is done by preventing the event's default action only. The event must not be stopped from propagating, so application-level bindings still receive keys.

Mouse:
- A click on any cell within a tab's selection range activates that tab. This applies on the label row and on the underline row, because the click action is attached to both.
- Where two clickable spans overlap, the span applied later in display order receives the click.
- A click outside every tab range does nothing.
- Clicking the active tab's label has no effect, because the active label does not carry the click action. The active tab's underline cells do carry the action, so clicking them also changes nothing.

Animation:
- When the active tab changes, the bar position animates from its current value to the index of the new active tab (from find_tab_by_name). It uses the configured easing function and duration. The animation is driven by a watcher on the active tab name.

## Data model

- Tab: label (text, required) and name (text, optional). When name is absent, it defaults to the label.
- Tab names are not unique. Displayed tabs are computed from the tab list as follows: one entry per distinct name; the entry's position is where that name first appears; the entry's label comes from the last Tab with that name. Only displayed tabs are rendered, so a duplicated name appears once.
- The full tab list keeps every tab. Navigation, digit activation, first-character search, and find_tab_by_name use the full list.
- Tabs state: the full ordered tab list; the active tab name (a private reactive value, none when there are no tabs); the bar position (a private reactive floating-point value); the style values; the inactive opacity; the animation duration and easing name; tab_padding; and the search flag.
- Label ranges and selection ranges, keyed by tab name, are computed during rendering from the same width arithmetic. They are the source for the underline bar's clickable ranges. Do not keep a separate hit-test computation.

## API contracts

- Module textual.widgets.tabs exports the names Tab and Tabs through its export list.
- Tab: a data holder with label and name, where name defaults to label. Two Tabs are equal when label and name are equal. Its representation shows both fields. Its text form is the label.
- Tabs is a Widget subclass. Its constructor takes these inputs in this order:
  - tabs: list of Tab (required).
  - active_tab: optional tab name. Default none.
  - active_tab_style: style value. Default "#f0f0f0 on #021720".
  - active_bar_style: style value. Default "#1BB152".
  - inactive_tab_style: style value. Default "#f0f0f0 on #021720".
  - inactive_bar_style: style value. Default "#455058".
  - inactive_text_opacity: float. Default 0.5.
  - animation_duration: float in seconds. Default 0.3.
  - animation_function: easing name string. Default "out_cubic".
  - tab_padding: optional integer cell count. Default none, meaning auto-fit.
  - search_by_first_character: boolean. Default true.
- Tabs default style: the widget's default style is a single bare declaration string that sets the height to two rows. It contains no selector and no braces. Declare it through the class attribute for default styles.
- Public Tabs methods and handlers, with these parameter names:
  - on_key, with one parameter named event: a synchronous keyboard handler described in Workflows. It does not await anything. Its Escape path is a bare call to the app's set_focus with no target. It is the handler for key events while the widget has focus.
  - activate_next_tab and activate_previous_tab: take no parameters and are synchronous. They move the active tab by one over the full tab list, with wrap-around.
  - activate_tab_by_first_char, with parameter char: synchronous. Takes one character and applies the search rule in Workflows.
  - activate_tab_by_number, with parameter tab_number: synchronous. Takes an integer tab number and applies this mapping inside the method, so direct calls and key presses behave the same:
    - If tab_number is greater than the number of tabs, return with no change and no error.
    - If tab_number is 0 and there are at least ten tabs, activate the 10th tab.
    - If tab_number is 0 and there are fewer than ten tabs, activate the last tab through negative indexing.
    - Otherwise activate the tab at the 1-based position tab_number.
  - find_tab_by_name, with parameter tab_name: synchronous. Returns the index of the first tab in the full tab list with that name, or 0 when no tab has it. Duplicate names return the first match, never the last.
  - action_range_clicked, with parameter target_tab_name: synchronous. Sets the named tab as the active tab.
  - A watcher on the active tab name that animates the bar position.
- Tabs.render returns an internal renderable class in the same module, named TabsRenderable. It is not part of the public export list.
- UnderlineBar: add an optional clickable-ranges input, a mapping from tab name to a (start, end) column pair. The end is exclusive. The default is empty. It is placed before the width input, which therefore moves to the fifth position, so callers pass width by keyword. The existing style and highlight inputs keep their names, order, defaults, and meanings.
  - Rendering contract: the bar yields exactly one rich text object, not a sequence of segments. Its styled runs are built as before. Then, for each clickable range in mapping order, the bar attaches the click action for that name to the span from start to end. Those click spans are the last spans on the text object, in mapping order.
  - Zero-width early path: after the highlight range is clamped to the bar width (start raised to at least 0, end lowered to at most the width), the bar takes its early path when start and end are both zero, or when end is negative, or when start is greater than end. On that path it yields only the full-width background run, and that text carries no click-metadata spans. The background run still has its own style span, so the spans list is not empty. Any other range, including a zero-width range at a non-zero position, is rendered with its highlight and receives the click spans.
- Opacity: parameters are unchanged. The blended color is combined into each segment's existing style, so other attributes, including click metadata, are preserved.
- Layout resolver edge: the edge description carries size (optional, default none), min_size (default 1), and fraction (default 1). Existing callers keep their current results.
- Click action dispatch: the action string resolves to the Tabs widget's action_range_clicked through the existing broker, with the widget as the default namespace.

## Module architecture

- textual/widgets/tabs.py holds Tab, TabsRenderable, and Tabs. Use the public module name tabs, not a private underscore-prefixed module.
- Do not re-export Tabs from the textual.widgets package initializer.
- textual/renderables/underline_bar.py owns clickable-range metadata. The bar, not the widget, attaches click actions to spans.
- textual/renderables/opacity.py gets the style-merge change.
- The layout resolver module gets the edge minimum-size change.
- Responsibilities: Tabs owns state, keyboard handling, and animation. TabsRenderable owns the width arithmetic and produces the label row and the bar. Tabs.render delegates to TabsRenderable.
- Dependency direction: widgets may import renderables and the layout helper. Renderables must not import widgets.
- The optional sandbox demo lives under the sandbox directory, not in the library package. It must load and run: mount the example Tabs widgets directly on the App, use a stylesheet that contains only CSS properties the builder supports, and do not call docking helpers that exist only on dock views.

## Implementation constraints

- Sizing: set the two-row height through the widget's default style declaration, as a single bare declaration string with no selector and no braces. Do not set a sizing attribute on the instance. Layouts read the style value, so an instance attribute is ignored.
- Default style parsing: every widget parses its default style string as bare declarations when it is constructed. A default style that wraps its declarations in a selector block makes the style tokenizer raise an error during construction, so every construction of the widget fails. Keep the default style to bare declarations.
- Constructor order: in Tabs.__init__, call the base Widget initializer first, then assign tab state, styles, and the other attributes.
- Clicks: do not implement coordinate hit-testing in an on_click handler and do not post custom click messages. Attach @click metadata to spans and let the existing broker dispatch to action_range_clicked.
- Keyboard: implement on_key as a synchronous method. Check for no tabs first. For Escape, make a bare call to the app's set_focus with no target, without a lookup, a guard, or an await. Compare keys against the key constants in textual.keys. Treat only the characters 0 through 9 as digits. Always mark the event handled by preventing its default action. Never stop the event's propagation.
- Animation: drive it from a reactive bar position and a watcher on the active tab name. Do not move the bar instantly.
- Style values reaching the bar and the label segments must always be resolved values. Never pass a null style into the bar.
- Separate the label row from the underline row with a line break, including when there are no tabs.
- Keep existing UnderlineBar rendered output identical for existing inputs. The new metadata must be additive.
- Keep lines within 88 columns (the repository's black style). Follow the repository's Google-style docstring Args format.

## Dependencies

- Use existing rich helpers for text, style, segments, and cell width; the Textual Widget, events, key constants, reactive values, and animation; and the Opacity, UnderlineBar, and layout resolver modules.
- No new third-party packages.

## Naming

- Classes: Tab, Tabs, TabsRenderable. Module: tabs.
- Methods: activate_next_tab, activate_previous_tab, activate_tab_by_first_char, activate_tab_by_number, find_tab_by_name, action_range_clicked. Do not use next_tab or previous_tab.
- Parameter names: char, tab_number, tab_name, target_tab_name.
- Reactive attributes are private: the active tab name is stored as a private reactive named with a leading underscore, and so is the bar position. The active-tab watcher follows the watcher naming convention for that private name.
- Action string: range_clicked. Clickable-range input: clickable_ranges.
- Use snake_case for functions and attributes, and PascalCase for classes.

## Validation

- tabs may be empty. An empty list is a supported state.
- active_tab is matched by name. An unknown name is accepted without error, and the bar position then falls back to index 0.
- inactive_text_opacity is used as a blend ratio.
- tab_padding of zero is treated the same as absent (auto-fit), matching the reference's truthiness check.
- Only the characters 0 through 9 are digit keys. Digit keys outside the tab count are ignored without error.

## Error handling

- Every style input to the bar must be a resolved value. A null style makes style resolution raise on every bar render, including the no-tabs path.
- A default style with a selector block makes widget construction raise a tokenizer error, because construction parses the default style as bare declarations. Any Tabs construction then fails, including with an empty tab list. The fix is the bare-declaration default style described in Implementation constraints.
- Keyboard paths must check for an empty tab list before any index arithmetic, so no key press raises.
- Clicks that match no range must do nothing and must not raise.
- activate_tab_by_number with a tab number greater than the tab count returns without error or change.
- Direct calls to next or previous, to first-character search, and to activate_tab_by_number with 0 on an empty list are not guarded. Callers are not expected to make those calls.
- Framework calls are not guarded by lookups. Do not probe for a framework method with an attribute lookup followed by a callability or None check, because that silently skips a missing API. Call the framework API directly so that a mismatch fails visibly.

## Documentation

- Docstrings for Tab and Tabs in the repository's Args format. Each Tabs parameter is described, including the defaults.
- The on_key docstring describes the key behavior. For Escape, it describes the bare set_focus call with no target and does not state that focus is removed.
- Source comments describe what the code does. Do not cite the reference implementation, a pull request, or other external artifacts in comments, and do not describe a known-ineffective call as intended.
- The UnderlineBar Args section documents clickable_ranges.
- A docs reference page for the module, containing a single directive whose target is the Tabs class in textual.widgets.tabs.
- An optional sandbox demo under the sandbox directory with a stylesheet. It is not required by tests.

## Maintainability

- Annotations in the Tabs module use the union form with a None alternative, not Optional, and postponed annotation evaluation, matching the reference tabs module.

## Compatibility

- Existing UnderlineBar callers keep identical rendered output for existing inputs. The item yielded by the bar's rich rendering changes from a sequence of segments to one text object. Callers that pass width by position must switch to keyword passing because of the new input's position.
- Existing Opacity callers keep identical color output. Other segment attributes are now preserved.
- Existing layout resolver callers with size and fraction values keep identical results.
- Existing tests must pass without modification.

## Behavioral acceptance criteria

1. A Tabs widget built from a tab list renders two rows: labels on the first row and the underline on the second row. The underline highlights the active tab's span.
2. The initial active tab is active_tab when given, otherwise the first tab.
3. Right and left keys cycle with wrap-around. Escape makes a bare set_focus call on the app with no target, without an await or a lookup guard, as described in Workflows.
4. Digit keys activate by position. The 0 key follows the reference rule for fewer than ten tabs and for ten or more, and the same rule applies to direct calls to activate_tab_by_number. Characters outside 0 through 9, including superscript or circled numerals, are not digit keys and do not activate a tab by number.
5. Letter search is case-insensitive, starts after the active tab, wraps, never selects the active tab, and is disabled when the flag is false.
6. A click inside an inactive tab's selection range activates that tab. A click outside every range does nothing.
7. A change of active tab animates the bar position.
8. With no tabs, the first row is empty and only the full-width inactive underline is drawn on the second row, with no error raised.
9. Inactive labels, including their padding cells, are dimmed by the configured opacity and carry the tab's click action.
10. A Tab without a name uses its label as its name.
11. Tabs with duplicate names display once, at the first occurrence's position, with the last tab's label. find_tab_by_name returns the first index for a duplicated name, and the underline sits under the displayed tab with the active name.
12. Key events are marked handled without stopping propagation, so application-level bindings still receive keys.
13. Constructing a Tabs widget with any tab list, including an empty one, succeeds without a style parsing error.

## Test requirements

- In tests/renderables/test_underline_bar.py, add a test that passes two clickable ranges with a small width, renders the bar's rich output with console and options doubles, and takes the first yielded item. It must check that the item is one text object whose last two spans have the given start and end columns and the click metadata for the tab name in the quoted form described in Terminology, in mapping order. This is the required new test.
- Add a test for the zero-width early path: a bar with no highlight, or a highlight that the early-path rule rejects, yields one text object whose spans carry no click metadata. Do not assert that the spans list is empty, because the background run adds its own style span. Check the click metadata of each span instead.
- Do not add trivial assertions about constants, such as checking that a character is absent from the default style string. Cover the default style through construction behavior instead.
- Do not assert rendered-string equality between a bar with clickable ranges and a bar without them, and do not pin a fixed ANSI string where a click boundary splits a run. Click boundaries split runs, so such assertions are brittle. Check spans or per-cell metadata instead.
- Assertions on the underline row must check the highlight's cells and the half-cell glyphs at its edges, not an exact uniform bar string. Half-cell glyphs appear whenever the highlight edges are fractional, and also when they are whole numbers that are not at the bar's ends: the background cell just before a highlight that starts after cell zero shows a right-half glyph, and the background cell at a highlight end that is before the bar's width shows a left-half glyph. For example, a highlight from 2 to 4 on a bar of width 6 has plain text of one heavy bar, a right-half glyph, two heavy bars, a left-half glyph, and one heavy bar. Do not expect six heavy bars.
- Do not assert that the active tab's underline cells lack a click action. The reference attaches the click action to the underline cells of every displayed tab, including the active one.
- Expected rendered label rows must be derived from the layout rule in Workflows, or the test must pass an explicit tab_padding. Do not hand-write an exact label row for auto-fit padding without computing the flexible shares.
- Tests must not call asyncio.run, create or replace event loops, or otherwise change the thread's event-loop state, because that breaks later widget construction. Test the synchronous methods (find_tab_by_name, the activate methods, action_range_clicked, and the rendered label and bar output through the render helper) directly. Do not drive on_key from tests unless the repository has an established harness for key events.
- Existing underline tests must pass unchanged.
- New tests should use the existing render helper from the tests utilities for rendered-text checks.
- Tabs behavior tests are encouraged for the widget, following the repository's renderable and widget test pattern. Useful cases include duplicate names, the no-tabs row layout, padded-cell styling, first-index lookup, and construction with default styles.
