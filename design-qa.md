# Interactive demo schema and theme bridge QA

## Evidence

- **Source visual truth path:** current-turn `Browser Comment 1` attachment (the client did not provide a filesystem path), showing the 1099 × 988 dark-theme System Design workspace.
- **Implementation evidence:** current-turn Codex in-app browser captures in Dark mode plus computed-style reads in both Dark and Light modes.
- **Route:** `http://127.0.0.1:8848/#/problems/cover-photo-conversion-evaluation` in the Codex in-app browser.
- **State:** Reference tab with a schema-v1 `sync` / `content` demo; original Dark mode restored after checking both themes.

## Comparison history

1. **Source finding — P1:** The visualization architecture needed a reusable contract instead of per-question assumptions, especially for theme ownership and large-canvas sizing.
2. **Contract:** Added a strict v1 schema with a stable demo ID, local standalone resource, `sync | light | dark` theme policy, pale `fallback_theme`, and `content | fixed` height policy.
3. **Theme bridge:** A sandbox-safe `postMessage` handshake sends the active theme plus resolved semantic DeepCode color tokens. The iframe accepts the message only from `window.parent` and retains a self-contained light default.
4. **Sizing bridge:** Only a schema-declared `content` demo can update its iframe height. The parent still source-matches the iframe and clamps the request before applying it.
5. **Post-fix evidence:** Dark and Light mode both produced exact host/demo background and surface token matches. The content iframe expanded from its 760 px fallback to 1151 px while the 741 px Reference viewport retained one outer scroll over 2162 px of content.

## Surface review

| Surface | Result | Evidence |
| --- | --- | --- |
| Fonts and typography | Pass | Existing DeepCode font families, weights, uppercase labels, and body line heights are unchanged. |
| Spacing and layout rhythm | Pass | The demo remains a full-width canvas inside Reference and keeps the established panel rhythm. |
| Colors and visual tokens | Pass | Dark host/demo matched `#17191f` background and `#20232b` surface; Light matched `#eef1f5` and `#f7f8fb`. Accent, text, border, status, and soft colors use the same semantic token payload. |
| Image and asset fidelity | Pass | No source imagery was replaced or added; the existing interactive walkthrough is preserved without scaling or cropping. |
| Copy and content | Pass | This change does not alter the question's teaching sequence or reference answer; it only makes the existing walkthrough the first schema consumer. |
| Interaction and accessibility | Pass | The existing controls remain available inside the titled sandbox; theme changes do not reset walkthrough state. |
| Scrolling and responsiveness | Pass | Desktop Reference uses one vertical scrollbar; the iframe grows to its reported canvas height and has no nested scroll. |
| Fallback behavior | Pass | The demo's inline palette starts in the schema-declared pale Light style if no parent theme message arrives. |

## Browser checks

- Reloaded in Draft and confirmed the iframe had schema data but no `src`; opening Reference lazy-loaded it.
- Confirmed `data-demo-theme=sync`, `fallbackTheme=light`, and `heightMode=content` reached the rendered iframe.
- Measured Reference at 741 px viewport height and 2162 px total content height; the iframe expanded to 1151 px.
- In Dark mode, host and iframe both resolved background `#17191f` and surface `#20232b`.
- In Light mode, host and iframe both resolved background `#eef1f5` and surface `#f7f8fb`.
- Restored Dark mode and `scrollTop = 0` after verification.
- Checked browser console errors: none.

## Focused comparison

The full-view Dark capture was reviewed for the overall two-column composition and the walkthrough header/canvas boundary. Computed styles were used for the theme check because they verify exact token equality more reliably than visual comparison alone.

## Follow-up polish

- No P0/P1/P2 findings remain. The next design iteration can change this question's teaching content without changing the host integration contract.

final result: passed
