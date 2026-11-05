"""Scoring helpers shared by the tests and the model comparison, so both measure the same way."""


def cer(expected, actual):
    """Character error rate: edit distance / length of the expected text."""
    row = list(range(len(actual) + 1))
    for i, a in enumerate(expected, 1):
        prev, row[0] = row[0], i
        for j, b in enumerate(actual, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (a != b))
    return row[-1] / len(expected)
