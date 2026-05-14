import random
from src.mining.function_extractor import FunctionInfo
from src.shared.schema import Entry, DriftType


def _params_match_signature(func: FunctionInfo) -> bool:
    """Check if documented params are consistent with the function signature."""
    if not func.docstring:
        return False
    for arg in func.args:
        if arg not in func.docstring:
            return False
    return True


def sample_no_drift_functions(
    functions: list[FunctionInfo],
    max_samples: int,
    repo_name: str,
) -> list[Entry]:
    """Sample functions where code and docs are consistent."""
    candidates = [f for f in functions if f.docstring and _params_match_signature(f)]
    sampled = random.sample(candidates, min(max_samples, len(candidates)))
    entries = []
    for i, func in enumerate(sampled):
        entries.append(Entry(
            entry_id=f"real_{repo_name}_nodrift_{func.name}_{i}",
            source="real",
            origin_repo=repo_name,
            origin_commit=None,
            origin_file="",
            origin_function=func.name,
            code=func.code,
            docstring=func.docstring,
            full_source=func.full_source,
            drift_label=DriftType.NO_DRIFT,
            drift_present=False,
        ))
    return entries