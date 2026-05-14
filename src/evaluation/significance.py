import numpy as np
from scipy import stats
from src.shared.schema import DriftType


def mcnemar_test(pred1: list[DriftType], pred2: list[DriftType],
                 ground_truth: list[DriftType]) -> dict:
    """McNemar's test for comparing two classifiers."""
    n01 = 0  # pred1 wrong, pred2 correct
    n10 = 0  # pred1 correct, pred2 wrong
    for p1, p2, gt in zip(pred1, pred2, ground_truth):
        correct1 = (p1 == gt)
        correct2 = (p2 == gt)
        if not correct1 and correct2:
            n01 += 1
        elif correct1 and not correct2:
            n10 += 1

    b = n01 + n10
    if b == 0:
        return {"statistic": 0, "p_value": 1.0, "significant": False}

    statistic = (abs(n01 - n10) - 1) ** 2 / b if b > 0 else 0
    p_value = 1 - stats.chi2.cdf(statistic, df=1)
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "n01": n01,
        "n10": n10,
    }


def bootstrap_ci(
    ground_truth: list[DriftType],
    predictions: list[DriftType],
    target_class: DriftType,
    n_samples: int = 10000,
    alpha: float = 0.05,
) -> dict:
    """Bootstrap confidence interval for F1 score."""
    from src.evaluation.metrics import compute_metrics
    f1_scores = []
    n = len(ground_truth)
    for _ in range(n_samples):
        indices = np.random.choice(n, size=n, replace=True)
        gt_sample = [ground_truth[i] for i in indices]
        pred_sample = [predictions[i] for i in indices]
        m = compute_metrics(gt_sample, pred_sample, target_class)
        f1_scores.append(m["f1"])

    lower = float(np.percentile(f1_scores, 100 * alpha / 2))
    upper = float(np.percentile(f1_scores, 100 * (1 - alpha / 2)))
    return {"f1_mean": float(np.mean(f1_scores)), "ci_lower": lower, "ci_upper": upper}