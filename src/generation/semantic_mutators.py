import re


def replace_behavioral_keyword(docstring: str, replacements: dict[str, str]) -> str:
    """Replace behavioral keywords in the docstring."""
    result = docstring
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def remove_exception_from_docstring(docstring: str) -> str:
    """Remove the Raises section from a docstring."""
    lines = docstring.split("\n")
    result = []
    in_raises = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Raises:"):
            in_raises = True
            continue
        if in_raises:
            # Indented lines are continuation of Raises section
            if line.startswith((" " * 4, "\t")) or stripped == "":
                continue
            # Non-indented, non-empty line = start of new section
            in_raises = False
            result.append(line)
            continue
        result.append(line)
    return "\n".join(result)


def add_incorrect_claim(docstring: str, claim: str) -> str:
    """Add an incorrect behavioral claim to the docstring."""
    return docstring.rstrip() + f"\n\nNote: {claim}"


def change_purpose_description(docstring: str, new_purpose: str) -> str:
    """Replace the first sentence (purpose) of the docstring."""
    lines = docstring.split("\n")
    if lines:
        for i, line in enumerate(lines):
            if line.strip():
                lines[i] = new_purpose
                break
    return "\n".join(lines)