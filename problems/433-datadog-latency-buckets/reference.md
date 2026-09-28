# Evidence and reconstruction boundary

The public candidate report describes latency values, a bucket count, a bucket width, zero-based ranges, and a final overflow bucket. This practice API names those parameters `bucket_count` and `bucket_width` and returns a list of counts. Integer/nonnegative assertions and empty-input behavior are local practice conventions; no performance or additional validation requirements are inferred.
