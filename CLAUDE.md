# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DocParity is a dissertation research project investigating **LLM-Assisted Documentation Drift Detection** — an empirical evaluation of code-documentation consistency in Python projects.

## Research Scope

- **Two drift types under study:** syntactic (signature/interface mismatches) and semantic (behavioral description vs. actual code logic)
- **Language focus:** Python docstrings
- **Out-of-scope but acknowledged:** completeness, structural, and temporal drift (noted as future work)

## Documentation Structure

All research planning lives in `docs/`:

- `initial_exploration_1.md` — Topic suitability and early decisions
- `step_by_step_strategy_2.md` — Full dissertation plan (5 phases, 15 steps), drift definitions, RQs
- `data_strategy_3.md` — Dataset schema, size targets (~800 entries), annotation protocol, evaluation flow
- `evaluation_strategy_4.md` — How LLM and non-LLM outputs are compared to ground truth for metrics
- `missing_aspects_5.md` — Gaps to address: prompt design, model selection, stat significance, etc.

When modifying strategy docs, preserve the numbering convention (filename contains sequence number).

## Key Decisions

- Dataset: ~800 entries total (~250 real git-mined + ~550 synthetic), 30% no-drift / 35% syntactic / 35% semantic
- Baselines: darglint (syntactic), AST signature checker (syntactic), git-history heuristic (semantic-ish)
- LLM strategies: zero-shot, few-shot, chain-of-thought
- Metrics: precision, recall, F1 per drift type; McNemar's test or bootstrap CI for significance
- Annotation: 2 independent annotators + Cohen's Kappa for real entries; auto-labeled for synthetic