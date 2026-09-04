# System Design compact workspace and problem focus QA

## Evidence

- **Source visual truth:** current-turn `Browser Comment 1` screenshot at 1099 × 988 and `Browser Comment 2` screenshot at 1374 × 988. The client did not expose filesystem paths for either annotated source image.
- **Implementation screenshots:** current-turn Codex in-app browser captures of the split Reference state and full-width Problem state. The browser API returned the captures inline without filesystem paths.
- **Route:** `http://127.0.0.1:8848/#/problems/cover-photo-conversion-evaluation`.
- **Normalized comparison:** the primary source and implementation captures are both 1099 × 988 pixels for a 1099 × 988 CSS viewport; no density rescaling was needed. The wider source was used only to confirm the intended full-width behavior.
- **State:** Light theme; Reference selected for the compact split view; Problem pane expanded for the focus view; split view restored after verification.

## Findings

- No actionable P0, P1, or P2 findings remain.
- The removed title/subtitle layer was redundant with the Draft and Reference tabs. Moving Reset to the same toolbar preserves the action without reintroducing the extra vertical region.
- `Full width` is a text action that reuses the existing button style, so no approximate icon or new visual language was introduced.

## Comparison history

1. **Source finding — P1:** `Your design` and its explanatory subtitle consumed a full header row without adding navigation or task context.
2. **Source finding — P1:** the draggable divider could resize the two panes but could not give the Problem pane the entire workspace in one action.
3. **Fix:** removed the redundant right header, moved Reset beside the tabs but outside the semantic tablist, and added a reversible `Full width` / `Split view` control to the Problem header.
4. **Post-fix evidence:** the right panel now has only a 51 px tab row plus its workspace; Reference client height increased to 797 px. In focus mode the Problem pane and layout both measured 1055 px, while the right panel and divider computed to `display: none`.
5. **Restoration evidence:** returning to split view restored the divider and right panel and preserved the selected Reference tab.

## Required fidelity surfaces

| Surface | Result | Evidence |
| --- | --- | --- |
| Fonts and typography | Pass | Existing font family, weights, sizes, truncation, and tab typography are unchanged. The new labels use existing button typography. |
| Spacing and layout rhythm | Pass | Removing one 54 px header layer increases useful right-panel height without changing outer gutters, radii, or panel spacing. Problem header actions remain on one 34 px row at 1099 px. |
| Colors and visual tokens | Pass | Both controls reuse existing panel, line, text, blue, hover, and pressed-state tokens in Light and Dark compatible styles. |
| Image quality and asset fidelity | Pass | No image, illustration, logo, or icon asset was added, removed, scaled, or substituted. |
| Copy and content | Pass | Only the redundant `Your design` title/subtitle were removed. Question content, Draft/Reference labels, walkthrough copy, and reference answer are unchanged. |
| Interaction and accessibility | Pass | Full-width mode exposes `aria-pressed` and a state-specific label, retains its restore control, and preserves the prior split ratio. Reset remains outside the two-item semantic tablist. |
| Responsiveness | Pass | The focus control is hidden below the existing 920 px stacked-layout breakpoint, where both panes are already full width; the editor remains visible in that mobile layout. |

## Browser checks

- Opened Draft and Reference after a fresh reload.
- Confirmed the removed header is absent and Reset remains available only in Draft.
- Confirmed the semantic tablist contains exactly the two navigation tabs, not Reset.
- Entered full-width mode and verified left width equals layout width, with both right panel and divider hidden.
- Restored split mode and confirmed Reference selection persisted.
- Checked browser console errors: none.

## Focused comparison

The top of the right panel and the left header controls were inspected as focused regions because those are the two annotated targets. The full-view captures were used to verify workspace proportions and the expanded Problem reading state.

## Follow-up polish

- No P3 follow-up is required for this scoped change.

final result: passed
