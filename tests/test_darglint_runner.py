from src.baselines.darglint_runner import parse_darglint_output


def test_parse_darglint_output_finds_missing_param():
    output = "flask/app.py:42:func run: ARGS section missing parameter: load_dotenv"
    results = parse_darglint_output(output)
    assert len(results) == 1
    assert results[0]["error_type"] == "missing_param"
    assert results[0]["param"] == "load_dotenv"


def test_parse_darglint_output_empty():
    results = parse_darglint_output("")
    assert results == []