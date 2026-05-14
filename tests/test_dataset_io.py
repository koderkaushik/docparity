import json
import tempfile
from pathlib import Path
from src.shared.schema import DriftType, DriftDetails, Entry
from src.shared.dataset_io import save_entries, load_entries, entry_to_dict, dict_to_entry


def _sample_entry(entry_id="entry_001", drift_label=None, drift_details=None):
    return Entry(
        entry_id=entry_id,
        source="synthetic",
        origin_repo="flask",
        origin_file="flask/app.py",
        origin_function="run",
        code="def run(self): ...",
        docstring="Runs the app.",
        full_source='def run(self):\n    """Runs the app."""\n    ...',
        drift_label=drift_label,
        drift_details=drift_details,
    )


def test_entry_round_trip():
    entry = _sample_entry()
    d = entry_to_dict(entry)
    restored = dict_to_entry(d)
    assert restored.entry_id == entry.entry_id
    assert restored.code == entry.code


def test_entry_with_drift_round_trip():
    details = DriftDetails(type=DriftType.SYNTACTIC, description="missing param", missing_params=["z"])
    entry = _sample_entry(drift_label=DriftType.SYNTACTIC, drift_details=details)
    d = entry_to_dict(entry)
    restored = dict_to_entry(d)
    assert restored.drift_label == DriftType.SYNTACTIC
    assert restored.drift_details.missing_params == ["z"]


def test_save_and_load_entries():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        entries_dir = data_dir / "entries"
        entries = [
            _sample_entry("entry_001"),
            _sample_entry("entry_002"),
        ]
        save_entries(entries, entries_dir)
        assert (data_dir / "manifest.json").exists()
        assert (entries_dir / "entry_001.json").exists()
        assert (entries_dir / "entry_002.json").exists()