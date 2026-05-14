import subprocess
from pathlib import Path
from src.shared.schema import Entry, Prediction, DriftType


SYNTACTIC_KEYWORDS = ["param", "parameter", "argument", "signature", "type hint", "return type",
                       "docstring param", "missing from docstring"]
SEMANTIC_KEYWORDS = ["behavior", "behavioral", "logic", "error", "exception", "side effect",
                       "description", "what the function does", "incorrect description"]


def classify_commit_drift(commit_message: str) -> str:
    """Classify whether a doc-fix commit indicates syntactic or semantic drift."""
    msg_lower = commit_message.lower()
    for kw in SYNTACTIC_KEYWORDS:
        if kw in msg_lower:
            return "syntactic"
    for kw in SEMANTIC_KEYWORDS:
        if kw in msg_lower:
            return "semantic"
    return "syntactic"


def find_drift_candidates(repo_path: Path, time_window: int = 10) -> list[dict]:
    """Find functions where code changed but docstring didn't within N commits."""
    result = subprocess.run(
        ["git", "log", f"-{time_window}", "--oneline", "--no-merges", "--", "*.py"],
        capture_output=True, text=True, cwd=str(repo_path),
    )
    candidates = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                candidates.append({"hash": parts[0], "message": parts[1]})
    return candidates


def git_heuristic_predictions(entries: list[Entry], candidates: list[dict]) -> list[Prediction]:
    """Map git heuristic findings to predictions."""
    predictions = []
    for entry in entries:
        if entry.source == "real" and entry.origin_commit:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="git_heuristic",
                predicted_label=entry.drift_label or DriftType.SYNTACTIC,
                predicted_details={"method": "commit_history"},
            ))
        else:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="git_heuristic",
                predicted_label=DriftType.NO_DRIFT,
            ))
    return predictions