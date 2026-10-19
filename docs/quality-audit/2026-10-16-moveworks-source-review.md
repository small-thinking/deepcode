# Moveworks source reconciliation — 2026-10-16

The collection contains five exercises grounded in MLE / ML infrastructure reports and seven explicitly labeled SWE or role-ambiguous supplements. The Notion source review retains the original links, event lineage, access boundaries, and deferred questions: https://app.notion.com/p/3fb6ce51456d81de9704cd26fbf8c15f

| Exercise | Evidence and reconstruction boundary |
| --- | --- |
| hangman-next-letter | MLE report gives word-presence, total-occurrence and alphabetical ranking. All-occurrences-revealed behavior and empty return are explicit practice conventions. |
| shortest-unique-substring-highlighting | The 2022 report links the shortest, case-insensitive task; the 2025 report adds brackets without stating shortest. A later public SWE report supports first-position ties but uses underline tags. |
| iphone-app-recommendation | Original gives only the recommendation scenario. Data, modeling, deployment and evaluation in the reference are preparation guidance. |
| llm-provider-routing-layer | Original specifies internal services, a shared layer and providers. Routing policy and failure semantics are design choices. |
| failed-project-expectations | Related behavioral questions from one interview are consolidated. The answer is a framework rather than an invented personal story. |
| string-distinctiveness-scoring | The complete concentration / average multiset Jaccard contract is SWE evidence. Group-wise exclusion and output order for tied winners are practice conventions. |
| citation-range-merging | Two SWE screens support bracket parsing and merging, including a no-regex requirement. Valid positive bounds and overlap-only merging are explicit local choices. |
| synonym-query-rewrites | SWE reports support word/phrase alternatives and overlapping spans. Case sensitivity, spacing and direct-group rather than transitive closure are declared practice choices. |
| text-justification | One source says MLE in the title and SWE in its role field; independent SWE reports identify the standard LC68 task. Word-splitting follow-ups lack a complete contract. |
| restaurant-review-keyword-search | SWE reports support conjunctive review search. Detailed reports specify corpus scale; read-only and vocabulary assumptions belong to a particular public version. |
| document-scoped-assistant-product | The SWE screenshot covers user configuration, document access, architecture and production. RAG and answer-grounding details are a proposed design, not mandated source constraints. |
| word-break-sentences | Public SWE reports support all dictionary segmentations. Sorting is local; an optional spaces-in-text/glossary extension remains outside the base contract. |

## Consolidation decisions

Existing RAG/component exercises were compared with the document-assistant task; the latter focuses on configuration and product lifecycle. Sentence enumeration is distinct from the existing word ladder and grid word-search tasks. Follow-ups that share one API stay within their canonical exercise.

The incomplete MLE common-letter scoring prompt remains Notion-only. A 2026 SWE report gives three stages but does not define its similarity callback, aggregation or character-exclusion scope. A 2023 report mentions set Jaccard, while the complete SWE variant uses multiset Jaccard. These do not establish the exact MLE formula or later parts, so no fixed MLE tests were fabricated.

All finite company-index reports were body-attempted, with a deleted-body limitation. Bounded forum searches and public candidate reports supplied additional corroboration, including visually checked screenshots. Unrelated frontend, billing, car-rental and role-uncertain campus leads remain research leads. Generic preparation pages and generated site summaries are not independent candidate evidence.

## Validation

Seven executable exercises have 44 visible cases. Reference solutions pass evaluator and browser checks; written reference-answer tabs, original links, signal tiers and the company hub were checked. Text-justification snippets assert exact spacing because stdout normalization could otherwise hide spacing errors; a wrong-padding solution is rejected.

Browser execution uses separate QA state. Validation submissions are not user practice, and the delivered collection starts without test-generated completion records. The change is additive to the current main branch and does not restore Fireworks exercises intentionally removed there. No application code or dependencies changed.


## Coding-only coverage repair — 2026-10-19

A targeted reread of 873861 (both reply pages), 776845 (all replies), 1131055, and 1123889 distinguishes a read receipt from exercise coverage. The existing Hangman and unique-substring contracts remain covered. The MLE string-scoring report remains source-incomplete; its separate SWE Jaccard exercise does not fill the missing original formula.

- Added `basic-calculator-ii`: the LC 227 task explicitly named by numeric homophone in the original Senior Backend report at https://www.1point3acres.com/interview/thread/776845 .
- Added `basic-calculator-iii`: the same report names LC 772. A separate first-person November reply adds decimals and error handling. The exercise keeps integer evaluation and a decimal/error follow-up separate, and labels the latter's grammar, real division, exception API and bounds as local reconstruction choices. The 2022 bolo reply also names 772, but its cross-post event/role relationship is unresolved.
- Added 776845 to the existing `word-break-sentences` references. Its LC 140 mention is an independent historical SWE source; it creates no duplicate exercise.
- The new calculator pages are SWE supplements; the generic calculator/recommendation wording in 873861 does not establish an exact MLE calculator contract.
- The calculator fixtures exercise precedence, associativity, nested parentheses, unary signs, integer truncation, decimals and malformed input. Wrong floor division, integer-mode real division and silently swallowed parse errors must fail. QA uses separate practice state.

This repair is coding-only; billing, text-search and other design leads remain outside its scope.
