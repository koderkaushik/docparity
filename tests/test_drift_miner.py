import ast
from src.mining.function_extractor import extract_functions, FunctionInfo
from src.mining.drift_miner import classify_drift_type


def test_extract_functions_with_docstring():
    source = '''def add(x: int, y: int) -> int:
    """Add two numbers.

    Args:
        x: First number.
        y: Second number.

    Returns:
        int: The sum.
    """
    return x + y
'''
    funcs = extract_functions(source)
    assert len(funcs) == 1
    assert funcs[0].name == "add"
    assert "Add two numbers" in funcs[0].docstring
    assert funcs[0].args == ["x", "y"]
    assert funcs[0].return_annotation == "int"


def test_extract_functions_no_docstring():
    source = "def foo():\n    pass\n"
    funcs = extract_functions(source)
    assert len(funcs) == 1
    assert funcs[0].docstring == ""


def test_extract_multiple_functions():
    source = '''def add(x, y):
    """Add."""
    return x + y

def sub(x, y):
    """Subtract."""
    return x - y
'''
    funcs = extract_functions(source)
    assert len(funcs) == 2
    names = [f.name for f in funcs]
    assert "add" in names
    assert "sub" in names


def test_classify_drift_type_param_mismatch():
    desc = "Parameter 'z' missing from docstring"
    assert classify_drift_type(desc) == "syntactic"


def test_classify_drift_type_behavior_mismatch():
    desc = "Docstring says product but code computes division"
    assert classify_drift_type(desc) == "semantic"


def test_classify_drift_type_return_mismatch():
    desc = "Return type documented as int but signature says float"
    assert classify_drift_type(desc) == "syntactic"