"""Scoring helpers shared by the tests and the experiments, so all of them measure the same way."""
from collections import Counter


def cer(expected, actual):
    """Character error rate: edit distance / length of the expected text."""
    row = list(range(len(actual) + 1))
    for i, a in enumerate(expected, 1):
        prev, row[0] = row[0], i
        for j, b in enumerate(actual, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (a != b))
    return row[-1] / len(expected)


def chrf(hypotheses, references, order=6, beta=2):
    """Translation quality, 0 to 100: character n-gram F-score over the whole set, spaces ignored (sacreBLEU's default chrF)."""
    stats = [[0, 0, 0] for _ in range(order)]  # per n-gram size: hypothesis count, reference count, matches
    for hyp, ref in zip(hypotheses, references):
        hyp, ref = "".join(hyp.split()), "".join(ref.split())
        for n in range(1, order + 1):
            h = Counter(hyp[i:i + n] for i in range(len(hyp) - n + 1))
            r = Counter(ref[i:i + n] for i in range(len(ref) - n + 1))
            stats[n - 1][0] += sum(h.values())
            stats[n - 1][1] += sum(r.values())
            stats[n - 1][2] += sum((h & r).values())
    scores = []
    for hyp_n, ref_n, match in stats:
        if hyp_n and ref_n:
            p, r = match / hyp_n, match / ref_n
            scores.append((1 + beta ** 2) * p * r / (beta ** 2 * p + r) if p + r else 0.0)
    return 100 * sum(scores) / len(scores) if scores else 0.0
