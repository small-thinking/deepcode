# System design reference tabs QA

## Evidence

- **Source visual truth path:** current-turn `Browser Comment 1` attachment (the client did not provide a filesystem path), showing the 1099 × 988 dark-theme split Draft/Reference workspace.
- **Implementation screenshots:** `/private/tmp/deepcode-system-design-draft-tab-final.png`, `/private/tmp/deepcode-system-design-reference-tab-top-autosized.png`, and `/private/tmp/deepcode-system-design-reference-tab-bottom-autosized.png`.
- **Route:** `http://127.0.0.1:8848/#/problems/cover-photo-conversion-evaluation` in the Codex in-app browser.
- **Viewport and density:** 1099 × 988 CSS px at device pixel ratio 2. Browser captures were normalized to 1099 × 988 pixels, matching the annotated viewport size.
- **State:** dark theme; Draft tab, Reference tab at canvas top, and Reference tab at answer bottom.

## Comparison history

1. **Source finding — P1:** Draft Response and Reference Answer shared the right panel vertically, so neither received the full workspace and the large walkthrough appeared clipped.
2. **First implementation — P1:** Separate full-height tabs fixed the workspace competition, but the 760 px iframe still had its own 1151 px document and therefore retained a nested scrollbar.
3. **Fix:** Replaced the internal Draft/Reference splitter with accessible tabs, made Reference the only vertical scroll container, and added a source-validated `postMessage` height handshake so the iframe expands to the walkthrough's rendered canvas height.
4. **Post-fix evidence:** The iframe reports and renders at 1151 px, its document client height and scroll height both equal 1151 px, its body overflow is hidden, and the Reference panel scrolls 1421 px from the walkthrough header through the final Guardrails paragraph. No actionable P0/P1/P2 difference remains.

## Surface review

| Surface | Result | Evidence |
| --- | --- | --- |
| Fonts and typography | Pass | Existing DeepCode font families, weights, uppercase labels, and body line heights are unchanged; tab labels reuse the established tab component. |
| Spacing and layout rhythm | Pass | Each tab owns the complete right-panel content area; header, tab strip, and 16 px workspace padding retain the existing panel rhythm. |
| Colors and visual tokens | Pass | Tabs, borders, panels, focus states, and walkthrough continue to use the existing dark-theme tokens. |
| Image and asset fidelity | Pass | No source imagery was replaced or added; the existing interactive walkthrough is preserved without scaling or cropping. |
| Copy and content | Pass | The controls are now named `Draft response` and `Reference answer`; the neutral panel subtitle explains the draft-to-compare workflow. |
| Interaction and accessibility | Pass | Tabs expose `tablist`/`tab`/`tabpanel`, selected state, roving tabindex, ArrowLeft/ArrowRight/Home/End navigation, and draft persistence across switching. |
| Scrolling and responsiveness | Pass | Desktop Reference uses one visible vertical scrollbar; the iframe has no nested scroll. Mobile keeps natural document scrolling and full-height tab content. |

## Browser checks

- Switched both tabs with pointer input and ArrowRight keyboard input.
- Confirmed a draft survives a tab round trip, then restored the original empty draft state.
- Confirmed the walkthrough remains interactive and lazy-loads only after opening Reference.
- Measured Reference at 741 px viewport height and 2162 px total content height after auto-sizing.
- Scrolled the Reference panel from `scrollTop = 0` to its maximum and visually confirmed the final answer content.
- Checked browser console errors: none.

## Focused comparison

The full-view captures were sufficient for the left problem pane and overall two-column composition. Focused top and bottom Reference captures were also reviewed because the core requirement depends on the walkthrough boundary and the final answer remaining reachable within the same scroll container.

## Follow-up polish

- No P0/P1/P2 findings remain. A future P3 enhancement could remember the selected System Design tab per problem, but defaulting to Draft is safer for interview practice.

final result: passed
