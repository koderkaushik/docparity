# DocParity Pipeline — Implementation Progress

**Last updated:** 2026-05-14

## Completed

All core pipeline modules are implemented and tested (46 tests, all passing).

### Infrastructure
- Project scaffold: `pyproject.toml`, uv, directory structure, configs
- Shared schema: `DriftType`, `Entry`, `DriftDetails`, `Prediction` dataclasses
- Dataset I/O: JSON serialization, manifest management, save/load entries

### Mining Pipeline
- `repo_cloner.py` — Clone target repos from YAML config
- `function_extractor.py` — AST-based extraction of functions with docstrings
- `drift_miner.py` — Classify drift type, find doc-fix commits
- `no_drift_sampler.py` — Sample consistent code-doc pairs

### Synthetic Generation
- `mutation_engine.py` — Apply random mutations to create drifted entries
- `syntactic_mutators.py` — 5 mutators: remove param, rename param, change type, add phantom, change return type
- `semantic_mutators.py` — 4 mutators: replace keyword, remove exception, add claim, change purpose

### Baseline Runners
- `darglint_runner.py` — Run darglint, parse output, map to predictions
- `ast_checker.py` — Compare AST signature vs docstring params
- `git_heuristic.py` — Classify commit messages for drift detection

### LLM Detection Pipeline
- `factory.py` — ModelProvider ABC + OllamaProvider + factory function
- `prompt_builder.py` — Build prompts from YAML templates
- `response_parser.py` — JSON parse → regex fallback for LLM responses
- `detector.py` — Orchestrate LLM drift detection over entries

### Evaluation
- `metrics.py` — Precision, recall, F1 per drift type, confusion matrix
- `significance.py` — McNemar's test, bootstrap CI
- `reporter.py` — Comparison table, error analysis, CSV export

## Next Steps

### 1. Dataset Construction (Phase 2 from dissertation plan)
- Clone the 10 target Python repos using repo_cloner
- Mine real drift instances from git history (aim for ~250)
- Sample no-drift entries
- Generate synthetic entries using mutation engine (~550)
- Assemble dataset into `data/entries/` with manifest

### 2. Pilot Validation
- Create 50-entry pilot dataset (10 no-drift, 20 syntactic, 20 semantic)
- Run all baselines on pilot
- Run LLM detection on pilot with at least one model
- Validate evaluation pipeline end-to-end

### 3. Full Evaluation Run
- Scale to ~800 entries
- Run all baselines + all LLM strategies across 4 models
- Compute final metrics and significance tests
- Generate error analysis and comparison tables

### 4. Dissertation Writing
- Results chapter with comparison matrix
- Discussion on where LLMs add value vs. static tools
- Threats to validity