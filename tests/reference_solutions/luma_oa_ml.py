import math


# 462 — centered grayscale crop
def center_crop(image, crop_h, crop_w):
    top = (len(image) - crop_h) // 2
    left = (len(image[0]) - crop_w) // 2
    return [row[left:left + crop_w] for row in image[top:top + crop_h]]


# 464 — numerically stable softmax
def softmax(logits):
    anchor = max(logits)
    weights = [math.exp(value - anchor) for value in logits]
    total = sum(weights)
    return [weight / total for weight in weights]


# 465 — normalized Gaussian kernel
def gaussian_kernel(k, sigma):
    radius = k // 2
    kernel = [
        [math.exp(-0.5 * ((row / sigma) * (row / sigma)
                          + (col / sigma) * (col / sigma)))
         for col in range(-radius, radius + 1)]
        for row in range(-radius, radius + 1)
    ]
    total = sum(sum(row) for row in kernel)
    return [[value / total for value in row] for row in kernel]


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
