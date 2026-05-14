import csv
from pathlib import Path
from src.shared.schema import DriftType, Prediction, Entry
from src.evaluation.metrics import compute_all_metrics


def generate_comparison_table(
    entries: list[Entry],
    all_predictions: dict[str, list[Prediction]],
) -> list[dict]:
    """Generate the comparison table from the strategy doc."""
    ground_truth = [e.drift_label for e in entries]
    table = []
    for approach_name, predictions in all_predictions.items():
        metrics = compute_all_metrics(ground_truth, predictions)
        row = {"approach": approach_name}
        for drift_type in DriftType:
            m = metrics[drift_type.value]
            row[f"{drift_type.value}_precision"] = m["precision"]
            row[f"{drift_type.value}_recall"] = m["recall"]
            row[f"{drift_type.value}_f1"] = m["f1"]
        table.append(row)
    return table


def generate_error_analysis(
    entries: list[Entry],
    predictions: list[Prediction],
    approach_name: str,
) -> dict:
    """Analyze false positives, false negatives, and misclassifications."""
    false_positives = []
    false_negatives = []
    misclassifications = []

    for entry, pred in zip(entries, predictions):
        if pred.predicted_label != entry.drift_label:
            if entry.drift_label == DriftType.NO_DRIFT:
                false_positives.append({
                    "entry_id": entry.entry_id,
                    "predicted": pred.predicted_label.value,
                    "details": pred.predicted_details,
                })
            elif pred.predicted_label == DriftType.NO_DRIFT:
                false_negatives.append({
                    "entry_id": entry.entry_id,
                    "actual": entry.drift_label.value,
                    "details": pred.predicted_details,
                })
            else:
                misclassifications.append({
                    "entry_id": entry.entry_id,
                    "actual": entry.drift_label.value,
                    "predicted": pred.predicted_label.value,
                })

    return {
        "approach": approach_name,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "misclassifications": misclassifications,
        "fp_count": len(false_positives),
        "fn_count": len(false_negatives),
        "misclassify_count": len(misclassifications),
    }


def save_results_csv(table: list[dict], output_path: Path) -> None:
    """Save comparison table as CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if table:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=table[0].keys())
            writer.writeheader()
            writer.writerows(table)