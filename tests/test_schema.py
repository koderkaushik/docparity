from src.shared.schema import DriftType, DriftDetails, Entry, Prediction


def test_drift_type_values():
    assert DriftType.SYNTACTIC.value == "syntactic"
    assert DriftType.SEMANTIC.value == "semantic"
    assert DriftType.NO_DRIFT.value == "no-drift"


def test_entry_creation():
    entry = Entry(
        entry_id="entry_001",
        source="synthetic",
        origin_repo="flask",
        origin_file="flask/app.py",
        origin_function="run",
        code="def run(self): ...",
        docstring="Runs the app.",
        full_source='def run(self):\n    """Runs the app."""\n    ...',
    )
    assert entry.entry_id == "entry_001"
    assert entry.drift_label is None
    assert entry.drift_present is None


def test_prediction_creation():
    pred = Prediction(
        entry_id="entry_001",
        approach="darglint",
        predicted_label=DriftType.SYNTACTIC,
    )
    assert pred.approach == "darglint"
    assert pred.predicted_label == DriftType.SYNTACTIC


def test_drift_details_defaults():
    details = DriftDetails(
        type=DriftType.SYNTACTIC,
        description="param missing",
    )
    assert details.missing_params == []
    assert details.severity is None