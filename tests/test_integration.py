"""End-to-end integration test using synthetic data through the full pipeline."""
import tempfile
from pathlib import Path
from src.shared.schema import Entry, DriftType, DriftDetails
from src.shared.dataset_io import save_entries, load_entries
from src.baselines.ast_checker import check_entry
from src.evaluation.metrics import compute_metrics


def _make_test_entries():
    entries = []
    # No-drift entry
    entries.append(Entry(
        entry_id="synth_001", source="synthetic", origin_repo="test",
        origin_file="test.py", origin_function="add",
        code="    return x + y",
        docstring="Add two numbers.\n\nArgs:\n    x: First.\n    y: Second.\n\nReturns:\n    int: The sum.",
        full_source='def add(x: int, y: int) -> int:\n    """Add two numbers.\n\n    Args:\n        x: First.\n        y: Second.\n\n    Returns:\n        int: The sum."""\n    return x + y',
        drift_label=DriftType.NO_DRIFT, drift_present=False,
    ))
    # Syntactic drift entry (missing param in docstring)
    entries.append(Entry(
        entry_id="synth_002", source="synthetic", origin_repo="test",
        origin_file="test.py", origin_function="compute",
        code="    if y == 0:\n        raise ValueError\n    return x // y",
        docstring="Compute something.\n\nArgs:\n    x: First.",
        full_source='def compute(x: int, y: int) -> int:\n    """Compute something.\n\n    Args:\n        x: First."""\n    if y == 0:\n        raise ValueError\n    return x // y',
        drift_label=DriftType.SYNTACTIC, drift_present=True,
        drift_details=DriftDetails(type=DriftType.SYNTACTIC, description="missing param y",
                                   missing_params=["y"]),
    ))
    return entries


def test_save_load_roundtrip():
    entries = _make_test_entries()
    with tempfile.TemporaryDirectory() as tmpdir:
        entries_dir = Path(tmpdir) / "entries"
        save_entries(entries, entries_dir)
        loaded = load_entries(Path(tmpdir))
        assert len(loaded) == 2
        assert loaded[0].entry_id == "synth_001"
        assert loaded[1].drift_label == DriftType.SYNTACTIC


def test_ast_checker_on_entries():
    entries = _make_test_entries()
    # Entry with no drift should be classified as no-drift
    pred = check_entry(entries[0])
    assert pred.predicted_label == DriftType.NO_DRIFT
    # Entry with missing param should be classified as syntactic
    pred = check_entry(entries[1])
    assert pred.predicted_label == DriftType.SYNTACTIC


def test_metrics_on_predictions():
    ground_truth = [DriftType.NO_DRIFT, DriftType.SYNTACTIC]
    predictions = [
        Entry(entry_id="synth_001", source="synthetic", origin_repo="test",
              origin_file="test.py", origin_function="add",
              code="", docstring="", full_source="",
              drift_label=DriftType.NO_DRIFT, drift_present=False),
        Entry(entry_id="synth_002", source="synthetic", origin_repo="test",
              origin_file="test.py", origin_function="compute",
              code="", docstring="", full_source="",
              drift_label=DriftType.SYNTACTIC, drift_present=True),
    ]
    from src.shared.schema import Prediction
    preds = [
        Prediction(entry_id="synth_001", approach="ast_checker", predicted_label=DriftType.NO_DRIFT),
        Prediction(entry_id="synth_002", approach="ast_checker", predicted_label=DriftType.SYNTACTIC),
    ]
    pred_labels = [p.predicted_label for p in preds]
    gt_labels = [e.drift_label for e in predictions]
    metrics = compute_metrics(gt_labels, pred_labels, DriftType.SYNTACTIC)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0