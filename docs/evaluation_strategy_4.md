# Evaluation Strategy: How LLM and Non-LLM Approaches Produce Performance Metrics

## The Core Idea

Every entry in the dataset has a **ground truth** label (the correct answer). Every approach produces a **prediction**. You compare prediction vs. ground truth to compute metrics.

---

## Step 1: What the Dataset Gives You

Say you have 10 entries:

| Entry | Ground Truth |
|---|---|
| 1 | syntactic |
| 2 | semantic |
| 3 | no-drift |
| 4 | syntactic |
| 5 | semantic |
| 6 | no-drift |
| 7 | syntactic |
| 8 | no-drift |
| 9 | semantic |
| 10 | no-drift |

These labels are already in the dataset — either filled by annotators (real entries) or auto-filled (synthetic entries).

---

## Step 2: What Each Approach Produces

You run each approach on the same entries. Each approach gives you a **prediction** per entry.

### darglint (Non-LLM)

You point darglint at the source files. It parses each function, compares the docstring against the signature, and reports mismatches.

| Entry | darglint Output |
|---|---|
| 1 | "param `z` missing from docstring" → **syntactic** |
| 2 | no issues found → **no-drift** |
| 3 | no issues found → **no-drift** |
| 4 | "return type mismatch" → **syntactic** |
| 5 | no issues found → **no-drift** |
| 6 | no issues found → **no-drift** |
| 7 | no issues found → **no-drift** |
| 8 | no issues found → **no-drift** |
| 9 | no issues found → **no-drift** |
| 10 | no issues found → **no-drift** |

darglint caught 2 of 3 syntactic drifts, caught 0 of 3 semantic drifts. That's expected — it can't reason about behavior.

### LLM Zero-Shot

You send each entry's `code` + `docstring` as a prompt. The LLM responds with its assessment.

| Entry | LLM Output |
|---|---|
| 1 | "param `z` is missing from docstring" → **syntactic** |
| 2 | "docstring says product but code computes division" → **semantic** |
| 3 | "no issues" → **no-drift** |
| 4 | "return type mismatch" → **syntactic** |
| 5 | "behavior mismatch" → **semantic** |
| 6 | "no issues" → **no-drift** |
| 7 | "no issues" → **no-drift** |
| 8 | "param `x` missing" → **syntactic** (wrong — hallucination) |
| 9 | "behavior mismatch" → **semantic** |
| 10 | "no issues" → **no-drift** |

The LLM caught 2 of 3 syntactic drifts, caught 3 of 3 semantic drifts, but hallucinated one false positive on entry 8.

---

## Step 3: Compare Predictions vs. Ground Truth

For each drift type, count four outcomes:

|  | Ground Truth = Drift | Ground Truth = No-Drift |
|---|---|---|
| **Predicted = Drift** | True Positive (TP) | False Positive (FP) |
| **Predicted = No-Drift** | False Negative (FN) | True Negative (TN) |

### For Syntactic Drift (entries 1, 4, 7 are truth = syntactic; 8 is truth = no-drift)

**darglint:**
- TP = 2 (entries 1, 4) — correctly found
- FN = 1 (entry 7) — missed
- FP = 0 — no false alarms
- TN = 6 (all no-drift/semantic entries correctly left alone)

**LLM:**
- TP = 2 (entries 1, 4) — correctly found
- FN = 1 (entry 7) — missed
- FP = 1 (entry 8) — false alarm
- TN = 5

### For Semantic Drift (entries 2, 5, 9 are truth = semantic)

**darglint:**
- TP = 0, FN = 3, FP = 0 — can't detect semantic drift at all

**LLM:**
- TP = 3, FN = 0, FP = 0 — found all three

---

## Step 4: Compute Metrics

```
Precision = TP / (TP + FP)     →  "Of everything I flagged, how many were real?"
Recall    = TP / (TP + FN)     →  "Of everything that was real, how many did I find?"
F1        = 2 × (P × R) / (P + R)  →  harmonic mean of both
```

### Syntactic Drift

| Metric | darglint | LLM Zero-Shot |
|---|---|---|
| Precision | 2/2 = **1.00** | 2/3 = **0.67** |
| Recall | 2/3 = **0.67** | 2/3 = **0.67** |
| F1 | **0.80** | **0.67** |

### Semantic Drift

| Metric | darglint | LLM Zero-Shot |
|---|---|---|
| Precision | 0/0 = **N/A** | 3/3 = **1.00** |
| Recall | 0/3 = **0.00** | 3/3 = **1.00** |
| F1 | **0.00** | **1.00** |

**The story these numbers tell:** darglint is precise for syntactic drift but can't detect semantic drift at all. The LLM catches semantic drift but sometimes hallucinates syntactic false positives. This is exactly the kind of contrast that makes the dissertation contribution clear.

---

## The Full Process in Practice

The evaluation script would:

1. **Load** all entries from the dataset (with ground truth already in place)
2. **Run** darglint / AST checker on `source_files/`, parse their output into per-entry predictions
3. **Run** LLM prompts using `code` + `docstring` fields, parse responses into per-entry predictions
4. **Align** predictions to ground truth by `entry_id`
5. **Count** TP, FP, FN, TN for each drift type × each approach
6. **Compute** precision, recall, F1