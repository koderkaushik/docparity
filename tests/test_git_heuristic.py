from src.baselines.git_heuristic import classify_commit_drift


def test_classify_commit_drift_doc_fix():
    msg = "Fix docstring for compute function"
    result = classify_commit_drift(msg)
    assert result in ("syntactic", "semantic")


def test_classify_commit_drift_behavior():
    msg = "Update documentation to reflect error handling"
    result = classify_commit_drift(msg)
    assert result == "semantic"


def test_classify_commit_drift_param():
    msg = "Add missing parameter to docstring"
    result = classify_commit_drift(msg)
    assert result == "syntactic"


def test_classify_commit_drift_default():
    msg = "Fix documentation typo"
    result = classify_commit_drift(msg)
    assert result == "syntactic"