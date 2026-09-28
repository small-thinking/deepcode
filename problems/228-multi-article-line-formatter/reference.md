# Source and practice boundaries

The report requires a maximum content width, whole words, no punctuation at the start of a line, and separators between articles. The executable exercise normalizes whitespace and groups punctuation-leading tokens with the preceding word before greedy wrapping. Moving a whole group preserves both width and punctuation constraints.

Rejecting a word or group that cannot fit, the exact punctuation set, and empty-article behavior are explicit practice choices. The source also mentions trying to avoid single-word lines; that soft preference is a discussion follow-up, not an additional scored reflow rule. The report is for a software-engineering interview and is not evidence of an MLE-specific contract.

The Background links include the original report and canonical source notes.
