## Goals

- Provide a horizontal tab-bar widget, Tabs, in the public module textual.widgets.tabs. It is built from a list of Tab items. A user can select a tab by keyboard or mouse, and the selection is shown by an animated underline bar.
- Each Tab has a display label and a name. Selection and activation are identified by name, not by position.
- Build the feature from the existing Textual mechanisms: widget default styles, the @click action metadata and broker, reactive attributes with watchers, the animation facility, and rich-based renderables.

## Scope

In scope:
- The Tab data holder and the Tabs widget, both in textual.widgets.tabs.
- Click-range support in the existing UnderlineBar renderable.
- A style-preserving change to the existing Opacity renderable.
- Minimum-size support in the existing layout resolver's edge description.
- Docstrings, a docs reference page for the module, an optional sandbox demo, and tests.

Out of scope:
- Any change to other widgets. Import cleanups elsewhere are not part of the feature.
- New third-party dependencies.
- Changes to the base Widget behavior.

Non-normative content from the pull request body (video, screenshots, demo command, and the checklist) is not a requirement. Do not describe clicks as "nearest tab" activation. Clicks activate the tab whose clickable span contains the clicked cell.

## Assumptions

- The target is the Textual repository at the base commit. Widget, reactive, animation, event broker, and rich renderable facilities are available as they exist there.
- Widths are measured in terminal cells. Wide characters are measured with cell-width functions, not character counts.

## Terminology

- Tab: a label and a name pair.
- Label range: the columns occupied by a tab's label text, not including padding.
- Selection range: the columns occupied by a tab including the padding on both sides. Clicks use this range.
- Bar position: a fractional tab index that places the underline. The highlight spans the interpolated label range between the floor index and the next index, wrapping at the end.
- Clickable range: a named column span on the underline bar that carries a click action.
- Click action: the action string `range_clicked` with the tab name as its argument in parentheses. It is attached as @click style metadata.

## Workflows

Rendering:
- The Tabs widget occupies two rows. The first row holds the labels. The second row holds the underline bar. A line break separates the two rows.
- Labels are laid out across the widget width. Each tab has a label edge sized to its label's cell width, and a padding edge on each side. When tab_padding is absent, the padding edges are flexible with a minimum of one cell and an equal share of remaining space. When tab_padding is present, each padding edge is that fixed size.
- The active tab's label uses the active tab style. Each inactive label uses the inactive tab style, is dimmed by inactive_text_opacity, and carries the click action for its own name.
- The underline row is an UnderlineBar. Its highlight spans the active bar style over the interpolated bar position. The rest uses the inactive bar style. Its clickable ranges are every tab's selection range, keyed by tab name.
- With no tabs, no labels are drawn. Only the inactive underline row is drawn, full width, with no highlight. This must render without error.

Initial state:
- The active tab is the tab named by active_tab. If active_tab is absent, it is the first tab. With no tabs, there is no active tab.
- The bar position starts at the index of the active tab. If the name is not found, the index is 0.

Keyboard (applies while the Tabs widget receives key events):
- With no tabs, the key event is marked handled and nothing else happens.
- Escape clears focus from the widget.
- Right and left move to the next and previous tab, wrapping at either end.
- Digit keys 1 through 9 activate the tab at that 1-based position. A digit larger than the tab count is ignored.
- The 0 key activates the 10th tab when there are at least ten tabs. With fewer than ten tabs, the reference resolves 0 to the last tab through negative indexing. Preserve this reference behavior.
- Digit handling takes precedence over letter search.
- When search_by_first_character is true, any other key activates the next tab after the active one, wrapping, whose label begins with that character, compared case-insensitively. The search is skipped when the flag is false.
- Every key event is marked handled, including unhandled keys.

Mouse:
- A click on any cell within a tab's selection range activates that tab. This applies on the label row and on the underline row, because the click action is attached to both.
- A click outside every tab range does nothing.
- Clicking the active tab's label has no effect, because the active label does not carry the click action.

Animation:
- When the active tab changes, the bar position animates from its current value to the new tab index. It uses the configured easing function and duration. The animation is driven by a watcher on the active tab name.

## Data model

- Tab: label (text, required) and name (text, optional). When name is absent, it defaults to the label.
- Tab names are not checked for uniqueness. When names collide, the reference's name-keyed lookup keeps only the last tab with that name for rendering. The tab list keeps every tab.
- Tabs state: the ordered tab list; the active tab name (a reactive value, empty when there are no tabs); the bar position (a reactive floating-point value); the style values; the inactive opacity; the animation duration and easing name; tab_padding; and the search flag.
- Label ranges and selection ranges, keyed by tab name, are computed during rendering from the same width arithmetic. They are the source for the underline bar's clickable ranges. Do not keep a separate hit-test computation.

## API contracts

- Module textual.widgets.tabs exports the names Tab and Tabs through its export list.
- Tab: a data holder with label and name, with name defaulting to label. Its text form is the label.
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
- Tabs default style: height is two rows. Declare this through the widget's default style mechanism.
- Public Tabs methods and handlers:
  - activate_next_tab and activate_previous_tab: move the active tab by one with wrap-around.
  - activate_tab_by_first_char: takes one character.
  - activate_tab_by_number: takes an integer tab number, with the 0 rule above.
  - find_tab_by_name: takes a name and returns its index, or 0 when the name is not found.
  - action_range_clicked: takes a tab name and sets it as the active tab.
  - on_key: keyboard handler as described in Workflows.
  - A watcher on the active tab name that animates the bar position.
- Tabs.render returns an internal renderable class in the same module, named TabsRenderable. It is not part of the public export list.
- UnderlineBar: add an optional clickable-ranges input, a mapping from tab name to a (start, end) column pair. Default is empty. It goes before the width input. Existing inputs, their order, defaults, and meanings are unchanged. The bar attaches the click action for each name to its span.
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
- The optional sandbox demo lives under the sandbox directory, not in the library package.

## Implementation constraints

- Sizing: set the two-row height through the widget's default style declaration. Do not set a sizing attribute on the instance. Layouts read the style value, so an instance attribute is ignored.
- Clicks: do not implement coordinate hit-testing in an on_click handler and do not post custom click messages. Attach @click metadata to spans and let the existing broker dispatch to action_range_clicked.
- Keyboard: handle keys in on_key, check for no tabs first, and always mark the event handled.
- Animation: drive it from a reactive bar position and a watcher on the active tab name. Do not move the bar instantly.
- Style values reaching the bar and the label segments must always be resolved values. Never pass a null style into the bar.
- Separate the label row from the underline row with a line break.
- Keep existing UnderlineBar output identical for existing inputs. The new metadata must be additive.
- Keep lines within 88 columns (the repository's black style). Follow the repository's Google-style docstring Args format.

## Dependencies

- Use existing rich helpers for text, style, segments, and cell width; the Textual Widget, events, key constants, reactive values, and animation; and the Opacity, UnderlineBar, and layout resolver modules.
- No new third-party packages.

## Naming

- Classes: Tab, Tabs, TabsRenderable. Module: tabs.
- Methods: activate_next_tab, activate_previous_tab, activate_tab_by_first_char, activate_tab_by_number, find_tab_by_name, action_range_clicked. Do not use next_tab or previous_tab.
- Action string: range_clicked. Clickable-range input: clickable_ranges.
- Use snake_case for functions and attributes, and PascalCase for classes.

## Validation

- tabs may be empty. An empty list is a supported state.
- active_tab is matched by name. An unknown name is accepted without error, and the bar position then falls back to index 0.
- inactive_text_opacity is used as a blend ratio.
- Digit keys outside the tab count are ignored without error.

## Error handling

- Failure identified in one run: Tabs.render passed a null highlight style into UnderlineBar. UnderlineBar then resolves that style through the console and raises on every render, including the no-tabs path. Every style input to the bar must be a resolved value.
- Keyboard paths must check for an empty tab list before any index arithmetic, so no key press raises.
- Clicks that match no range must do nothing and must not raise.
- Direct calls to next or previous on an empty list are not guarded by the reference. Callers are not expected to make that call.

## Documentation

- Docstrings for Tab and Tabs in the repository's Args format. Each Tabs parameter is described, including the defaults.
- The on_key docstring describes the key behavior.
- The UnderlineBar Args section documents clickable_ranges.
- A docs reference page for the module, containing a single directive that points to textual.widgets.tabs.Tabs.
- An optional sandbox demo under the sandbox directory with a stylesheet. It is not required by tests.

## Compatibility

- Existing UnderlineBar callers keep identical rendered output for existing inputs.
- Existing Opacity callers keep identical color output. Other segment attributes are now preserved.
- Existing layout resolver callers with size and fraction values keep identical results.
- Existing tests must pass without modification.

## Behavioral acceptance criteria

1. A Tabs widget built from a tab list renders two rows: labels on the first row and the underline on the second row. The underline highlights the active tab's span.
2. The initial active tab is active_tab when given, otherwise the first tab.
3. Right and left keys cycle with wrap-around. Escape clears focus.
4. Digit keys activate by position. The 0 key follows the reference rule for fewer than ten tabs and for ten or more.
5. Letter search is case-insensitive, starts after the active tab, wraps, and is disabled when the flag is false.
6. A click inside an inactive tab's selection range activates that tab. A click outside every range does nothing.
7. A change of active tab animates the bar position.
8. With no tabs, only the full-width inactive underline is drawn, and no error is raised.
9. Inactive labels are dimmed by the configured opacity.
10. A Tab without a name uses its label as its name.

## Test requirements

- In tests/renderables/test_underline_bar.py, add a test that passes clickable ranges and checks that the rendered text carries click-action metadata on the given spans. This is the required new test.
- Existing underline tests must pass unchanged.
- New tests should use the existing render helper from the tests utilities.
- Tabs behavior tests are encouraged for the widget, following the repository's renderable and widget test pattern.
