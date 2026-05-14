import subprocess
from pathlib import Path
from src.mining.function_extractor import extract_functions, FunctionInfo
from src.shared.schema import Entry, DriftType, DriftDetails


def classify_drift_type(description: str) -> str:
    syntactic_keywords = ["param", "parameter", "argument", "return type", "signature",
                          "missing from docstring", "type mismatch", "not documented"]
    description_lower = description.lower()
    for kw in syntactic_keywords:
        if kw in description_lower:
            return "syntactic"
    return "semantic"


def find_doc_fix_commits(repo_path: Path) -> list[dict]:
    """Find commits that fixed documentation/docstrings."""
    result = subprocess.run(
        ["git", "log", "--all", "--grep=doc\\|docstring\\|documentation",
         "--oneline", "--no-merges"],
        capture_output=True, text=True, cwd=str(repo_path),
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commits.append({"hash": parts[0], "message": parts[1]})
    return commits


def extract_entry_from_commit(
    func_info: FunctionInfo,
    repo_name: str,
    commit_hash: str,
    file_path: str,
    drift_type: DriftType,
    drift_description: str,
) -> Entry:
    details = DriftDetails(type=drift_type, description=drift_description)
    return Entry(
        entry_id=f"real_{repo_name}_{func_info.name}_{commit_hash[:7]}",
        source="real",
        origin_repo=repo_name,
        origin_commit=commit_hash,
        origin_file=file_path,
        origin_function=func_info.name,
        code=func_info.code,
        docstring=func_info.docstring,
        full_source=func_info.full_source,
        drift_label=drift_type,
        drift_present=True,
        drift_details=details,
    )