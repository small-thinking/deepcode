# Evidence and reconstruction boundary

The full-loop report specifies a bounded in-memory wrapper, `write` and `flush`, automatic flush at capacity, and explicit flush on demand. This practice API uses `bytes` and a sink whose `write` consumes the full argument synchronously; the Python types and success semantics are local conventions. The source describes a partial-write/circular-buffer follow-up, but the candidate did not fully implement it, so it is intentionally excluded from the required contract and tests.
