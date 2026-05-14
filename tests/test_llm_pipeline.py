import yaml
from pathlib import Path
from src.shared.schema import Entry, DriftType
from src.llm.prompt_builder import build_prompt
from src.llm.response_parser import parse_response


def test_build_prompt_zero_shot():
    entry = Entry(
        entry_id="test_001", source="synthetic", origin_repo="test",
        origin_file="test.py", origin_function="add",
        code="return x + y", docstring="Add numbers.",
        full_source='def add(x, y):\n    """Add numbers."""\n    return x + y',
    )
    prompt = build_prompt(entry, "zero_shot", Path("configs/prompts.yaml"))
    assert "return x + y" in prompt
    assert "Add numbers" in prompt


def test_parse_response_valid_json():
    response = '{"drift_type": "syntactic", "description": "missing param"}'
    result = parse_response(response)
    assert result["drift_type"] == "syntactic"


def test_parse_response_with_reasoning():
    response = '{"drift_type": "semantic", "description": "wrong behavior", "reasoning": "doc says product"}'
    result = parse_response(response)
    assert result["drift_type"] == "semantic"
    assert "reasoning" in result


def test_parse_response_fallback_regex():
    response = 'The drift type is semantic. The docstring describes multiplication but code does division.'
    result = parse_response(response)
    assert result["drift_type"] == "semantic"


def test_parse_response_no_drift():
    response = '{"drift_type": "no-drift", "description": "No inconsistencies found."}'
    result = parse_response(response)
    assert result["drift_type"] == "no-drift"


def test_parse_response_embedded_json():
    response = 'Based on my analysis: {"drift_type": "syntactic", "description": "param missing"}'
    result = parse_response(response)
    assert result["drift_type"] == "syntactic"