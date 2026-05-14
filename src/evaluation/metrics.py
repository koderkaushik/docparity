from collections import defaultdict
from src.shared.schema import DriftType, Prediction


def compute_confusion_matrix(
    ground_truth: list[DriftType],
    predictions: list[DriftType],
) -> dict[DriftType, dict[DriftType, int]]:
    """Build a confusion matrix: cm[true_label][predicted_label] = count."""
    cm = defaultdict(lambda: defaultdict(int))
    for true, pred in zip(ground_truth, predictions):
        cm[true][pred] += 1
    return dict(cm)


def compute_metrics(
    ground_truth: list[DriftType],
    predictions: list[DriftType],
    target_class: DriftType,
) -> dict[str, float]:
    """Compute precision, recall, F1 for a specific drift type (one-vs-rest)."""
    tp = sum(1 for t, p in zip(ground_truth, predictions) if t == target_class and p == target_class)
    fp = sum(1 for t, p in zip(ground_truth, predictions) if t != target_class and p == target_class)
    fn = sum(1 for t, p in zip(ground_truth, predictions) if t == target_class and p != target_class)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def compute_all_metrics(
    ground_truth: list[DriftType],
    predictions: list[Prediction],
) -> dict[str, dict[str, float]]:
    """Compute metrics for each drift type."""
    pred_labels = [p.predicted_label for p in predictions]
    results = {}
    for drift_type in DriftType:
        results[drift_type.value] = compute_metrics(ground_truth, pred_labels, drift_type)
    return results