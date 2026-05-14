# Step-by-Step Dissertation Strategy

## Scope Decision

This study focuses on **two drift types**: syntactic and semantic. Completeness and structural drift are acknowledged but excluded from the evaluation scope, noted as future work.

**Rationale:** Syntactic and semantic sit at opposite ends of the detection-difficulty spectrum. This contrast is the core contribution — static tools handle syntactic drift well, but semantic drift requires behavioral reasoning where LLMs may add value. Completeness drift (undocumented or phantom elements) is treated as a sub-case of syntactic drift in this study.

---

## Phase 1: Foundation (Weeks 1-4)

### Step 1: Refine the Research Questions
- **RQ1:** How frequently do syntactic and semantic code-documentation drifts occur in Python projects?
- **RQ2:** How effectively can LLMs detect syntactic and semantic drift compared to existing non-LLM tools?
- **RQ3:** What are the limitations and failure modes of LLM-based drift detection?

### Step 2: Literature Review
Systematic review covering three streams:
- **Documentation drift / code-comment consistency** — Tan et al., 2007; Steidl et al., 2013; Wen et al., 2018
- **LLMs for code understanding** — CodeBERT, Codex, GPT-based analysis tools
- **Automated documentation quality tools** — darglint, pydocstyle, doxygen, academic frameworks

Deliverable: A literature review chapter or technical report.

### Step 3: Finalize the Drift Definitions

#### Syntactic Drift
A discrepancy between the **formal interface** documented (parameter names, types, return types, raised exceptions) and the **actual code signature**, where the mismatch can be detected through structural comparison without requiring behavioral understanding of the code.

```python
# Code
def compute(x: int, y: int, z: int = 0) -> float:
    ...

# Docstring — Syntactic Drift
"""Compute something.

Args:
    x (int): The first value.
    y (int): The second value.

Returns:
    int: The result.
"""
# z missing from docs, return type documented as int but signature says float
```

**Key property:** Detectable by comparing the docstring's declared interface against the AST/parsed signature — no execution or reasoning about behavior needed.

#### Semantic Drift
A discrepancy between the **behavioral description** in documentation and the **actual runtime behavior** of the code, where the documented interface may be syntactically correct but the described logic, side effects, or guarantees diverge from what the code implements.

```python
# Code
def compute(x: int, y: int) -> int:
    if y == 0:
        raise ValueError("y must be non-zero")
    return x // y

# Docstring — Semantic Drift
"""Compute something.

Args:
    x (int): The first value.
    y (int): The second value.

Returns:
    int: The product of x and y.
"""
# Doc says "product" but code computes integer division;
# doc doesn't mention the ValueError when y == 0
```

**Key property:** The signature matches — you need to **read and understand the code logic** to detect this. A static signature checker would miss it entirely.

#### Out-of-Scope Drift Types (Acknowledged, Not Evaluated)
- **Completeness drift** — Code elements undocumented or docs describe unimplemented elements (treated as a sub-case of syntactic drift in this study)
- **Structural drift** — Documentation references modules/classes that have been reorganized or removed
- **Temporal drift** — Documentation references deprecated or obsolete patterns

These are discussed in Related Work and noted as future work.

#### Boundary Summary

| Drift Type | What mismatches | Detection level | Example trigger |
|---|---|---|---|
| **Syntactic** | Declared interface vs. actual signature | Structural comparison | Wrong param name/type in doc |
| **Semantic** | Described behavior vs. actual behavior | Behavioral reasoning | Doc says "product", code divides |

**Detection difficulty hierarchy:** Syntactic < Semantic

---

## Phase 2: Dataset Construction (Weeks 5-10)

### Step 4: Select Target Repositories
Pick 10-15 popular, well-documented Python repos (e.g., Django, Flask, Requests, scikit-learn, FastAPI, pandas, numpy, matplotlib, pytest, click).

Criteria: active maintenance, good docstring coverage, public git history.

### Step 5: Mine Real Drift Instances from Git History
- Write scripts to identify commits where code changed but docstrings didn't
- Grep for "documentation fix" / "docstring fix" commits — the pre-fix state = confirmed drift
- Manually validate and label a sample (aim for 200-500 instances)
- Label each instance as syntactic or semantic drift

### Step 6: Generate Synthetic Drift
- Take well-documented functions/classes
- Systematically mutate docs per the two drift types:
  - **Syntactic:** remove/rename a parameter in the docstring, change return type, add non-existent parameter
  - **Semantic:** change the described behavior, add incorrect behavioral claims, omit documented exceptions/side effects
- Aim for 500-1000 synthetic instances with known ground truth

### Step 7: Build a Clean Evaluation Dataset
Combine real + synthetic instances. Structure as:
- Code snippet
- Documentation snippet
- Drift type label (syntactic / semantic / no-drift)
- Drift severity (optional)

This dataset is itself a dissertation contribution.

---

## Phase 3: Baseline & LLM Pipeline (Weeks 11-16)

### Step 8: Implement Non-LLM Baselines
- **darglint** — run on target repos, collect its findings (syntactic baseline)
- **Git-history heuristic** — code changed within N commits but docs didn't (semantic-ish baseline)
- **AST signature checker** — simple custom script comparing function signatures to docstring params (syntactic baseline)

Record precision, recall, and which drift types each baseline can/cannot detect.

### Step 9: Design the LLM-Based Detection Pipeline
Two main design decisions:

**a) Input format** — How to present code+docs to the LLM?
- Raw code block with docstring
- Structured prompt (function signature + docstring separated)
- Few-shot examples included or not

**b) Prompting strategy:**
- Zero-shot: "Is this docstring consistent with this function? If not, explain the drift."
- Few-shot: Provide labeled examples of each drift type
- Chain-of-thought: Ask the LLM to reason through the comparison step by step

### Step 10: Implement the Pipeline
- Build a Python tool that extracts functions + docstrings
- Constructs prompts per the chosen strategy
- Calls the LLM API (e.g., Claude/GPT-4)
- Parses LLM responses into structured drift reports (type, location, description)

---

## Phase 4: Evaluation (Weeks 17-22)

### Step 11: Run Evaluation
For each approach (baselines + LLM variants), measure on the dataset:
- **Precision** — Of reported drifts, how many are real?
- **Recall** — Of real drifts, how many were detected?
- **F1** — Balance between the two
- **Drift-type accuracy** — Did the tool correctly classify the drift type (syntactic vs. semantic)?

### Step 12: Error Analysis
Critical for a dissertation. For every failure case:
- **False positives** — LLM says drift exists but it doesn't. Why? (hallucination, misinterpretation?)
- **False negatives** — Drift exists but LLM missed it. Why? (too subtle, lacks context?)
- **Type misclassification** — Drift detected but wrong type assigned (syntactic vs. semantic). Why?

This is where the limitations are discovered — committees value this.

### Step 13: Compare Across Drift Types
Build a results matrix:

| Approach | Syntactic Precision | Syntactic Recall | Syntactic F1 | Semantic Precision | Semantic Recall | Semantic F1 |
|---|---|---|---|---|---|---|
| darglint | ? | ? | ? | ? | ? | ? |
| AST checker | ? | ? | ? | ? | ? | ? |
| Git heuristic | ? | ? | ? | ? | ? | ? |
| LLM zero-shot | ? | ? | ? | ? | ? | ? |
| LLM few-shot | ? | ? | ? | ? | ? | ? |
| LLM CoT | ? | ? | ? | ? | ? | ? |

This directly answers RQ2 and shows where LLMs add value vs. where simpler tools suffice.

---

## Phase 5: Writing & Defense (Weeks 23-30)

### Step 14: Write the Dissertation
Suggested chapter structure:
1. **Introduction** — Problem, motivation, research questions
2. **Related Work** — Literature review (including completeness, structural, temporal drift as out-of-scope)
3. **Drift Definitions** — Syntactic and semantic drift with formal criteria and examples
4. **Dataset Construction** — Methodology for mining + synthetic generation
5. **Methodology** — Baselines + LLM pipeline design
6. **Evaluation** — Results, comparison matrix, error analysis
7. **Discussion** — When do LLMs help? When don't they? Implications for practice.
8. **Threats to Validity** — Internal (labeling bias), external (Python-only, two drift types), construct (prompt sensitivity)
9. **Conclusion & Future Work** — Extending to completeness, structural, and temporal drift

### Step 15: Prepare for Defense
- Anticipate questions on generalizability beyond Python and beyond two drift types
- Be ready to discuss why syntactic + semantic is sufficient for a first study
- Be ready to discuss cost/latency tradeoffs of LLMs vs. static tools
- Have a clear "so what" — practical takeaways for developers and tool builders

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM API costs add up | Start with a small pilot (50-100 samples) before scaling |
| Manual labeling is slow | Use 2 annotators + disagreement resolution; or start with synthetic data |
| Reproducibility concerns | Fix model version, log all prompts/responses, set temperature=0 |
| Scope creep | Stick to syntactic + semantic drift; Python only; docstrings only (not READMEs/wikis) |
| Committee pushes on limited drift types | Completeness is a sub-case of syntactic; structural/temporal are noted as future work with clear rationale |