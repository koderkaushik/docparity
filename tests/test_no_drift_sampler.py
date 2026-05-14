from src.mining.no_drift_sampler import sample_no_drift_functions
from src.mining.function_extractor import FunctionInfo
from src.shared.schema import DriftType


def test_sample_no_drift_returns_empty_for_no_functions():
    entries = sample_no_drift_functions([], max_samples=5, repo_name="flask")
    assert isinstance(entries, list)
    assert len(entries) == 0


def test_sample_no_drift_filters_inconsistent():
    consistent = FunctionInfo(
        name="add", code="return x + y",
        docstring="Add x and y.\n\nArgs:\n    x: First.\n    y: Second.\n\nReturns:\n    int: Sum.",
        full_source='def add(x, y):\n    """Add x and y."""\n    return x + y',
        start_line=1, end_line=3, args=["x", "y"], return_annotation="int",
    )
    entries = sample_no_drift_functions([consistent], max_samples=5, repo_name="flask")
    assert len(entries) == 1
    assert entries[0].drift_label == DriftType.NO_DRIFT
    assert entries[0].drift_present is False