from collections import Counter


class Solution:
    def getHint(self, secret: str, guess: str) -> str:
        bulls = 0
        secret_counts = Counter()
        guess_counts = Counter()
        for actual, proposed in zip(secret, guess):
            if actual == proposed:
                bulls += 1
            else:
                secret_counts[actual] += 1
                guess_counts[proposed] += 1
        cows = sum(min(count, guess_counts[digit]) for digit, count in secret_counts.items())
        return f"{bulls}A{cows}B"
