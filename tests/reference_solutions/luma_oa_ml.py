import math


# 464 — numerically stable softmax
def softmax(logits):
    anchor = max(logits)
    weights = [math.exp(value - anchor) for value in logits]
    total = sum(weights)
    return [weight / total for weight in weights]


# 468 — zero imputation and population standardization
def impute_and_standardize(matrix):
    rows = len(matrix)
    cols = len(matrix[0])
    result = [[float(value) for value in row] for row in matrix]
    for col in range(cols):
        observed = [result[row][col] for row in range(rows) if result[row][col] != 0]
        fill = sum(observed) / len(observed)
        values = [result[row][col] or fill for row in range(rows)]
        mean = sum(values) / rows
        variance = sum((value - mean) ** 2 for value in values) / rows
        scale = math.sqrt(variance)
        for row, value in enumerate(values):
            result[row][col] = (value - mean) / scale
    return result
