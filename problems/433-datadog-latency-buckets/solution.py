def calc_buckets(latencies, bucket_count, bucket_width):
    assert type(bucket_count) is int and bucket_count > 0
    assert type(bucket_width) is int and bucket_width > 0
    assert all(type(value) is int and value >= 0 for value in latencies)

    counts = [0] * bucket_count
    for value in latencies:
        index = min(value // bucket_width, bucket_count - 1)
        counts[index] += 1
    return counts
