from collections import Counter


def recommend_friends(graph, user, k):
    friends = set(graph[user])
    if not friends or k == 0:
        return []
    counts = Counter()
    for friend in friends:
        for candidate in set(graph[friend]):
            if candidate != user and candidate not in friends:
                counts[candidate] += 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [(candidate, count, count / len(friends)) for candidate, count in ranked[:k]]
