# Plan of Work

| Phases | Start Date – End Date | Work to be Done |
|---|---|---|
| Foundation & Literature Review | 5 May 2026 – 18 May 2026 | Finalize drift definitions, formulate research questions, conduct systematic literature review across documentation drift, LLMs for code understanding, and automated documentation quality tools |

| Dataset Construction | 19 May 2026 – 15 Jun 2026 | Select target Python repositories, mine real drift instances from git history, generate synthetic drift via mutation scripts, manual annotation with two annotators, compute Cohen's Kappa, build the evaluation dataset (~800 entries) |

| Baseline & LLM Pipeline | 16 Jun 2026 – 28 Jun 2026 | Implement non-LLM baselines (darglint, AST checker, git heuristic), design and implement LLM-based detection pipeline (zero-shot, few-shot, chain-of-thought), build output normalization layer, set up evaluation harness |

| Evaluation & Analysis | 29 Jun 2026 – 12 Jul 2026 | Run all approaches on the dataset, compute precision/recall/F1 per drift type, perform statistical significance testing (McNemar's test/bootstrap CI), conduct error analysis (false positives, false negatives, type misclassification) |

| Dissertation Writing | 13 Jul 2026 – 20 Jul 2026 | Write full dissertation chapters: introduction, related work, drift definitions, dataset construction, methodology, evaluation, discussion, threats to validity, conclusion and future work |

| Dissertation Review | 21 Jul 2026 – 22 Jul 2026 | Submit dissertation to supervisor for review and feedback, incorporate revisions |

| Final Submission | 23 Jul 2026 | Final review and submission of dissertation |