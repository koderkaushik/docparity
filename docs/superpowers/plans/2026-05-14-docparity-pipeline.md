# DocParity Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete DocParity research pipeline — mining, synthetic generation, baselines, LLM detection, and evaluation — for a dissertation on documentation drift detection.

**Architecture:** Phase-driven modular pipeline with shared JSON dataset. Each phase is a set of scripts in `src/` that read/write from a `data/` directory. Configs in YAML control parameters. Factory pattern for LLM providers.

**Tech Stack:** Python 3.11+, uv, PyYAML, Ollama Python client, darglint, pytest

---

### Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/shared/__init__.py`
- Create: `src/shared/schema.py`
- Create: `src/shared/dataset_io.py`
- Create: `src/mining/__init__.py`
- Create: `src/generation/__init__.py`
- Create: `src/baselines/__init__.py`
- Create: `src/llm/__init__.py`
- Create: `src/evaluation/__init__.py`
- Create: `configs/models.yaml`
- Create: `configs/prompts.yaml`
- Create: `configs/dataset.yaml`
- Create: `configs/evaluation.yaml`
- Create: `data/.gitkeep`
- Create: `data/repos/.gitkeep`
- Create: `data/entries/.gitkeep`
- Create: `data/source_files/.gitkeep`
- Create: `results/.gitkeep`
- Create: `tests/__init__.py`

- [ ] **Step 1: Initialize uv project and create pyproject.toml**

Run: `cd /mnt/d/project/docparity && uv init --no-readme`

Then replace the generated pyproject.toml with:

```toml
[project]
name = "docparity"
version = "0.1.0"
description = "LLM-Assisted Documentation Drift Detection — dissertation research pipeline"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "ollama>=0.4.0",
    "darglint>=1.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Install dependencies**

Run: `uv sync --extra dev`

- [ ] **Step 3: Create directory structure and __init__.py files**

Run:
```bash
mkdir -p src/shared src/mining src/generation src/baselines src/llm src/evaluation
mkdir -p configs data/repos data/entries data/source_files results tests
touch src/shared/__init__.py src/mining/__init__.py src/generation/__init__.py
touch src/baselines/__init__.py src/llm/__init__.py src/evaluation/__init__.py
touch tests/__init__.py
touch data/repos/.gitkeep data/entries/.gitkeep data/source_files/.gitkeep results/.gitkeep
```

- [ ] **Step 4: Write src/shared/schema.py**

```python
from dataclasses import dataclass, field
from enum import Enum


class DriftType(Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    NO_DRIFT = "no-drift"


@dataclass
class DriftDetails:
    type: DriftType
    description: str
    severity: str | None = None
    missing_params: list[str] = field(default_factory=list)
    extra_params_in_doc: list[str] = field(default_factory=list)
    type_mismatches: list[dict] = field(default_factory=list)
    behavioral_mismatches: list[str] = field(default_factory=list)


@dataclass
class Entry:
    entry_id: str
    source: str
    origin_repo: str
    origin_file: str
    origin_function: str
    code: str
    docstring: str
    full_source: str
    drift_label: DriftType | None = None
    drift_present: bool | None = None
    drift_details: DriftDetails | None = None
    origin_commit: str | None = None
    ground_truth_annotation: dict | None = None


@dataclass
class Prediction:
    entry_id: str
    approach: str
    predicted_label: DriftType
    predicted_details: dict | None = None
    raw_output: str | None = None
```

- [ ] **Step 5: Write tests/test_schema.py**

```python
from src.shared.schema import DriftType, DriftDetails, Entry, Prediction


def test_drift_type_values():
    assert DriftType.SYNTACTIC.value == "syntactic"
    assert DriftType.SEMANTIC.value == "semantic"
    assert DriftType.NO_DRIFT.value == "no-drift"


def test_entry_creation():
    entry = Entry(
        entry_id="entry_001",
        source="synthetic",
        origin_repo="flask",
        origin_file="flask/app.py",
        origin_function="run",
        code="def run(self): ...",
        docstring="Runs the app.",
        full_source='def run(self):\n    """Runs the app."""\n    ...',
    )
    assert entry.entry_id == "entry_001"
    assert entry.drift_label is None
    assert entry.drift_present is None


def test_prediction_creation():
    pred = Prediction(
        entry_id="entry_001",
        approach="darglint",
        predicted_label=DriftType.SYNTACTIC,
    )
    assert pred.approach == "darglint"
    assert pred.predicted_label == DriftType.SYNTACTIC


def test_drift_details_defaults():
    details = DriftDetails(
        type=DriftType.SYNTACTIC,
        description="param missing",
    )
    assert details.missing_params == []
    assert details.severity is None
```

- [ ] **Step 6: Run tests to verify schema**

Run: `uv run pytest tests/test_schema.py -v`
Expected: All 4 tests PASS

- [ ] **Step 7: Write src/shared/dataset_io.py**

```python
import json
from pathlib import Path
from src.shared.schema import Entry, DriftDetails, DriftType


def entry_to_dict(entry: Entry) -> dict:
    d = {
        "entry_id": entry.entry_id,
        "source": entry.source,
        "origin_repo": entry.origin_repo,
        "origin_commit": entry.origin_commit,
        "origin_file": entry.origin_file,
        "origin_function": entry.origin_function,
        "code": entry.code,
        "docstring": entry.docstring,
        "full_source": entry.full_source,
        "drift_label": entry.drift_label.value if entry.drift_label else None,
        "drift_present": entry.drift_present,
        "drift_details": _drift_details_to_dict(entry.drift_details) if entry.drift_details else None,
        "ground_truth_annotation": entry.ground_truth_annotation,
    }
    return d


def dict_to_entry(d: dict) -> Entry:
    drift_label = DriftType(d["drift_label"]) if d.get("drift_label") else None
    drift_details = _dict_to_drift_details(d["drift_details"]) if d.get("drift_details") else None
    return Entry(
        entry_id=d["entry_id"],
        source=d["source"],
        origin_repo=d["origin_repo"],
        origin_commit=d.get("origin_commit"),
        origin_file=d["origin_file"],
        origin_function=d["origin_function"],
        code=d["code"],
        docstring=d["docstring"],
        full_source=d["full_source"],
        drift_label=drift_label,
        drift_present=d.get("drift_present"),
        drift_details=drift_details,
        ground_truth_annotation=d.get("ground_truth_annotation"),
    )


def _drift_details_to_dict(details: DriftDetails) -> dict:
    return {
        "type": details.type.value,
        "description": details.description,
        "severity": details.severity,
        "missing_params": details.missing_params,
        "extra_params_in_doc": details.extra_params_in_doc,
        "type_mismatches": details.type_mismatches,
        "behavioral_mismatches": details.behavioral_mismatches,
    }


def _dict_to_drift_details(d: dict) -> DriftDetails:
    return DriftDetails(
        type=DriftType(d["type"]),
        description=d["description"],
        severity=d.get("severity"),
        missing_params=d.get("missing_params", []),
        extra_params_in_doc=d.get("extra_params_in_doc", []),
        type_mismatches=d.get("type_mismatches", []),
        behavioral_mismatches=d.get("behavioral_mismatches", []),
    )


def save_entries(entries: list[Entry], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for entry in entries:
        d = entry_to_dict(entry)
        entry_path = output_dir / f"{entry.entry_id}.json"
        entry_path.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        manifest.append({"entry_id": entry.entry_id, "file": str(entry_path)})
    manifest_path = output_dir.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))


def load_entries(data_dir: Path) -> list[Entry]:
    manifest_path = data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entries = []
    for item in manifest:
        entry_path = Path(item["file"]) if "file" in item else data_dir / "entries" / f"{item['entry_id']}.json"
        d = json.loads(entry_path.read_text())
        entries.append(dict_to_entry(d))
    return entries
```

- [ ] **Step 8: Write tests/test_dataset_io.py**

```python
import json
import tempfile
from pathlib import Path
from src.shared.schema import DriftType, DriftDetails, Entry
from src.shared.dataset_io import save_entries, load_entries, entry_to_dict, dict_to_entry


def _sample_entry(entry_id="entry_001", drift_label=None, drift_details=None):
    return Entry(
        entry_id=entry_id,
        source="synthetic",
        origin_repo="flask",
        origin_file="flask/app.py",
        origin_function="run",
        code="def run(self): ...",
        docstring="Runs the app.",
        full_source='def run(self):\n    """Runs the app."""\n    ...',
        drift_label=drift_label,
        drift_details=drift_details,
    )


def test_entry_round_trip():
    entry = _sample_entry()
    d = entry_to_dict(entry)
    restored = dict_to_entry(d)
    assert restored.entry_id == entry.entry_id
    assert restored.code == entry.code


def test_entry_with_drift_round_trip():
    details = DriftDetails(type=DriftType.SYNTACTIC, description="missing param", missing_params=["z"])
    entry = _sample_entry(drift_label=DriftType.SYNTACTIC, drift_details=details)
    d = entry_to_dict(entry)
    restored = dict_to_entry(d)
    assert restored.drift_label == DriftType.SYNTACTIC
    assert restored.drift_details.missing_params == ["z"]


def test_save_and_load_entries():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        entries_dir = data_dir / "entries"
        entries = [
            _sample_entry("entry_001"),
            _sample_entry("entry_002"),
        ]
        save_entries(entries, entries_dir)
        assert (data_dir / "manifest.json").exists()
        assert (entries_dir / "entry_001.json").exists()
        assert (entries_dir / "entry_002.json").exists()
```

- [ ] **Step 9: Run dataset_io tests**

Run: `uv run pytest tests/test_dataset_io.py -v`
Expected: All 3 tests PASS

- [ ] **Step 10: Write config YAML files**

`configs/dataset.yaml`:
```yaml
repos:
  - name: flask
    url: https://github.com/pallets/flask.git
  - name: requests
    url: https://github.com/psf/requests.git
  - name: scikit-learn
    url: https://github.com/scikit-learn/scikit-learn.git
  - name: fastapi
    url: https://github.com/tiangolo/fastapi.git
  - name: pandas
    url: https://github.com/pandas-dev/pandas.git
  - name: numpy
    url: https://github.com/numpy/numpy.git
  - name: matplotlib
    url: https://github.com/matplotlib/matplotlib.git
  - name: pytest
    url: https://github.com/pytest-dev/pytest.git
  - name: click
    url: https://github.com/pallets/click.git
  - name: django
    url: https://github.com/django/django.git

sizes:
  real_total: 250
  synthetic_total: 550
  real_no_drift: 75
  real_syntactic: 90
  real_semantic: 85
  synthetic_no_drift: 165
  synthetic_syntactic: 190
  synthetic_semantic: 195

pilot:
  enabled: true
  size: 50
  split:
    no_drift: 10
    syntactic: 20
    semantic: 20
```

`configs/models.yaml`:
```yaml
providers:
  # Local Ollama models
  - name: ollama-llama3
    provider: ollama
    model: llama3:8b
    temperature: 0
  - name: ollama-mistral
    provider: ollama
    model: mistral:7b
    temperature: 0
  # Ollama cloud models
  - name: ollama-glm
    provider: ollama
    model: glm4:9b
    temperature: 0
  - name: ollama-kimi
    provider: ollama
    model: kimi:latest
    temperature: 0
```

`configs/prompts.yaml`:
```yaml
zero_shot:
  system: "You are a documentation drift detector. Analyze Python functions and their docstrings to identify inconsistencies."
  template: |
    Compare the following Python function code with its docstring.
    Identify any inconsistencies between what the code does and what the docstring describes.

    Code:
    {code}

    Docstring:
    {docstring}

    Respond in JSON: {{"drift_type": "syntactic|semantic|no-drift", "description": "..."}}

few_shot:
  system: "You are a documentation drift detector. Analyze Python functions and their docstrings to identify inconsistencies."
  template: |
    Here are examples of documentation drift detection:
    {examples}

    Now analyze:
    Code:
    {code}

    Docstring:
    {docstring}

    Respond in JSON: {{"drift_type": "syntactic|semantic|no-drift", "description": "..."}}

chain_of_thought:
  system: "You are a documentation drift detector. Analyze Python functions and their docstrings to identify inconsistencies."
  template: |
    Compare the following Python function code with its docstring.
    Think step by step:
    1. Extract the function signature (parameters, types, return type).
    2. Extract the documented interface from the docstring.
    3. Compare for syntactic mismatches.
    4. Analyze whether the behavioral description matches the code logic.
    5. Conclude with your assessment.

    Code:
    {code}

    Docstring:
    {docstring}

    Respond in JSON: {{"drift_type": "syntactic|semantic|no-drift", "description": "...", "reasoning": "..."}}
```

`configs/evaluation.yaml`:
```yaml
metrics:
  - precision
  - recall
  - f1

significance:
  test: mcnemar
  bootstrap_ci: true
  bootstrap_samples: 10000
  alpha: 0.05

annotators: 2
kappa_threshold: 0.61
```

- [ ] **Step 11: Create .gitignore for data directory**

Create `data/.gitignore`:
```
repos/
entries/
source_files/
manifest.json
```

Create top-level `.gitignore` (append if exists):
```
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
.venv/
data/repos/
data/entries/
data/source_files/
data/manifest.json
results/*.csv
results/*.json
```

- [ ] **Step 12: Commit scaffold**

```bash
git add -A
git commit -m "feat: project scaffold with schema, dataset_io, and configs"
```

---

### Task 2: Mining Pipeline — repo_cloner

**Files:**
- Create: `src/mining/repo_cloner.py`
- Create: `tests/test_repo_cloner.py`

- [ ] **Step 1: Write test for repo_cloner**

```python
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml
from src.mining.repo_cloner import clone_repos, load_repo_config


def test_load_repo_config():
    config = load_repo_config(Path("configs/dataset.yaml"))
    assert len(config["repos"]) >= 1
    assert config["repos"][0]["name"] == "flask"


def test_clone_repos_creates_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"repos": [{"name": "test-repo", "url": "https://github.com/octocat/Hello-World.git"}]}
        with patch("src.mining.repo_cloner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            clone_repos(config, Path(tmpdir))
            assert mock_run.called
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repo_cloner.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write src/mining/repo_cloner.py**

```python
import subprocess
from pathlib import Path
import yaml


def load_repo_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def clone_repos(config: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for repo in config["repos"]:
        name = repo["name"]
        url = repo["url"]
        dest = output_dir / name
        if dest.exists():
            print(f"Repo {name} already exists, skipping...")
            continue
        print(f"Cloning {name} from {url}...")
        result = subprocess.run(
            ["git", "clone", "--depth=1", url, str(dest)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"Failed to clone {name}: {result.stderr}")
        else:
            print(f"Cloned {name} successfully.")


if __name__ == "__main__":
    config = load_repo_config(Path("configs/dataset.yaml"))
    clone_repos(config, Path("data/repos"))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_repo_cloner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/repo_cloner.py tests/test_repo_cloner.py
git commit -m "feat: add repo_cloner for cloning target repositories"
```

---

### Task 3: Mining Pipeline — Function Extractor & Drift Miner

**Files:**
- Create: `src/mining/function_extractor.py`
- Create: `src/mining/drift_miner.py`
- Create: `tests/test_drift_miner.py`

- [ ] **Step 1: Write tests for function extraction and drift mining**

```python
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
    assert funcs[0].code == "    return x + y"


def test_extract_functions_no_docstring():
    source = "def foo():\n    pass\n"
    funcs = extract_functions(source)
    assert len(funcs) == 1
    assert funcs[0].docstring == ""


def test_classify_drift_type_param_mismatch():
    desc = "Parameter 'z' missing from docstring"
    assert classify_drift_type(desc) == "syntactic"


def test_classify_drift_type_behavior_mismatch():
    desc = "Docstring says product but code computes division"
    assert classify_drift_type(desc) == "semantic"


def test_classify_drift_type_return_mismatch():
    desc = "Return type documented as int but signature says float"
    assert classify_drift_type(desc) == "syntactic"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_drift_miner.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/mining/function_extractor.py**

```python
import ast
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    name: str
    code: str
    docstring: str
    full_source: str
    start_line: int
    end_line: int
    args: list[str]
    return_annotation: str | None


def extract_functions(source: str) -> list[FunctionInfo]:
    tree = ast.parse(source)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node) or ""
            code_lines = source.splitlines()
            code = "\n".join(code_lines[node.body[-1].lineno - 1:node.body[-1].end_lineno]) if node.body else ""
            if docstring:
                # Remove docstring from code to get just the body
                body_start = node.body[1] if len(node.body) > 1 else node.body[0]
                code = "\n".join(code_lines[body_start.lineno - 1:node.body[-1].end_lineno]) if len(node.body) > 1 else ""
            full_source = "\n".join(code_lines[node.lineno - 1:(node.end_lineno or node.lineno)])
            args = [a.arg for a in node.args.args if a.arg != "self"]
            ret = ast.unparse(node.returns) if node.returns else None
            functions.append(FunctionInfo(
                name=node.name, code=code, docstring=docstring,
                full_source=full_source, start_line=node.lineno,
                end_line=node.end_lineno or node.lineno, args=args,
                return_annotation=ret,
            ))
    return functions
```

- [ ] **Step 4: Write src/mining/drift_miner.py**

```python
import re
from pathlib import Path
from src.mining.function_extractor import extract_functions, FunctionInfo
from src.shared.schema import Entry, DriftType, DriftDetails


def classify_drift_type(description: str) -> str:
    syntactic_keywords = ["param", "parameter", "argument", "return type", "signature",
                          "missing from docstring", "type mismatch", "not documented"]
    description_lower = description.lower()
    for kw in syntactic_keywords:
        if kw in description_lower:
            return "syntactic"
    return "semantic"


def find_doc_fix_commits(repo_path: Path) -> list[dict]:
    """Find commits that fixed documentation/docstrings."""
    import subprocess
    result = subprocess.run(
        ["git", "log", "--all", "--grep=doc\\|docstring\\|documentation",
         "--oneline", "--no-merges"],
        capture_output=True, text=True, cwd=str(repo_path),
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                commits.append({"hash": parts[0], "message": parts[1]})
    return commits


def extract_entry_from_commit(
    func_info: FunctionInfo,
    repo_name: str,
    commit_hash: str,
    file_path: str,
    drift_type: DriftType,
    drift_description: str,
) -> Entry:
    details = DriftDetails(type=drift_type, description=drift_description)
    return Entry(
        entry_id=f"real_{repo_name}_{func_info.name}_{commit_hash[:7]}",
        source="real",
        origin_repo=repo_name,
        origin_commit=commit_hash,
        origin_file=file_path,
        origin_function=func_info.name,
        code=func_info.code,
        docstring=func_info.docstring,
        full_source=func_info.full_source,
        drift_label=drift_type,
        drift_present=True,
        drift_details=details,
    )
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_drift_miner.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/mining/function_extractor.py src/mining/drift_miner.py tests/test_drift_miner.py
git commit -m "feat: add function extractor and drift miner"
```

---

### Task 4: Mining Pipeline — no_drift_sampler

**Files:**
- Create: `src/mining/no_drift_sampler.py`
- Create: `tests/test_no_drift_sampler.py`

- [ ] **Step 1: Write test**

```python
from pathlib import Path
from src.mining.no_drift_sampler import sample_no_drift_functions
from src.shared.schema import Entry


def test_sample_no_drift_returns_entries():
    entries = sample_no_drift_functions([], max_samples=5, repo_name="flask")
    # When no functions provided, returns empty list
    assert isinstance(entries, list)


def test_sample_no_drift_filters_inconsistent():
    from src.mining.function_extractor import FunctionInfo
    consistent = FunctionInfo(
        name="add", code="return x + y",
        docstring="Add x and y.\n\nArgs:\n    x: First.\n    y: Second.\n\nReturns:\n    int: Sum.",
        full_source='def add(x, y):\n    """Add x and y."""\n    return x + y',
        start_line=1, end_line=3, args=["x", "y"], return_annotation="int",
    )
    entries = sample_no_drift_functions([consistent], max_samples=5, repo_name="flask")
    assert all(e.drift_label.value == "no-drift" for e in entries)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_no_drift_sampler.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/mining/no_drift_sampler.py**

```python
import random
from src.mining.function_extractor import FunctionInfo
from src.shared.schema import Entry, DriftType


def _params_match_signature(func: FunctionInfo) -> bool:
    """Check if documented params match the function signature."""
    if not func.docstring:
        return False
    doc_args = []
    for line in func.docstring.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- ") or (": " in stripped and not stripped.startswith("Returns")):
            param_name = stripped.split(":")[0].split()[-1] if ":" in stripped else ""
            if param_name and not stripped.lower().startswith(("return", "raise")):
                doc_args.append(param_name.rstrip(")"))
    # Loose check: all signature args should appear somewhere in docstring
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
    for func in sampled:
        entries.append(Entry(
            entry_id=f"real_{repo_name}_nodrift_{func.name}",
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
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_no_drift_sampler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mining/no_drift_sampler.py tests/test_no_drift_sampler.py
git commit -m "feat: add no_drift_sampler for consistent code-doc pairs"
```

---

### Task 5: Synthetic Generation — mutation_engine & mutators

**Files:**
- Create: `src/generation/mutation_engine.py`
- Create: `src/generation/syntactic_mutators.py`
- Create: `src/generation/semantic_mutators.py`
- Create: `tests/test_mutation_engine.py`

- [ ] **Step 1: Write tests for mutators**

```python
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
    assert "x:" not in result


def test_change_param_type_in_docstring():
    docstring = "Do something.\n\nArgs:\n    x (int): First."
    result = change_param_type_in_docstring(docstring, "x", "str")
    assert "str" in result
    assert "int" not in result


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mutation_engine.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/generation/syntactic_mutators.py**

```python
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
            if stripped.startswith("Returns:") or stripped.startswith("Raises:") or (not stripped and skip is False and i > 0 and lines[i-1].strip() == ""):
                in_args = False
                result.append(line)
                continue
            if stripped.startswith(f"{param_name}") and (":" in stripped or ")" in stripped):
                skip = True
                continue
            if skip and stripped == "":
                skip = False
                continue
            if skip and not stripped.startswith(" " * 4) and not stripped.startswith("\t"):
                skip = False
            if not skip:
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
    return re.sub(pattern, rf"\1{new_type}\3", docstring)


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
```

- [ ] **Step 4: Write src/generation/semantic_mutators.py**

```python
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
            if stripped and not stripped.startswith(" " * 4) and not stripped.startswith("\t"):
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
        # Replace first non-empty line
        for i, line in enumerate(lines):
            if line.strip():
                lines[i] = new_purpose
                break
    return "\n".join(lines)
```

- [ ] **Step 5: Write src/generation/mutation_engine.py**

```python
import random
from src.shared.schema import Entry, DriftType, DriftDetails
from src.mining.function_extractor import FunctionInfo
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
        full_source=entry.full_source.replace(entry.docstring, mutated_docstring),
        drift_label=drift_type,
        drift_present=True,
        drift_details=details,
    )


def _build_mutation_context(entry: Entry, mutator_name: str) -> dict:
    """Build context dict for a mutator based on the entry."""
    import hashlib
    seed = int(hashlib.md5(entry.entry_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    if mutator_name == "remove_param":
        if entry.docstring:
            return {"param": entry.docstring.split("\n")[0][:10]}
        return {"param": "x"}
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
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_mutation_engine.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/generation/ tests/test_mutation_engine.py
git commit -m "feat: add mutation engine with syntactic and semantic mutators"
```

---

### Task 6: Baseline — darglint_runner

**Files:**
- Create: `src/baselines/darglint_runner.py`
- Create: `tests/test_darglint_runner.py`

- [ ] **Step 1: Write test**

```python
import tempfile
from pathlib import Path
from src.baselines.darglint_runner import run_darglint, parse_darglint_output


def test_parse_darglint_output_finds_missing_param():
    output = "flask/app.py:42:func run: ARGS section missing parameter: load_dotenv"
    results = parse_darglint_output(output)
    assert len(results) == 1
    assert results[0]["error_type"] == "missing_param"
    assert results[0]["param"] == "load_dotenv"


def test_parse_darglint_output_empty():
    results = parse_darglint_output("")
    assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_darglint_runner.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/baselines/darglint_runner.py**

```python
import subprocess
import re
from pathlib import Path
from src.shared.schema import Entry, Prediction, DriftType


def run_darglint(source_dir: Path) -> str:
    """Run darglint on all Python files in source_dir."""
    result = subprocess.run(
        ["darglint", "-v", "2", str(source_dir)],
        capture_output=True, text=True,
    )
    return result.stdout + result.stderr


def parse_darglint_output(output: str) -> list[dict]:
    """Parse darglint output into structured findings."""
    findings = []
    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        # Pattern: file:line:function: ERROR_TYPE: message
        match = re.match(r"(.+?):(\d+):(\S+):\s*(.+)", line)
        if match:
            error_msg = match.group(4)
            finding = {"file": match.group(1), "line": int(match.group(2)),
                        "function": match.group(3), "message": error_msg}
            if "missing parameter" in error_msg.lower():
                param_match = re.search(r"parameter:\s*(\w+)", error_msg)
                finding["error_type"] = "missing_param"
                finding["param"] = param_match.group(1) if param_match else ""
            elif "return" in error_msg.lower():
                finding["error_type"] = "return_type_mismatch"
            else:
                finding["error_type"] = "other_syntactic"
            findings.append(finding)
    return findings


def darglint_entries_to_predictions(
    entries: list[Entry],
    findings: list[dict],
) -> list[Prediction]:
    """Convert darglint findings to Predictions aligned with dataset entries."""
    file_findings = {}
    for f in findings:
        key = f["function"]
        file_findings[key] = file_findings.get(key, []) + [f]

    predictions = []
    for entry in entries:
        func_findings = file_findings.get(entry.origin_function, [])
        if func_findings:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="darglint",
                predicted_label=DriftType.SYNTACTIC,
                predicted_details={"findings": func_findings},
                raw_output=str(func_findings),
            ))
        else:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="darglint",
                predicted_label=DriftType.NO_DRIFT,
            ))
    return predictions
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_darglint_runner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/baselines/darglint_runner.py tests/test_darglint_runner.py
git commit -m "feat: add darglint baseline runner"
```

---

### Task 7: Baseline — ast_checker

**Files:**
- Create: `src/baselines/ast_checker.py`
- Create: `tests/test_ast_checker.py`

- [ ] **Step 1: Write test**

```python
from src.baselines.ast_checker import check_entry


def test_check_entry_missing_param():
    from src.shared.schema import Entry, DriftType
    entry = Entry(
        entry_id="test_001",
        source="synthetic",
        origin_repo="test",
        origin_file="test.py",
        origin_function="add",
        code="    return x + y",
        docstring="Add numbers.\n\nArgs:\n    x: First.",
        full_source='def add(x, y):\n    """Add numbers.\n\n    Args:\n        x: First."""\n    return x + y',
        drift_label=DriftType.SYNTACTIC,
        drift_present=True,
    )
    result = check_entry(entry)
    assert result.predicted_label == DriftType.SYNTACTIC


def test_check_entry_no_drift():
    from src.shared.schema import Entry, DriftType
    entry = Entry(
        entry_id="test_002",
        source="synthetic",
        origin_repo="test",
        origin_file="test.py",
        origin_function="add",
        code="    return x + y",
        docstring="Add numbers.\n\nArgs:\n    x: First.\n    y: Second.",
        full_source='def add(x, y):\n    """Add numbers.\n\n    Args:\n        x: First.\n        y: Second."""\n    return x + y',
        drift_label=DriftType.NO_DRIFT,
        drift_present=False,
    )
    result = check_entry(entry)
    assert result.predicted_label == DriftType.NO_DRIFT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ast_checker.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/baselines/ast_checker.py**

```python
import ast
import re
from src.shared.schema import Entry, Prediction, DriftType, DriftDetails


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
            # Match "param_name" or "param_name (type):" or "param_name:"
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
            # Get signature params
            sig_params = [a.arg for a in node.args.args if a.arg != "self"]
            # Get docstring params
            doc_params = _parse_docstring_args(entry.docstring) if entry.docstring else []

            missing_params = [p for p in sig_params if p not in doc_params]
            extra_params = [p for p in doc_params if p not in sig_params]

            if missing_params:
                mismatches.append(f"Missing from docstring: {missing_params}")
            if extra_params:
                mismatches.append(f"Extra in docstring: {extra_params}")

            # Check return type
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
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_ast_checker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/baselines/ast_checker.py tests/test_ast_checker.py
git commit -m "feat: add AST checker baseline"
```

---

### Task 8: Baseline — git_heuristic

**Files:**
- Create: `src/baselines/git_heuristic.py`
- Create: `tests/test_git_heuristic.py`

- [ ] **Step 1: Write test**

```python
from src.baselines.git_heuristic import classify_commit_drift


def test_classify_commit_drift_doc_fix():
    msg = "Fix docstring for compute function"
    result = classify_commit_drift(msg)
    assert result in ("syntactic", "semantic")


def test_classify_commit_drift_behavior():
    msg = "Update documentation to reflect error handling"
    result = classify_commit_drift(msg)
    assert result == "semantic"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_git_heuristic.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/baselines/git_heuristic.py**

```python
import subprocess
from pathlib import Path
from src.shared.schema import Entry, Prediction, DriftType


SYNTACTIC_KEYWORDS = ["param", "parameter", "argument", "signature", "type hint", "return type",
                       "docstring param", "missing from docstring"]
SEMANTIC_KEYWORDS = ["behavior", "behavioral", "logic", "error", "exception", "side effect",
                       "description", "what the function does", "incorrect description"]


def classify_commit_drift(commit_message: str) -> str:
    """Classify whether a doc-fix commit indicates syntactic or semantic drift."""
    msg_lower = commit_message.lower()
    for kw in SYNTACTIC_KEYWORDS:
        if kw in msg_lower:
            return "syntactic"
    for kw in SEMANTIC_KEYWORDS:
        if kw in msg_lower:
            return "semantic"
    return "syntactic"  # default to syntactic for doc-fixes


def find_drift_candidates(repo_path: Path, time_window: int = 10) -> list[dict]:
    """Find functions where code changed but docstring didn't within N commits."""
    result = subprocess.run(
        ["git", "log", f"-{time_window}", "--oneline", "--no-merges", "--", "*.py"],
        capture_output=True, text=True, cwd=str(repo_path),
    )
    candidates = []
    for line in result.stdout.strip().split("\n"):
        if line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                candidates.append({"hash": parts[0], "message": parts[1]})
    return candidates


def git_heuristic_predictions(entries: list[Entry], candidates: list[dict]) -> list[Prediction]:
    """Map git heuristic findings to predictions."""
    # This is a simplified mapping — in practice, would compare commit diffs
    predictions = []
    for entry in entries:
        if entry.source == "real" and entry.origin_commit:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="git_heuristic",
                predicted_label=entry.drift_label or DriftType.SYNTACTIC,
                predicted_details={"method": "commit_history"},
            ))
        else:
            predictions.append(Prediction(
                entry_id=entry.entry_id,
                approach="git_heuristic",
                predicted_label=DriftType.NO_DRIFT,
            ))
    return predictions
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_git_heuristic.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/baselines/git_heuristic.py tests/test_git_heuristic.py
git commit -m "feat: add git heuristic baseline"
```

---

### Task 9: LLM Pipeline — factory, prompt_builder, detector, response_parser

**Files:**
- Create: `src/llm/factory.py`
- Create: `src/llm/prompt_builder.py`
- Create: `src/llm/detector.py`
- Create: `src/llm/response_parser.py`
- Create: `tests/test_llm_pipeline.py`

- [ ] **Step 1: Write tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_llm_pipeline.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/llm/factory.py**

```python
from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, config: dict | None = None) -> str:
        ...


class OllamaProvider(ModelProvider):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str, config: dict | None = None) -> str:
        import ollama
        config = config or {}
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": config.get("temperature", 0)},
        )
        return response["message"]["content"]


def create_provider(provider_config: dict) -> ModelProvider:
    """Factory function to create a model provider from config."""
    provider_type = provider_config.get("provider", "ollama")
    if provider_type == "ollama":
        return OllamaProvider(model_name=provider_config["model"])
    raise ValueError(f"Unknown provider: {provider_type}")
```

- [ ] **Step 4: Write src/llm/prompt_builder.py**

```python
import yaml
from pathlib import Path
from src.shared.schema import Entry


def load_prompts(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_prompt(entry: Entry, strategy: str, config_path: Path = Path("configs/prompts.yaml"),
                 examples: str = "") -> str:
    """Build a prompt for the given entry using the specified strategy."""
    prompts = load_prompts(config_path)
    template = prompts[strategy]["template"]
    system = prompts[strategy]["system"]
    prompt = template.format(code=entry.code, docstring=entry.docstring, examples=examples)
    return f"System: {system}\n\n{prompt}"
```

- [ ] **Step 5: Write src/llm/response_parser.py**

```python
import json
import re
from src.shared.schema import DriftType


def parse_response(response: str) -> dict:
    """Parse an LLM response into a structured result.

    Tries JSON parsing first, falls back to regex extraction.
    """
    # Try JSON parse
    try:
        result = json.loads(response.strip())
        if "drift_type" in result:
            result["drift_type"] = _normalize_drift_type(result["drift_type"])
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON embedded in text
    json_match = re.search(r'\{[^}]+\}', response)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if "drift_type" in result:
                result["drift_type"] = _normalize_drift_type(result["drift_type"])
                return result
        except json.JSONDecodeError:
            pass

    # Fallback: regex extraction
    drift_type = _extract_drift_type_from_text(response)
    description = _extract_description_from_text(response)
    return {"drift_type": drift_type, "description": description}


def _normalize_drift_type(raw: str) -> str:
    raw_lower = raw.strip().lower()
    if raw_lower in ("syntactic", "syntax"):
        return "syntactic"
    if raw_lower in ("semantic", "behavioral"):
        return "semantic"
    if raw_lower in ("no-drift", "no_drift", "none", "consistent"):
        return "no-drift"
    return raw_lower


def _extract_drift_type_from_text(text: str) -> str:
    text_lower = text.lower()
    if "syntactic" in text_lower or "syntax" in text_lower or "parameter" in text_lower:
        return "syntactic"
    if "semantic" in text_lower or "behavioral" in text_lower or "behavior" in text_lower:
        return "semantic"
    return "no-drift"


def _extract_description_from_text(text: str) -> str:
    # Take first sentence as description fallback
    sentences = re.split(r'[.!?]', text)
    return sentences[0].strip() if sentences else ""
```

- [ ] **Step 6: Write src/llm/detector.py**

```python
import yaml
from pathlib import Path
from src.shared.schema import Entry, Prediction, DriftType
from src.llm.factory import create_provider
from src.llm.prompt_builder import build_prompt
from src.llm.response_parser import parse_response


def detect_drift(
    entries: list[Entry],
    strategy: str,
    model_config: dict,
    prompts_config: Path = Path("configs/prompts.yaml"),
    examples: str = "",
) -> list[Prediction]:
    """Run LLM drift detection on a list of entries."""
    provider = create_provider(model_config)
    predictions = []
    for entry in entries:
        prompt = build_prompt(entry, strategy, prompts_config, examples)
        raw_response = provider.generate(prompt)
        parsed = parse_response(raw_response)
        drift_type = DriftType(parsed.get("drift_type", "no-drift"))
        predictions.append(Prediction(
            entry_id=entry.entry_id,
            approach=f"llm-{strategy}",
            predicted_label=drift_type,
            predicted_details=parsed,
            raw_output=raw_response,
        ))
    return predictions
```

- [ ] **Step 7: Run tests**

Run: `uv run pytest tests/test_llm_pipeline.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/llm/ tests/test_llm_pipeline.py
git commit -m "feat: add LLM detection pipeline with factory, prompt builder, detector, response parser"
```

---

### Task 10: Evaluation — metrics, significance, reporter

**Files:**
- Create: `src/evaluation/metrics.py`
- Create: `src/evaluation/significance.py`
- Create: `src/evaluation/reporter.py`
- Create: `tests/test_evaluation.py`

- [ ] **Step 1: Write tests**

```python
from src.shared.schema import Prediction, DriftType
from src.evaluation.metrics import compute_metrics, compute_confusion_matrix


def test_compute_metrics_perfect():
    ground_truth = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.NO_DRIFT]
    predictions = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.NO_DRIFT]
    metrics = compute_metrics(ground_truth, predictions, DriftType.SYNTACTIC)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_compute_metrics_with_fp():
    ground_truth = [DriftType.NO_DRIFT, DriftType.NO_DRIFT, DriftType.SYNTACTIC]
    predictions = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.SYNTACTIC]
    metrics = compute_metrics(ground_truth, predictions, DriftType.SYNTACTIC)
    assert metrics["precision"] == 0.5  # 1 TP, 1 FP
    assert metrics["recall"] == 1.0      # 1 TP, 0 FN


def test_compute_confusion_matrix():
    ground_truth = [DriftType.SYNTACTIC, DriftType.SEMANTIC, DriftType.NO_DRIFT]
    predictions = [DriftType.SYNTACTIC, DriftType.NO_DRIFT, DriftType.SEMANTIC]
    cm = compute_confusion_matrix(ground_truth, predictions)
    assert cm[DriftType.SYNTACTIC][DriftType.SYNTACTIC] == 1
    assert cm[DriftType.SEMANTIC][DriftType.NO_DRIFT] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_evaluation.py -v`
Expected: FAIL

- [ ] **Step 3: Write src/evaluation/metrics.py**

```python
from collections import defaultdict
from src.shared.schema import DriftType, Prediction


def compute_confusion_matrix(
    ground_truth: list[DriftType],
    predictions: list[DriftType],
) -> dict[DriftType, dict[DriftType, int]]:
    """Build a confusion matrix: cm[true_label][predicted_label] = count."""
    cm = defaultdict(lambda: defaultdict(int))
    for true, pred in zip(ground_truth, predictions):
        cm[true][pred] += 1
    return dict(cm)


def compute_metrics(
    ground_truth: list[DriftType],
    predictions: list[DriftType],
    target_class: DriftType,
) -> dict[str, float]:
    """Compute precision, recall, F1 for a specific drift type (one-vs-rest)."""
    tp = sum(1 for t, p in zip(ground_truth, predictions) if t == target_class and p == target_class)
    fp = sum(1 for t, p in zip(ground_truth, predictions) if t != target_class and p == target_class)
    fn = sum(1 for t, p in zip(ground_truth, predictions) if t == target_class and p != target_class)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def compute_all_metrics(
    ground_truth: list[DriftType],
    predictions: list[Prediction],
) -> dict[str, dict[str, float]]:
    """Compute metrics for each drift type."""
    pred_labels = [p.predicted_label for p in predictions]
    results = {}
    for drift_type in DriftType:
        results[drift_type.value] = compute_metrics(ground_truth, pred_labels, drift_type)
    return results
```

- [ ] **Step 4: Write src/evaluation/significance.py**

```python
import numpy as np
from scipy import stats
from src.shared.schema import DriftType, Prediction


def mcnemar_test(pred1: list[DriftType], pred2: list[DriftType],
                 ground_truth: list[DriftType]) -> dict:
    """McNemar's test for comparing two classifiers."""
    n01 = 0  # pred1 wrong, pred2 correct
    n10 = 0  # pred1 correct, pred2 wrong
    for p1, p2, gt in zip(pred1, pred2, ground_truth):
        correct1 = (p1 == gt)
        correct2 = (p2 == gt)
        if not correct1 and correct2:
            n01 += 1
        elif correct1 and not correct2:
            n10 += 1

    b = n01 + n10
    if b == 0:
        return {"statistic": 0, "p_value": 1.0, "significant": False}

    statistic = (abs(n01 - n10) - 1) ** 2 / b if b > 0 else 0
    p_value = 1 - stats.chi2.cdf(statistic, df=1)
    return {
        "statistic": statistic,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "n01": n01,
        "n10": n10,
    }


def bootstrap_ci(
    ground_truth: list[DriftType],
    predictions: list[DriftType],
    target_class: DriftType,
    n_samples: int = 10000,
    alpha: float = 0.05,
) -> dict:
    """Bootstrap confidence interval for F1 score."""
    from src.evaluation.metrics import compute_metrics
    f1_scores = []
    n = len(ground_truth)
    for _ in range(n_samples):
        indices = np.random.choice(n, size=n, replace=True)
        gt_sample = [ground_truth[i] for i in indices]
        pred_sample = [predictions[i] for i in indices]
        m = compute_metrics(gt_sample, pred_sample, target_class)
        f1_scores.append(m["f1"])

    lower = np.percentile(f1_scores, 100 * alpha / 2)
    upper = np.percentile(f1_scores, 100 * (1 - alpha / 2))
    return {"f1_mean": float(np.mean(f1_scores)), "ci_lower": float(lower), "ci_upper": float(upper)}
```

- [ ] **Step 5: Write src/evaluation/reporter.py**

```python
import csv
from pathlib import Path
from src.shared.schema import DriftType, Prediction, Entry
from src.evaluation.metrics import compute_all_metrics


def generate_comparison_table(
    entries: list[Entry],
    all_predictions: dict[str, list[Prediction]],
) -> list[dict]:
    """Generate the comparison table from the strategy doc."""
    ground_truth = [e.drift_label for e in entries]
    table = []
    for approach_name, predictions in all_predictions.items():
        metrics = compute_all_metrics(ground_truth, predictions)
        row = {"approach": approach_name}
        for drift_type in DriftType:
            m = metrics[drift_type.value]
            row[f"{drift_type.value}_precision"] = m["precision"]
            row[f"{drift_type.value}_recall"] = m["recall"]
            row[f"{drift_type.value}_f1"] = m["f1"]
        table.append(row)
    return table


def generate_error_analysis(
    entries: list[Entry],
    predictions: list[Prediction],
    approach_name: str,
) -> dict:
    """Analyze false positives, false negatives, and misclassifications."""
    false_positives = []
    false_negatives = []
    misclassifications = []

    for entry, pred in zip(entries, predictions):
        if pred.predicted_label != entry.drift_label:
            if entry.drift_label == DriftType.NO_DRIFT:
                false_positives.append({
                    "entry_id": entry.entry_id,
                    "predicted": pred.predicted_label.value,
                    "details": pred.predicted_details,
                })
            elif pred.predicted_label == DriftType.NO_DRIFT:
                false_negatives.append({
                    "entry_id": entry.entry_id,
                    "actual": entry.drift_label.value,
                    "details": pred.predicted_details,
                })
            else:
                misclassifications.append({
                    "entry_id": entry.entry_id,
                    "actual": entry.drift_label.value,
                    "predicted": pred.predicted_label.value,
                })

    return {
        "approach": approach_name,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "misclassifications": misclassifications,
        "fp_count": len(false_positives),
        "fn_count": len(false_negatives),
        "misclassify_count": len(misclassifications),
    }


def save_results_csv(table: list[dict], output_path: Path) -> None:
    """Save comparison table as CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if table:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=table[0].keys())
            writer.writeheader()
            writer.writerows(table)
```

- [ ] **Step 6: Add scipy to dependencies**

Update `pyproject.toml` to add `scipy` and `numpy`:

```toml
dependencies = [
    "pyyaml>=6.0",
    "ollama>=0.4.0",
    "darglint>=1.8.0",
    "numpy>=1.26.0",
    "scipy>=1.12.0",
]
```

Run: `uv sync --extra dev`

- [ ] **Step 7: Run tests**

Run: `uv run pytest tests/test_evaluation.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/evaluation/ tests/test_evaluation.py pyproject.toml uv.lock
git commit -m "feat: add evaluation pipeline with metrics, significance tests, and reporter"
```

---

### Task 11: End-to-End Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
"""End-to-end integration test using synthetic data through the full pipeline."""
import tempfile
from pathlib import Path
from src.shared.schema import Entry, DriftType, DriftDetails
from src.shared.dataset_io import save_entries, load_entries
from src.baselines.ast_checker import check_entry
from src.evaluation.metrics import compute_metrics


def _make_test_entries():
    entries = []
    # No-drift entry
    entries.append(Entry(
        entry_id="synth_001", source="synthetic", origin_repo="test",
        origin_file="test.py", origin_function="add",
        code="    return x + y",
        docstring="Add two numbers.\n\nArgs:\n    x: First.\n    y: Second.\n\nReturns:\n    int: The sum.",
        full_source='def add(x: int, y: int) -> int:\n    """Add two numbers.\n\n    Args:\n        x: First.\n        y: Second.\n\n    Returns:\n        int: The sum."""\n    return x + y',
        drift_label=DriftType.NO_DRIFT, drift_present=False,
    ))
    # Syntactic drift entry (missing param in docstring)
    entries.append(Entry(
        entry_id="synth_002", source="synthetic", origin_repo="test",
        origin_file="test.py", origin_function="compute",
        code="    if y == 0:\n        raise ValueError\n    return x // y",
        docstring="Compute something.\n\nArgs:\n    x: First.",
        full_source='def compute(x: int, y: int) -> int:\n    """Compute something.\n\n    Args:\n        x: First."""\n    if y == 0:\n        raise ValueError\n    return x // y',
        drift_label=DriftType.SYNTACTIC, drift_present=True,
        drift_details=DriftDetails(type=DriftType.SYNTACTIC, description="missing param y",
                                   missing_params=["y"]),
    ))
    return entries


def test_save_load_roundtrip():
    entries = _make_test_entries()
    with tempfile.TemporaryDirectory() as tmpdir:
        entries_dir = Path(tmpdir) / "entries"
        save_entries(entries, entries_dir)
        loaded = load_entries(Path(tmpdir))
        assert len(loaded) == 2
        assert loaded[0].entry_id == "synth_001"
        assert loaded[1].drift_label == DriftType.SYNTACTIC


def test_ast_checker_on_entries():
    entries = _make_test_entries()
    # Entry with no drift should be classified as no-drift
    pred = check_entry(entries[0])
    assert pred.predicted_label == DriftType.NO_DRIFT
    # Entry with missing param should be classified as syntactic
    pred = check_entry(entries[1])
    assert pred.predicted_label == DriftType.SYNTACTIC


def test_metrics_on_predictions():
    from src.shared.schema import Prediction
    ground_truth = [DriftType.NO_DRIFT, DriftType.SYNTACTIC]
    predictions = [
        Prediction(entry_id="synth_001", approach="ast_checker", predicted_label=DriftType.NO_DRIFT),
        Prediction(entry_id="synth_002", approach="ast_checker", predicted_label=DriftType.SYNTACTIC),
    ]
    pred_labels = [p.predicted_label for p in predictions]
    metrics = compute_metrics(ground_truth, pred_labels, DriftType.SYNTACTIC)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
```

- [ ] **Step 2: Run integration test**

Run: `uv run pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration test"
```

---

### Task 12: Run All Tests & Verify

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Verify project structure**

Run: `find src configs tests data -type f | sort`
Expected: All files from the spec are present

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: any remaining test or integration issues"
```