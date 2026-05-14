import re


def remove_param_from_docstring(docstring: str, param_name: str) -> str:
    """Remove a parameter from the Args section of a docstring."""
    lines = docstring.split("\n")
    result = []
    skip = False
    in_args = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("Args:"):
            in_args = True
            result.append(line)
            continue
        if in_args:
            if stripped.startswith("Returns:") or stripped.startswith("Raises:"):
                in_args = False
                result.append(line)
                continue
            if stripped.startswith("Args:") or (not stripped and i > 0 and lines[i-1].strip() == ""):
                in_args = False
            if skip and not stripped.startswith((" " * 4, "\t")) and stripped != "":
                skip = False
            if stripped.startswith(f"{param_name}") and (":" in stripped or ")" in stripped):
                skip = True
                continue
            if skip:
                if stripped == "" or not stripped.startswith((" " * 4, "\t")):
                    skip = False
                else:
                    continue
            result.append(line)
        else:
            result.append(line)
    return "\n".join(result)


def rename_param_in_docstring(docstring: str, old_name: str, new_name: str) -> str:
    """Rename a parameter in the docstring."""
    return docstring.replace(f"{old_name}:", f"{new_name}:").replace(
        f"{old_name} ", f"{new_name} "
    )


def change_param_type_in_docstring(docstring: str, param_name: str, new_type: str) -> str:
    """Change the type annotation of a parameter in the docstring."""
    pattern = rf"({param_name}\s*\()(\w+)(\):)"
    result = re.sub(pattern, rf"\1{new_type}\3", docstring)
    if result == docstring:
        # Fallback: try "param (type):" format
        pattern2 = rf"({param_name}\s*\()(\w+)(\)\s*:)"
        result = re.sub(pattern2, rf"\1{new_type}\3", docstring)
    return result


def add_phantom_param_to_docstring(docstring: str, param_name: str, description: str) -> str:
    """Add a parameter to the docstring that doesn't exist in the signature."""
    lines = docstring.split("\n")
    result = []
    inserted = False
    for line in lines:
        result.append(line)
        if line.strip().startswith("Args:") and not inserted:
            result.append(f"    {param_name}: {description}")
            inserted = True
    if not inserted:
        result.append(f"\nArgs:\n    {param_name}: {description}")
    return "\n".join(result)


def change_return_type_in_docstring(docstring: str, new_type: str) -> str:
    """Change the return type in the docstring."""
    pattern = r"(Returns:\s*\n\s*)(\w+)(:)"
    return re.sub(pattern, rf"\1{new_type}\3", docstring)