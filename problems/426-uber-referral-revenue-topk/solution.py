def solution(operations):
    parent = {}
    aggregate = {}
    answers = []

    for operation in operations:
        if operation[0] == 'insert':
            _, customer, amount, referrer = operation
            if customer not in parent:
                assert referrer is None or referrer in parent
                parent[customer] = referrer
                aggregate[customer] = 0
            node = customer
            while node is not None:
                aggregate[node] += amount
                node = parent[node]
        else:
            _, k, threshold = operation
            assert k >= 0
            ranked = sorted(
                ((customer, total) for customer, total in aggregate.items()
                 if total > threshold),
                key=lambda item: (-item[1], item[0]),
            )
            answers.append([[customer, total] for customer, total in ranked[:k]])
    return answers
