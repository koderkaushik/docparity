from src.generation.syntactic_mutators import (
    remove_param_from_docstring,
    rename_param_in_docstring,
    change_param_type_in_docstring,
    add_phantom_param_to_docstring,
    change_return_type_in_docstring,
)
from src.generation.semantic_mutators import (
    replace_behavioral_keyword,
    remove_exception_from_docstring,
    add_incorrect_claim,
    change_purpose_description,
)


# --- Syntactic mutator tests ---

def test_remove_param_from_docstring():
    docstring = "Do something.\n\nArgs:\n    x: First.\n    y: Second.\n\nReturns:\n    int: Result."
    result = remove_param_from_docstring(docstring, "y")
    assert "y" not in result
    assert "x:" in result


def test_rename_param_in_docstring():
    docstring = "Do something.\n\nArgs:\n    x: First.\n    y: Second."
    result = rename_param_in_docstring(docstring, "x", "x_coord")
    assert "x_coord" in result


def test_change_param_type_in_docstring():
    docstring = "Do something.\n\nArgs:\n    x (int): First."
    result = change_param_type_in_docstring(docstring, "x", "str")
    assert "str" in result


def test_add_phantom_param_to_docstring():
    docstring = "Do something.\n\nArgs:\n    x: First."
    result = add_phantom_param_to_docstring(docstring, "phantom", "A phantom param.")
    assert "phantom" in result


def test_change_return_type_in_docstring():
    docstring = "Do something.\n\nReturns:\n    int: The result."
    result = change_return_type_in_docstring(docstring, "float")
    assert "float" in result


# --- Semantic mutator tests ---

def test_replace_behavioral_keyword():
    docstring = "Compute the product of x and y."
    result = replace_behavioral_keyword(docstring, {"product": "sum"})
    assert "sum" in result
    assert "product" not in result


def test_remove_exception_from_docstring():
    docstring = "Do something.\n\nRaises:\n    ValueError: If y is zero."
    result = remove_exception_from_docstring(docstring)
    assert "Raises" not in result
    assert "ValueError" not in result


def test_add_incorrect_claim():
    docstring = "Compute x plus y."
    result = add_incorrect_claim(docstring, "This function is thread-safe.")
    assert "thread-safe" in result


def test_change_purpose_description():
    docstring = "Sort a list in ascending order."
    result = change_purpose_description(docstring, "Filter a list by removing duplicates.")
    assert "Filter" in result