from src.shared.schema import Prediction, DriftType
from src.evaluation.metrics import compute_metrics, compute_confusion_matrix


def test_compute_metrics_perfect():
    ground_truth = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.NO_DRIFT]
    predictions = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.NO_DRIFT]
    metrics = compute_metrics(ground_truth, predictions, DriftType.SYNTACTIC)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_compute_metrics_with_fp():
    ground_truth = [DriftType.NO_DRIFT, DriftType.NO_DRIFT, DriftType.SYNTACTIC]
    predictions = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.SYNTACTIC]
    metrics = compute_metrics(ground_truth, predictions, DriftType.SYNTACTIC)
    assert metrics["precision"] == 0.5  # 1 TP, 1 FP
    assert metrics["recall"] == 1.0      # 1 TP, 0 FN


def test_compute_confusion_matrix():
    ground_truth = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.NO_DRIFT]
    predictions = [DriftType.SYNTACTIC, DriftType.NO_DRIFT, DriftType.SEMANTIC]
    cm = compute_confusion_matrix(ground_truth, predictions)
    assert cm[DriftType.SYNTACTIC][DriftType.SYNTACTIC] == 1
    assert cm[DriftType.SEMANTIC][DriftType.NO_DRIFT] == 1