# DocParity Pipeline Design

**Date:** 2026-05-14
**Status:** Approved

## Overview

DocParity is a dissertation research project evaluating LLM-based documentation drift detection against non-LLM baselines in Python projects. This spec defines the implementation architecture for the data pipeline, detection pipeline, and evaluation pipeline.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| LLM provider | Ollama (local open-source models) | Cost-effective for dissertation, factory pattern allows adding providers later |
| Initial models | Start with local Ollama models (Llama 3, Mistral), extend to Ollama cloud models (GLM, Kimi) | Factory pattern supports adding providers; start small, extend later |
| Repos | 10-15 popular Python repos from strategy doc | Proven, stable, good docstring coverage |
| Python version | 3.11+ | Modern syntax, wide library support |
| Package manager | uv | Fast, lockfile support, reproducibility |
| Config format | YAML | Human-readable, standard for research configs |
| Architecture | Phase-driven modular pipeline | Matches dissertation phases, independently runnable scripts |
| Data interface | Shared `data/` directory with JSON entries | Simple, debuggable, matches strategy doc schema |

## Project Structure

```
docparity/
├── configs/
│   ├── models.yaml              # LLM model configs (provider, model name, params)
│   ├── prompts.yaml             # Prompt templates (zero-shot, few-shot, CoT)
│   ├── dataset.yaml             # Dataset generation params (sizes, repos, splits)
│   └── evaluation.yaml          # Evaluation settings (metrics, significance tests)
├── src/
│   ├── mining/
│   │   ├── repo_cloner.py       # Clone target repos
│   │   ├── drift_miner.py       # Mine drift instances from git history
│   │   └── no_drift_sampler.py  # Sample consistent code-docs pairs
│   ├── generation/
│   │   ├── mutation_engine.py   # Apply drift mutations to docstrings
│   │   ├── syntactic_mutators.py   # Parameter/type mutations
│   │   └── semantic_mutators.py     # Behavioral description mutations
│   ├── baselines/
│   │   ├── darglint_runner.py   # Run darglint on source files
│   │   ├── ast_checker.py       # Custom AST signature comparison
│   │   └── git_heuristic.py     # Code-changed-docs-didn't heuristic
│   ├── llm/
│   │   ├── factory.py           # Model factory (Ollama + future providers)
│   │   ├── prompt_builder.py    # Construct prompts from entries + templates
│   │   ├── detector.py          # Run LLM detection pipeline
│   │   └── response_parser.py   # Parse LLM output to structured predictions
│   ├── evaluation/
│   │   ├── metrics.py           # Precision, recall, F1 per drift type
│   │   ├── significance.py      # McNemar's test, bootstrap CI
│   │   └── reporter.py          # Generate results tables and error analysis
│   └── shared/
│       ├── schema.py            # Entry, Prediction, DriftLabel dataclasses
│       └── dataset_io.py        # Load/save dataset entries
├── data/
│   ├── repos/                   # Cloned git repos (gitignored)
│   ├── entries/                 # JSON entry files
│   ├── source_files/            # .py files for baseline tools
│   └── manifest.json            # Master index
├── results/                     # Evaluation output (CSV, tables)
├── tests/
└── pyproject.toml
```

## Shared Data Schema

### DriftType Enum

```python
class DriftType(Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    NO_DRIFT = "no-drift"
```

### Entry Dataclass

Matches the dataset schema from `data_strategy_3.md`:

```python
@dataclass
class Entry:
    entry_id: str
    source: str                          # "real" or "synthetic"
    origin_repo: str
    origin_commit: str | None
    origin_file: str
    origin_function: str
    code: str                            # function body without docstring
    docstring: str                        # isolated docstring text
    full_source: str                       # complete function with docstring
    drift_label: DriftType | None
    drift_present: bool | None
    drift_details: DriftDetails | None
    ground_truth_annotation: dict | None  # null for synthetic entries
```

### DriftDetails Dataclass

```python
@dataclass
class DriftDetails:
    type: DriftType
    description: str
    severity: str | None                  # optional: "low", "medium", "high"
    missing_params: list[str]             # params in code but not docs
    extra_params_in_doc: list[str]        # params in docs but not code
    type_mismatches: list[dict]            # param/return type conflicts
    behavioral_mismatches: list[str]       # description vs. logic conflicts
```

### Prediction Dataclass

The normalization layer — every tool's output gets converted to this format:

```python
@dataclass
class Prediction:
    entry_id: str
    approach: str                         # "darglint", "ast_checker", "llm-zero-shot", etc.
    predicted_label: DriftType
    predicted_details: dict | None         # approach-specific output
    raw_output: str | None                # original tool/LLM output for audit
```

## Component Designs

### Mining Pipeline

**repo_cloner.py** — Reads repo list from `configs/dataset.yaml`, clones them to `data/repos/`.

**drift_miner.py** — Two strategies:
1. **Doc-fix commits**: `git log --grep="doc|docstring|documentation"` — the pre-fix state is confirmed drift
2. **Code-changed-docs-didn't**: Find commits where function code changed but docstring didn't update within a time window

For each instance, extracts the function, its docstring, and labels the drift type based on the nature of the mismatch.

**no_drift_sampler.py** — Randomly samples well-documented functions where darglint reports no issues and no recent doc-fix commits exist.

### Synthetic Generation

**mutation_engine.py** — Takes a clean (no-drift) function and applies a mutation to produce a drifted version. Selects a mutator based on the target drift type.

**Syntactic mutators** (applied to docstring only):
- Remove a parameter from the Args section
- Rename a parameter in the docstring (e.g., `x` becomes `x_coord`)
- Change a parameter's documented type
- Add a phantom parameter not in the signature
- Change the documented return type

**Semantic mutators** (applied to docstring only):
- Replace a behavioral keyword ("multiply" with "divide")
- Remove documented exception/side-effect
- Add an incorrect behavioral claim
- Change the described purpose to something plausible but wrong

Each mutation auto-fills `drift_label`, `drift_details`, and sets `ground_truth_annotation` to `null`.

### Baseline Pipeline

**darglint_runner.py** — Runs darglint on `data/source_files/`, parses text output into `Prediction` objects. Maps darglint's findings to `syntactic` or `no-drift` (darglint cannot detect semantic drift).

**ast_checker.py** — Custom script that parses each function's AST signature and compares against the docstring's Args/Returns section. Produces structured predictions for syntactic mismatches.

**git_heuristic.py** — Runs during the mining phase. Records which functions had code changes without docstring changes. Maps to `syntactic` or `semantic` labels heuristically.

### LLM Detection Pipeline

**factory.py** — Abstract model provider interface with concrete Ollama implementation:

```python
class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, config: dict) -> str: ...

class OllamaProvider(ModelProvider):
    def __init__(self, model_name: str): ...
    def generate(self, prompt: str, config: dict) -> str: ...
```

Adding a new provider means implementing one class.

**prompt_builder.py** — Reads prompt templates from `configs/prompts.yaml`, fills in `code` and `docstring` fields from the entry.

**detector.py** — Iterates over entries, builds prompts, calls the model provider, collects responses.

**response_parser.py** — Parses LLM responses into structured `Prediction` objects. Primarily uses JSON mode to extract drift type and description. Falls back to regex extraction if the LLM doesn't produce valid JSON. Logs unparsable responses for manual review.

### Evaluation Pipeline

**metrics.py** — Computes precision, recall, F1 per drift type per approach, plus overall metrics.

**significance.py** — McNemar's test for pairwise comparison, bootstrap confidence intervals.

**reporter.py** — Generates the comparison matrix table, plus error analysis (FP/FN breakdowns, misclassification patterns).

## Configuration

### configs/models.yaml

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

### configs/prompts.yaml

```yaml
zero_shot:
  system: "You are a documentation drift detector..."
  template: |
    Compare the following Python function code with its docstring.
    Identify any inconsistencies.

    Code:
    {code}

    Docstring:
    {docstring}

    Respond in JSON: {"drift_type": "syntactic|semantic|no-drift", "description": "..."}

few_shot:
  system: "You are a documentation drift detector..."
  template: |
    Here are examples of documentation drift detection:
    {examples}

    Now analyze:
    Code:
    {code}

    Docstring:
    {docstring}

    Respond in JSON: {"drift_type": "syntactic|semantic|no-drift", "description": "..."}

chain_of_thought:
  system: "You are a documentation drift detector..."
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

    Respond in JSON: {"drift_type": "syntactic|semantic|no-drift", "description": "...", "reasoning": "..."}
```

### configs/dataset.yaml

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

### configs/evaluation.yaml

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

## Development Phases

| # | Phase | Description |
|---|---|---|
| 1 | Project scaffold | pyproject.toml, directory structure, shared schema, config files |
| 2 | Mining pipeline | repo_cloner, drift_miner, no_drift_sampler |
| 3 | Synthetic generation | mutation_engine, syntactic_mutators, semantic_mutators |
| 4 | Pilot dataset | Run on 50 entries, validate schema and pipeline end-to-end |
| 5 | Baseline runners | darglint_runner, ast_checker, git_heuristic |
| 6 | LLM pipeline | factory, prompt_builder, detector, response_parser |
| 7 | Evaluation harness | metrics, significance, reporter |
| 8 | Full evaluation run | All entries, all approaches |
| 9 | Error analysis | FP/FN breakdown, comparison matrix, results |