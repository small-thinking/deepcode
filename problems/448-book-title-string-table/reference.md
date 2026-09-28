# Evidence and reconstruction boundary

The September 19, 2026 report (1190112) mentions formatting book titles into a string table, without an executable specification. The May 11 report (1176406) describes a width-55 table with each sentence on one padded, bordered line; overlong-input behavior is left for clarification. The April 16 report (1173286) describes an article and width with vertical borders and a multi-column follow-up. The August 19 report (1186786) describes boxed sentences, fixed-width wrapping, and mixed widths within one box.

This exercise combines the title framing with a one-line base and an optional wrapping follow-up. Content-width interpretation, `+`/`-` horizontal borders between title blocks, empty-title behavior, normalization during wrapping, and rejection rather than truncation or word splitting are explicit practice choices, not a verbatim interview contract. Multi-column and mixed-width layouts remain discussion follow-ups because the reports do not establish their exact rendering rules. PracHub's matching interview account appears to describe the same event as 1190112; no independently established occurrence is counted.

The border-free multi-article formatter is a separate variant with different punctuation and separator rules. Its contract remains separate. See the original reports and canonical source ledger linked in the problem's Background.

# Reference approach

Construct each title's rows, right-pad them, and append one border after its block. For wrapping, keep one current row and flush it when the next whole word would exceed the width. Empty titles still contribute a row. The implementation is in `solution.py`, avoiding a second copy of the reference code. Runtime is linear in input and emitted output size; auxiliary space besides the output is proportional to one title's rows.
