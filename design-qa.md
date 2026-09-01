# Progress dashboard design QA

## Evidence

- **Visual source:** `/var/folders/yq/4yfpd24912b9wb8m2b5b67v80000gq/T/TemporaryItems/NSIRD_screencaptureui_bRyzkE/Screenshot 2026-08-31 at 9.24.09 PM.png`
- **Implementation capture:** the local `#/progress` screen in the Codex in-app browser at `http://127.0.0.1:8866/#/progress` (temporary isolated user/activity state).
- **Comparison viewport and state:** 765 × 228 CSS px, light theme, all company/category filters, two recorded evaluator runs. The source and implementation captures were rendered together in the same comparison input.

## Comparison history

1. **Initial comparison — P2:** The contribution title and explanatory copy lived inside the bordered card, producing a visibly taller panel than the GitHub reference. The graph also had avoidable right-edge scrolling at the reference viewport.
2. **Fix:** Moved the contribution total above the bordered graph, removed the redundant in-card copy, and tightened the graph container's horizontal padding while retaining the 53-week calendar, weekday labels, and `Less`/`More` legend.
3. **Post-fix comparison:** The contribution total now sits above a compact white, 1 px bordered grid. Its month labels, low-contrast empty squares, green activity scale, weekday labels, and footer legend align with the supplied reference's hierarchy and density. No actionable P0/P1/P2 visual mismatch remains.

## Surface review

| Surface | Result | Evidence |
| --- | --- | --- |
| Visual fidelity | Pass | GitHub-like white contribution card, restrained neutral borders, five green intensity levels, and compact calendar geometry. |
| Layout and responsive behavior | Pass | Verified at the supplied 765 × 228 viewport; the 53-week graph remains legible with the final date column available in horizontal overflow when needed. |
| Interaction and state | Pass | `Systems Coding` opens the Problems page with that category selected; `Anthropic` opens `#/companies/anthropic`. |
| Content hierarchy | Pass | Range/filter context remains above the metrics; the contribution total is immediately followed by its calendar; breakdown links use clear category/company labels. |
| Accessibility and clarity | Pass | Contribution cells expose date/count labels, the graph has an accessible name, and navigation buttons carry destination-specific labels. |

## Browser checks

- Confirmed the temporary dashboard shows 2 submissions, 1 unique question, and 1 question in progress after a full and a selected evaluator run.
- Confirmed category and company navigation using the rendered controls.
- Checked browser console errors after navigation: none.

## Follow-up polish

- P3: When an unusually narrow viewport has less room than the 53-week calendar, the graph intentionally preserves square size and offers horizontal scrolling rather than compressing cells below their readable size.

final result: passed
