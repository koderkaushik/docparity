# Missing Aspects to Pre-Consider

Areas not yet covered in the existing strategy documents that will matter for the dissertation.

---

## 1. Prompt Design Details

Zero-shot, few-shot, and CoT are identified as strategies, but the **actual prompt wording** significantly affects results. Small phrasing changes can shift LLM accuracy.

- Define a fixed prompt template for each strategy
- Document the exact wording in the dissertation
- Consider running a **prompt sensitivity analysis** — try 2-3 phrasings per strategy to show results aren't an artifact of one lucky prompt

---

## 2. LLM Model Selection

Which model(s) to evaluate matters:

- **Claude (Opus/Sonnet)**, **GPT-4**, **open-source (Llama, Mistral, CodeLlama)** — each has different code understanding capabilities
- Minimum: test **2 models** (one proprietary, one open-source) to show findings generalize beyond one LLM
- Fix and report exact model version for reproducibility

---

## 3. Negative Examples (No-Drift Entries)

The dataset needs entries where code and docs are **consistent**. Without these, false positives can't be measured meaningfully. Aim for roughly:

- 30-40% no-drift entries
- 30-35% syntactic drift
- 30-35% semantic drift

This ratio prevents the dataset from being skewed and gives realistic precision numbers.

---

## 4. Statistical Significance

Reporting "LLM got F1=0.85, darglint got F1=0.60" isn't enough. Show the difference isn't due to chance:

- Use **McNemar's test** or **bootstrap confidence intervals** on paired predictions
- Report p-values or 95% CI alongside F1 scores

---

## 5. Context Window and Function Size

What happens when a function is too long for the LLM's context? Or when semantic drift requires understanding surrounding code (e.g., a helper function defined elsewhere)?

- Define a **size cutoff** (e.g., max 200 lines per entry)
- Decide: provide the function only, or include surrounding context (imports, class definition, helper calls)?

---

## 6. Cost and Latency Comparison

Beyond accuracy, practitioners care about practical tradeoffs:

| Dimension | darglint | LLM |
|---|---|---|
| Cost per function | Free | ~$0.01-0.05 per API call |
| Time per function | <1ms | 1-5 seconds |
| Setup complexity | pip install | API key + prompt engineering |

This makes the Discussion chapter practical and relevant.

---

## 7. Output Standardization

Each tool produces output in different formats:

- **darglint** outputs text warnings
- **LLM** outputs natural language
- **AST checker** outputs structured data

A **normalization layer** is needed — a script that converts each tool's raw output into a standard format: `{entry_id, predicted_label: syntactic|semantic|no-drift}`. This is what feeds into the evaluation.

---

## 8. Reproducibility Protocol

Fix and document these before running experiments:

| Parameter | What to Fix |
|---|---|
| LLM model + version | e.g., `gpt-4-0613` |
| Temperature | 0 (deterministic) |
| Random seed | For any sampling in dataset construction |
| Prompt templates | Version-controlled, exact wording frozen |
| API logs | Save all prompts + responses for audit |

---

## Summary of Coverage

| Area | Covered? | Priority |
|---|---|---|
| Drift definitions | Yes | — |
| Dataset structure | Yes | — |
| Evaluation metrics | Yes | — |
| Annotation process | Yes | — |
| Prompt design details | No | High |
| LLM model selection | No | High |
| No-drift negative examples | No | High |
| Statistical significance testing | No | High |
| Context/size handling | No | Medium |
| Cost/latency comparison | No | Medium |
| Output normalization | No | Medium |
| Reproducibility protocol | No | Medium |