from src.baselines.ast_checker import check_entry
from src.shared.schema import Entry, DriftType


def test_check_entry_missing_param():
    entry = Entry(
        entry_id="test_001",
        source="synthetic",
        origin_repo="test",
        origin_file="test.py",
        origin_function="add",
        code="    return x + y",
        docstring="Add numbers.\n\nArgs:\n    x: First.",
        full_source='def add(x, y):\n    """Add numbers.\n\n    Args:\n        x: First."""\n    return x + y',
        drift_label=DriftType.SYNTACTIC,
        drift_present=True,
    )
    result = check_entry(entry)
    assert result.predicted_label == DriftType.SYNTACTIC


def test_check_entry_no_drift():
    entry = Entry(
        entry_id="test_002",
        source="synthetic",
        origin_repo="test",
        origin_file="test.py",
        origin_function="add",
        code="    return x + y",
        docstring="Add numbers.\n\nArgs:\n    x: First.\n    y: Second.",
        full_source='def add(x, y):\n    """Add numbers.\n\n    Args:\n        x: First.\n        y: Second."""\n    return x + y',
        drift_label=DriftType.NO_DRIFT,
        drift_present=False,
    )
    result = check_entry(entry)
    assert result.predicted_label == DriftType.NO_DRIFT