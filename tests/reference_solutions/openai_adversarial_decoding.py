def termination_distribution(n, p):
    probabilities = [0.0] * n
    surviving = 1.0
    for index in range(n):
        if index == n - 1:
            probabilities[index] = surviving
        else:
            probabilities[index] = surviving * p[index]
            surviving *= 1.0 - p[index]
    expected_time = sum((index + 1) * probability for index, probability in enumerate(probabilities))
    return probabilities, expected_time


def solve(n, p, decisions, adversaries):
    best_decision = None
    best_worst_reward = float("-inf")
    for decision in decisions:
        worst_reward = float("inf")
        for adversary in adversaries:
            probabilities = adversary["probabilities"]
            if probabilities is None:
                probabilities = p
            distribution, _expected_time = termination_distribution(n, probabilities)
            rewards = adversary["reward_table"][decision]
            expected_reward = sum(
                probability * reward
                for probability, reward in zip(distribution, rewards)
            )
            worst_reward = min(worst_reward, expected_reward)
        if worst_reward > best_worst_reward:
            best_decision = decision
            best_worst_reward = worst_reward
    return best_decision, best_worst_reward
