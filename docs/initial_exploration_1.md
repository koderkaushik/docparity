# Initial Exploration - Dissertation Topic Discussion

## Topic

**LLM-Assisted Documentation Drift Detection: An Empirical Evaluation of Code-Documentation Consistency**

---

## Suitability Assessment

### Strengths

- **Timely and relevant** — Documentation drift is a well-documented practical problem (studies show outdated docs waste developer time and introduce bugs), and applying LLMs to it is a hot but not yet saturated area.
- **Clear research gap** — Most prior work on code-documentation consistency uses rule-based or heuristic approaches. LLM-based detection is under-explored empirically, so there's room for a meaningful contribution.
- **Sound methodology** — "Empirical evaluation" signals the work will be grounded in real data and measurable results, which is exactly what committees look for.
- **Feasible scope** — Can be scoped up or down: from a focused benchmark study to a full tool prototype with user evaluation.

### Things to Strengthen

- **Define "drift" precisely** — Is it syntactic (API signatures changed but docs weren't updated), semantic (behavioral mismatches), or both? Being specific will sharpen the contribution.
- **Baseline comparison** — Compare against non-LLM approaches (e.g., diff-based heuristics, rule checkers) so the "LLM-assisted" part is empirically justified, not assumed.
- **Evaluation rigor** — A labeled dataset of code-documentation pairs with ground-truth inconsistencies is key. If none exists, creating one *is* a contribution.

### Potential Concern

- Committees may push on generalizability — define the domain (e.g., Python libraries, REST APIs, specific languages/frameworks) rather than making vague claims about "all documentation."

**Verdict:** Well-chosen topic with real-world impact and clear academic contribution.

---

## Doubt 1: Drift Definition — Beyond Syntactic and Semantic

Additional categories of drift beyond syntactic and semantic:

| Type | Description | Example |
|---|---|---|
| **Completeness drift** | Code features/params exist but aren't documented (or docs describe features absent from code) | Function has 5 parameters but docs only list 3 |
| **Structural drift** | Doc organization doesn't match code architecture | Docs describe a module that was renamed or removed |
| **Temporal drift** | Docs reference outdated versions, deprecated features, or obsolete patterns | "Use `urllib2`" when code has migrated to `requests` |
| **Behavioral drift** | Docs describe the happy path but miss error handling, side effects, or edge cases the code covers | Doc says "returns a list" but code can also return `None` |

**Suggested taxonomy framing:** syntactic → semantic → pragmatic (where pragmatic covers completeness, behavioral, temporal). This gives a nice escalation from "easy to detect mechanically" to "requires understanding."

---

## Doubt 2: Non-LLM Baselines for Comparison

### Python-specific Tools

- **darglint** — Checks that docstring parameters/return values match function signatures. Purely syntactic baseline.
- **pydocstyle** — Enforces PEP 257 docstring conventions. Style-level only.
- **interrogate** — Checks docstring coverage (presence/absence), not content accuracy.

### Academic / General Approaches

- **AST-based diff approaches** — Parse code and docstrings into ASTs and compare structural consistency. Academic papers include *Michail & Notkin, 1999* on code-comment consistency; more recent work by *Murta et al.* on API evolution tracking.
- **Git-history heuristic** — Code changed but docs didn't within N commits (semantic-ish baseline).

**Recommended baseline strategy:** Use **darglint** as the syntactic baseline (most direct non-LLM comparator for parameter/signature mismatches) and a simple **git-history heuristic** as a semantic-ish baseline.

---

## Doubt 3: Dataset for Code-Documentation Conflicts (Python Scope)

### a) Mine from Git History (most realistic)

- Pick popular Python repos (Django, Flask, Requests, scikit-learn, etc.)
- Identify commits where code changed but adjacent docstrings/comments didn't within a time window
- Label these as likely drift instances
- Also find "documentation fix" commits (grep commit messages for "doc", "documentation", "typo in docstring") — the *before* state of these commits is a confirmed drift sample

### b) Synthetic Drift Injection (for controlled evaluation)

- Take a well-documented Python codebase
- Automatically mutate docs: remove parameters, change return type descriptions, swap argument names, introduce outdated version references
- This gives a labeled dataset with known ground truth

### c) Existing Academic Datasets

- The **CoSMeD** (Code-Comment Mismatch Detection) dataset and similar benchmarks from SE research
- Papers on API documentation consistency (e.g., *Zhong & Su, 2013*; *McBurney et al., 2018*) often include curated datasets — check availability

**Recommendation:** Combine (a) and (b). Real git-mined drift for ecological validity, synthetic drift for controlled coverage of the taxonomy. The dataset itself becomes a methodological contribution.