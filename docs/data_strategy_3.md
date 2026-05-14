# Data Strategy: Dataset Structure, Annotation & Evaluation Flow

## Dataset Size Target: ~800 Entries

### Overall Breakdown

| Category | Count | Percentage |
|---|---|---|
| No-drift (consistent) | ~240 | 30% |
| Syntactic drift | ~280 | 35% |
| Semantic drift | ~280 | 35% |

### Split by Source

| Source | Count | Rationale |
|---|---|---|
| Real (git-mined) | ~250 | Manually annotated — this is the bottleneck |
| Synthetic | ~550 | Auto-labeled — cheap to generate at scale |

### Why These Numbers

**Minimum for statistical significance:** ~100-150 samples per drift type for McNemar's test and bootstrap confidence intervals to produce meaningful results. Below that, p-values become unreliable.

**Why not larger:** 500+ real entries would require 15-25 hours of annotation per person. 250 real entries is sufficient for ecological validity when combined with 550 synthetic entries.

**Why 30% no-drift:** If the dataset is all drift, false positives can't be measured realistically. Practitioners run these tools on entire codebases where most functions are fine — 30% no-drift approximates that.

### Detailed Breakdown — Real Entries (~250)

| Type | Count | How Obtained |
|---|---|---|
| No-drift | ~75 | Random well-documented functions with matching docs |
| Syntactic | ~90 | Git-mined: commits that fixed docstring signatures |
| Semantic | ~85 | Git-mined: commits that fixed behavioral descriptions |

**Annotation effort:** 250 entries × ~3 min × 2 annotators ≈ 25 hours per annotator. Spread over 2-3 weeks, this is manageable.

### Detailed Breakdown — Synthetic Entries (~550)

| Type | Count | How Obtained |
|---|---|---|
| No-drift | ~165 | Unmodified well-documented functions |
| Syntactic | ~190 | Auto-mutated (remove param, change type, add phantom param) |
| Semantic | ~195 | Auto-mutated (alter behavioral description, omit exceptions) |

**No manual annotation needed** — the mutation script knows exactly what it changed.

### Why Not Smaller or Larger?

| Size | Problem |
|---|---|
| < 300 | Statistical tests unreliable, reviewers may question robustness |
| 300-500 | Acceptable for a thesis, but weaker for publication |
| **500-1000** | **Sweet spot — rigorous enough, feasible to build** |
| > 1500 | Diminishing returns, annotation becomes a project unto itself |

### Pilot Before Scaling

Start with a **pilot of ~50 entries** (10 no-drift, 20 syntactic, 20 semantic) to:
- Validate annotation guidelines
- Test the evaluation pipeline end-to-end
- Estimate annotation time accurately
- Catch issues before scaling to the full 800

## Dataset Structure

Each entry represents a single **function/method + its docstring** as a unit of analysis:

```
dataset/
├── manifest.json              # Master index of all entries
├── entries/
│   ├── entry_001.json
│   ├── entry_002.json
│   ├── ...
└── source_files/              # Original .py files for baseline tools
    ├── repo_name/
    │   ├── module_path/
    │   │   └── original.py    # Unmodified source (for non-LLM tools)
    │   │   └── mutated.py     # Synthetic drift injected version
    │   └── ...
    └── ...
```

### Individual Entry Schema

```json
{
  "entry_id": "entry_001",
  "source": "real",
  "origin_repo": "flask",
  "origin_commit": "a1b2c3d",
  "origin_file": "flask/app.py",
  "origin_function": "run",

  "code": "def run(self, host=None, port=None, debug=None, load_dotenv=True):\n    ...",

  "docstring": "Runs the application on the local development server.",

  "full_source": "def run(self, host=None, port=None, debug=None, load_dotenv=True):\n    \"\"\"Runs the application on the local development server.\n    \n    Args:\n        host: The hostname to listen on.\n        port: The port of the web server.\n        debug: Enable debug mode.\n    \"\"\"\n    ...",

  "drift_label": "syntactic",
  "drift_present": true,

  "drift_details": {
    "type": "syntactic",
    "description": "Parameter 'load_dotenv' is not documented in Args section",
    "missing_params": ["load_dotenv"],
    "extra_params_in_doc": [],
    "type_mismatches": []
  },

  "ground_truth_annotation": {
    "annotator_1": "syntactic",
    "annotator_2": "syntactic",
    "agreement": true
  }
}
```

### Field Breakdown

| Field | Purpose | Used by |
|---|---|---|
| `code` | Function body without docstring | LLM prompt construction |
| `docstring` | Isolated docstring text | LLM prompt construction |
| `full_source` | Complete function with docstring embedded | AST checkers, darglint |
| `drift_label` | Ground truth: `syntactic`, `semantic`, or `no-drift` | Evaluation |
| `drift_present` | Binary: drift exists or not | Evaluation |
| `drift_details` | Structured breakdown of what's wrong | Error analysis |
| `source` | `real` (git-mined) or `synthetic` | Dataset analysis |
| `origin_*` | Provenance for real entries | Reproducibility |
| `ground_truth_annotation` | Inter-annotator agreement | Validity |

### Why Both `code`+`docstring` and `full_source`

- **LLM approaches** use `code` and `docstring` separately — the prompt presents them as distinct inputs for comparison
- **Non-LLM tools** (darglint, AST checker) need `full_source` — they parse the original file and compare docstring against signature internally

---

## Ground Truth Annotation

### Why It Matters

In empirical research, dataset labels must be proven reliable, not just one person's opinion. If only one person labels the data, a reviewer can argue the labels are biased.

### How It Works

Two independent humans (annotator_1 and annotator_2) each look at the same code+docstring pair and independently assign a drift label (`syntactic`, `semantic`, or `no-drift`) without seeing each other's answer.

| Step | Action |
|---|---|
| **1** | Both annotators independently label the same entry |
| **2** | If they agree → label is accepted as-is |
| **3** | If they disagree → a discussion resolves it (or a third annotator breaks the tie) |
| **4** | Compute **Cohen's Kappa** across all entries — this measures agreement beyond chance |

### Cohen's Kappa Interpretation

| Kappa Value | Agreement Level |
|---|---|
| < 0.20 | Poor |
| 0.21 – 0.40 | Fair |
| 0.41 – 0.60 | Moderate |
| 0.61 – 0.80 | Substantial |
| 0.81 – 1.00 | Almost perfect |

A kappa above 0.61 is generally considered acceptable for a dissertation. Report this in the evaluation chapter.

### Who Should the Annotators Be

You (as researcher) + one other person (another PhD student, supervisor, or a developer). They need to understand Python and docstrings, but they don't need to be domain experts in the specific repo.

---

## Who Provides drift_label and drift_details

### For Synthetic Entries — Automated, No Manual Work

The mutation script injects drift. Since the script designed the mutation, it knows exactly what changed and auto-fills the fields:

```json
{
  "source": "synthetic",
  "drift_label": "syntactic",
  "drift_present": true,
  "drift_details": {
    "type": "syntactic",
    "description": "Parameter 'z' removed from docstring",
    "missing_params": ["z"],
    "extra_params_in_doc": [],
    "type_mismatches": []
  },
  "ground_truth_annotation": null
}
```

`ground_truth_annotation` is `null` for synthetic entries because the label is deterministic — the drift was created by design, so the answer is certain.

### For Real (Git-Mined) Entries — Manual Annotation Required

Workflow:

```
1. Mining script identifies candidate entries
   (commits where code changed but docs didn't)

2. Script extracts code + docstring and creates stub entries:
   {
     "drift_label": null,          ← empty, needs human
     "drift_details": null,        ← empty, needs human
     "drift_present": null         ← empty, needs human
   }

3. You + a second annotator independently review each entry
   and fill in drift_label, drift_details, drift_present

4. Compare annotations, resolve disagreements,
   compute Cohen's Kappa

5. Final dataset has agreed-upon labels
```

Estimated effort: 200-500 real instances × ~2-3 minutes each ≈ 7-25 hours per annotator. Manageable within a weekend or two.

### Summary

| Entry Source | drift_label | drift_details | ground_truth_annotation |
|---|---|---|---|
| **Synthetic** | Auto-filled by mutation script | Auto-filled by mutation script | `null` (not needed) |
| **Real** | Filled manually by 2 annotators | Filled manually by 2 annotators | Both annotators' labels + agreement |

---

## Can Both LLM and Non-LLM Approaches Run on the Same Dataset?

Yes, with one caveat.

### Non-LLM Baselines

| Tool | Input Needed | Works on Dataset? |
|---|---|---|
| **darglint** | `.py` source files | Yes — point it at `source_files/` directory |
| **AST checker** | `.py` source files | Yes — parse `full_source` from entries |
| **Git heuristic** | Git history of repos | Partially — needs live repo clones, not just snapshots |

**Caveat:** darglint and AST checkers run on **source files**, not on isolated JSON entries. The `.py` files in `source_files/` exist for this reason.

### LLM Approaches

| Strategy | Input Needed | Works on Dataset? |
|---|---|---|
| **Zero-shot** | Prompt with code + docstring | Yes — constructed from `code` + `docstring` fields |
| **Few-shot** | Prompt with examples + target | Yes — pick entries as few-shot examples |
| **Chain-of-thought** | Prompt with reasoning instructions | Yes — constructed from `code` + `docstring` fields |

### The Git Heuristic Baseline

This operates on **commit history**, not individual function entries. Run it separately during the mining phase and record its results as a separate baseline — it doesn't operate on the final dataset directly.

---

## Evaluation Flow

```
                    ┌─────────────────┐
                    │   Dataset        │
                    │ (entries + files)│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──────┐  ┌───▼────────┐  ┌──▼─────────┐
    │  Non-LLM Tools │  │ LLM Prompt  │  │ Git        │
    │  (darglint,    │  │ Builder     │  │ Heuristic  │
    │   AST checker) │  │             │  │ (separate) │
    └────────┬───────┘  └───┬────────┘  └───┬────────┘
             │              │               │
             │         ┌────▼────┐          │
             │         │ LLM API │          │
             │         └────┬────┘          │
             │              │               │
    ┌────────▼──────────────▼───────────────▼──────┐
    │           Evaluation Harness                  │
    │  Compare all outputs against ground truth     │
    │  (precision, recall, F1, drift-type accuracy) │
    └───────────────────────────────────────────────┘
```