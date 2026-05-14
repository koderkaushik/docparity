import ast
import re
from src.shared.schema import Entry, Prediction, DriftType


def _parse_docstring_args(docstring: str) -> list[str]:
    """Extract parameter names from Args section of a docstring."""
    params = []
    in_args = False
    for line in docstring.split("\n"):
        stripped = line.strip()
        if stripped.startswith("Args:"):
            in_args = True
            continue
        if in_args:
            if stripped.startswith("Returns:") or stripped.startswith("Raises:"):
                break
            match = re.match(r"(\w+)\s*(?:\([^)]*\))?\s*:", stripped)
            if match:
                params.append(match.group(1))
    return params


def _parse_docstring_returns(docstring: str) -> str | None:
    """Extract return type from docstring."""
    match = re.search(r"Returns:\s*\n?\s*(\w+)\s*:", docstring)
    return match.group(1) if match else None


def check_entry(entry: Entry) -> Prediction:
    """Compare a function's signature against its docstring using AST parsing."""
    try:
        tree = ast.parse(entry.full_source)
    except SyntaxError:
        return Prediction(
            entry_id=entry.entry_id, approach="ast_checker",
            predicted_label=DriftType.NO_DRIFT,
            predicted_details={"error": "syntax_error"},
        )

    mismatches = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name != entry.origin_function:
                continue
            sig_params = [a.arg for a in node.args.args if a.arg != "self"]
            doc_params = _parse_docstring_args(entry.docstring) if entry.docstring else []

            missing_params = [p for p in sig_params if p not in doc_params]
            extra_params = [p for p in doc_params if p not in sig_params]

            if missing_params:
                mismatches.append(f"Missing from docstring: {missing_params}")
            if extra_params:
                mismatches.append(f"Extra in docstring: {extra_params}")

            sig_return = ast.unparse(node.returns) if node.returns else None
            doc_return = _parse_docstring_returns(entry.docstring) if entry.docstring else None
            if sig_return and doc_return and sig_return != doc_return:
                mismatches.append(f"Return type mismatch: sig={sig_return}, doc={doc_return}")

    if mismatches:
        return Prediction(
            entry_id=entry.entry_id, approach="ast_checker",
            predicted_label=DriftType.SYNTACTIC,
            predicted_details={"mismatches": mismatches},
        )
    return Prediction(
        entry_id=entry.entry_id, approach="ast_checker",
        predicted_label=DriftType.NO_DRIFT,
    )