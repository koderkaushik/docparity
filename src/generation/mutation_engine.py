import random
import hashlib
from src.shared.schema import Entry, DriftType, DriftDetails
from src.generation import syntactic_mutators, semantic_mutators


SYNTACTIC_MUTATORS = [
    ("remove_param", lambda doc, ctx: syntactic_mutators.remove_param_from_docstring(doc, ctx["param"])),
    ("rename_param", lambda doc, ctx: syntactic_mutators.rename_param_in_docstring(doc, ctx["old_name"], ctx["new_name"])),
    ("change_param_type", lambda doc, ctx: syntactic_mutators.change_param_type_in_docstring(doc, ctx["param"], ctx["new_type"])),
    ("add_phantom_param", lambda doc, ctx: syntactic_mutators.add_phantom_param_to_docstring(doc, ctx["param"], ctx["description"])),
    ("change_return_type", lambda doc, ctx: syntactic_mutators.change_return_type_in_docstring(doc, ctx["new_type"])),
]

SEMANTIC_MUTATORS = [
    ("replace_behavioral_keyword", lambda doc, ctx: semantic_mutators.replace_behavioral_keyword(doc, ctx["replacements"])),
    ("remove_exception", lambda doc, ctx: semantic_mutators.remove_exception_from_docstring(doc)),
    ("add_incorrect_claim", lambda doc, ctx: semantic_mutators.add_incorrect_claim(doc, ctx["claim"])),
    ("change_purpose", lambda doc, ctx: semantic_mutators.change_purpose_description(doc, ctx["new_purpose"])),
]


def mutate_entry(entry: Entry, drift_type: DriftType) -> Entry:
    """Apply a random mutation to create a drifted version of an entry."""
    if drift_type == DriftType.SYNTACTIC:
        mutators = SYNTACTIC_MUTATORS
    elif drift_type == DriftType.SEMANTIC:
        mutators = SEMANTIC_MUTATORS
    else:
        raise ValueError(f"Cannot mutate for drift type: {drift_type}")

    mutator_name, mutator_fn = random.choice(mutators)
    ctx = _build_mutation_context(entry, mutator_name)
    mutated_docstring = mutator_fn(entry.docstring, ctx)

    description = f"Applied {mutator_name} mutation"
    details = DriftDetails(type=drift_type, description=description)

    return Entry(
        entry_id=f"{entry.entry_id}_{drift_type.value}_{mutator_name}",
        source="synthetic",
        origin_repo=entry.origin_repo,
        origin_commit=None,
        origin_file=entry.origin_file,
        origin_function=entry.origin_function,
        code=entry.code,
        docstring=mutated_docstring,
        full_source=entry.full_source.replace(entry.docstring, mutated_docstring) if entry.docstring else mutated_docstring,
        drift_label=drift_type,
        drift_present=True,
        drift_details=details,
    )


def _build_mutation_context(entry: Entry, mutator_name: str) -> dict:
    """Build context dict for a mutator based on the entry."""
    seed = int(hashlib.md5(entry.entry_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    if mutator_name == "remove_param":
        return {"param": entry.args[0] if hasattr(entry, 'args') and entry.args else "x"}
    elif mutator_name == "rename_param":
        return {"old_name": "x", "new_name": "x_coord"}
    elif mutator_name == "change_param_type":
        return {"param": "x", "new_type": "str"}
    elif mutator_name == "add_phantom_param":
        return {"param": "phantom_extra", "description": "An extra parameter."}
    elif mutator_name == "change_return_type":
        return {"new_type": "float"}
    elif mutator_name == "replace_behavioral_keyword":
        return {"replacements": {"product": "sum", "multiply": "divide", "add": "subtract"}}
    elif mutator_name == "remove_exception":
        return {}
    elif mutator_name == "add_incorrect_claim":
        return {"claim": "This function is thread-safe and optimized for parallel execution."}
    elif mutator_name == "change_purpose":
        return {"new_purpose": "Filter and transform the input data."}
    return {}