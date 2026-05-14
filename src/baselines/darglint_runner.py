import subprocess
import re
from pathlib import Path
from src.shared.schema import Entry, Prediction, DriftType


def run_darglint(source_dir: Path) -> str:
    """Run darglint on all Python files in source_dir."""
    result = subprocess.run(
        ["darglint", "-v", "2", str(source_dir)],
        capture_output=True, text=True,
    )
    return result.stdout + result.stderr


def parse_darglint_output(output: str) -> list[dict]:
    """Parse darglint output into structured findings."""
    findings = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        match = re.match(r"(.+?):(\d+):(.+?):\s*(.+)", line)
        if match:
            error_msg = match.group(4)
            finding = {"file": match.group(1), "line": int(match.group(2)),
                        "function": match.group(3), "message": error_msg}
            if "missing parameter" in error_msg.lower():
                param_match = re.search(r"parameter:\s*(\w+)", error_msg)
                finding["error_type"] = "missing_param"
                finding["param"] = param_match.group(1) if param_match else ""
            elif "return" in error_msg.lower():
                finding["error_type"] = "return_type_mismatch"
            else:
                finding["error_type"] = "other_syntactic"
            findings.append(finding)
    return findings


def darglint_entries_to_predictions(
    entries: list[Entry],
    findings: list[dict],
) -> list[Prediction]:
    """Convert darglint findings to Predictions aligned with dataset entries."""
    file_findings = {}
    for f in findings:
        key = f["function"]
        file_findings[key] = file_findings.get(key, []) + [f]

    predictions = []
    for entry in entries:
        func_findings = file_findings.get(entry.origin_function, [])
        if func_findings:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="darglint",
                predicted_label=DriftType.SYNTACTIC,
                predicted_details={"findings": func_findings},
                raw_output=str(func_findings),
            ))
        else:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="darglint",
                predicted_label=DriftType.NO_DRIFT,
            ))
    return predictions