import json
from pathlib import Path
from src.shared.schema import Entry, DriftDetails, DriftType


def entry_to_dict(entry: Entry) -> dict:
    d = {
        "entry_id": entry.entry_id,
        "source": entry.source,
        "origin_repo": entry.origin_repo,
        "origin_commit": entry.origin_commit,
        "origin_file": entry.origin_file,
        "origin_function": entry.origin_function,
        "code": entry.code,
        "docstring": entry.docstring,
        "full_source": entry.full_source,
        "drift_label": entry.drift_label.value if entry.drift_label else None,
        "drift_present": entry.drift_present,
        "drift_details": _drift_details_to_dict(entry.drift_details) if entry.drift_details else None,
        "ground_truth_annotation": entry.ground_truth_annotation,
    }
    return d


def dict_to_entry(d: dict) -> Entry:
    drift_label = DriftType(d["drift_label"]) if d.get("drift_label") else None
    drift_details = _dict_to_drift_details(d["drift_details"]) if d.get("drift_details") else None
    return Entry(
        entry_id=d["entry_id"],
        source=d["source"],
        origin_repo=d["origin_repo"],
        origin_commit=d.get("origin_commit"),
        origin_file=d["origin_file"],
        origin_function=d["origin_function"],
        code=d["code"],
        docstring=d["docstring"],
        full_source=d["full_source"],
        drift_label=drift_label,
        drift_present=d.get("drift_present"),
        drift_details=drift_details,
        ground_truth_annotation=d.get("ground_truth_annotation"),
    )


def _drift_details_to_dict(details: DriftDetails) -> dict:
    return {
        "type": details.type.value,
        "description": details.description,
        "severity": details.severity,
        "missing_params": details.missing_params,
        "extra_params_in_doc": details.extra_params_in_doc,
        "type_mismatches": details.type_mismatches,
        "behavioral_mismatches": details.behavioral_mismatches,
    }


def _dict_to_drift_details(d: dict) -> DriftDetails:
    return DriftDetails(
        type=DriftType(d["type"]),
        description=d["description"],
        severity=d.get("severity"),
        missing_params=d.get("missing_params", []),
        extra_params_in_doc=d.get("extra_params_in_doc", []),
        type_mismatches=d.get("type_mismatches", []),
        behavioral_mismatches=d.get("behavioral_mismatches", []),
    )


def save_entries(entries: list[Entry], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for entry in entries:
        d = entry_to_dict(entry)
        entry_path = output_dir / f"{entry.entry_id}.json"
        entry_path.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        manifest.append({"entry_id": entry.entry_id, "file": str(entry_path.relative_to(output_dir.parent))})
    manifest_path = output_dir.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))


def load_entries(data_dir: Path) -> list[Entry]:
    manifest_path = data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entries = []
    for item in manifest:
        entry_path = data_dir / "entries" / f"{item['entry_id']}.json"
        d = json.loads(entry_path.read_text())
        entries.append(dict_to_entry(d))
    return entries