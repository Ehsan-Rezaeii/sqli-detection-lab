# AGENTS.md — Project 4: SQL Injection Detection Lab

## Mission and boundaries

Build the complete, honest, reproducible `sqli-detection-lab` research prototype. This is Project 4 in a five-repository AI/optimization portfolio. It studies **detection of SQL-injection-like HTTP parameter values**, not exploitation, web application vulnerability discovery, or a complete security control. Implement first; teach the user later in a separate conversation. Code, documentation, reports, commits, and PR text must be professional English.

**Read `docs/PROJECT_SPEC.md` first.** It is the methodological contract. If a major contradiction appears, report it rather than silently changing the scope. Do not substitute another dataset without a reason, provenance and a documented approved change. Do not edit other portfolio repositories.

## Real dependency on Project 1

Import binary optimization algorithms through the actual installed `metaheuristics-lab` dependency at Git commit `6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e` (verify its API against that commit). Use `BinaryGA`, `BinaryGWO` (`transfer='s'`/`'v'`), `RandomSearch(domain='binary')`, and `Problem`. Explicitly set `population_size=12` for **every** search, including Random Search; budget 60 objective evaluations per search. Store the actual instantiated optimizer settings in every trace and study freeze. Do not duplicate optimizer source code.

## Scientific integrity

1. Inspect source data and license/provenance before training. Treat documentation counts as unverified until audited. Source: `Morzeux/HttpParamsDataset`, master commit `926670a710283f87c05b554680facf3f9530548c`, primary `payload_full.csv`. Acquire from this immutable commit; record SHA-256 and byte size. Preserve raw bytes off-repo unless redistribution rights of all constituent sources are confirmed. Do not assume upstream MIT license resolves rights for all derived third-party payloads.
2. Define primary labels `norm -> 0` and `sqli -> 1`; never silently classify XSS/CMDI/path-traversal samples as benign. Audit all categories, missing/invalid rows, duplicated text, canonical-duplicate groups, label conflicts, train/test overlap and provenance limitations.
3. Use deterministic, group-disjoint development/holdout split and **nested training-only CV** for selection and model comparison. `TfidfVectorizer` vocabulary, IDF, `StandardScaler`, feature filters, calibrators/threshold choices (if any), and search objectives must be learned only inside permitted training folds. No test-driven model/pipeline tuning.
4. Compare a transparent fixed-rule baseline, structural-only logistic regression, character n-gram TF-IDF logistic regression, hybrid representation, `SelectKBest` on structural features, and `BinaryGA`, `BinaryGWO-S`, `BinaryGWO-V`, binary `RandomSearch` selection on structural features. Do not perform dense optimization across tens of thousands of text n-grams. Maintain fair optimizer evaluation budgets; nonsearch baselines have different compute and should be reported separately.
5. Predeclare metrics: SQLi-positive Precision/Recall/F1, false-positive rate (FPR), confusion matrices, AP where score outputs exist, selected feature counts, sparse dimension, inference time and compute. Report group-level and duplicate-sensitivity diagnostics, uncertainty and negative findings. Do not claim generalization to deployed attacks or claim one source's generator artifacts represent real traffic.
6. Final holdout is scored after an explicit committed freeze containing models/configs/seeds/splits/fit costs/dependency/dataset/code hashes. The study's single final evaluation must not tune or select winners on target metrics. For transient failures, investigate and preserve a truthful event log; don't falsify gate evidence. CI should be able to run before final artifacts exist without erroneous red results: clearly separate synthetic/core tests from finalized-artifact tests.
7. Run genuine experiments; save raw anonymized/aggregated evidence (without publishing third-party text payloads unless rights are clear), summaries, plots, run commands, environment versions and limitations. Audit predictions from saved scores where feasible. Never invent outputs or label an unexecuted check as passed. Never erase an inconvenient negative result.

## Engineering and security

- Installable Python `src/` package, simple typed modules, deterministic seeds, clear CLI, pytest, Ruff, source/wheel build, clean installation/import, GitHub Actions; use a compatible pinned dependency set and explain how to reproduce it.
- Safe small FastAPI demonstration: one `/predict` endpoint for a **string value only**, plus `/health`; local, read-only inference, no SQL/database execution, no payload execution, no remote scanning, no logs of raw input by default, no automatic download/training on server startup. Validate type and maximum input length and return a clearly experimental score/label. Use a locally produced, version-checked model artifact; do not load arbitrary remote pickle/joblib files. Test API with FastAPI `TestClient`.
- Include input robustness tests (empty, very long, Unicode, encoding-like strings), feature extraction dimensions, label direction, rule precision limitations, pipeline train-fold isolation, duplicate grouping, holdout gate, frozen model identity, and end-to-end synthetic smoke.
- **Never** represent a classifier as SQL injection prevention. Clearly reference OWASP primary defenses: parameterized SQL, allowlisted dynamic identifiers, least privilege, and secure application design.
- Avoid offensive deployment or exploit automation. Do not probe any real service. Dataset strings are treated as inert text; never execute them as queries or shell commands.

## Deliverables

At minimum: `pyproject.toml`, `README.md`, `src/sqli_detection_lab/`, `tests/`, `experiments/`, `docs/PROJECT_SPEC.md`, `docs/EXPERIMENT_PROTOCOL.md`, `docs/RESULTS.md`, `docs/IMPLEMENTATION_WALKTHROUGH.md`, `docs/VERIFICATION.md`, `docs/HANDOFF.md`, `.github/workflows/ci.yml`, reproducible `results/` with evidence, and `.gitignore`. Avoid putting raw dataset or sensitive/proprietary payload text in public results. Include data provenance and a limitations section.

Work autonomously through the full approved scope, not merely a skeleton or MVP. Commit on a dedicated feature branch and open a PR against `main`; **do not merge**. Before claiming completion, run actual test/lint/build/wheel/smoke/experiment/audit steps and report exact outcomes, CI links and blockers. If source data cannot legally/technically be used, provide a defensible alternative plan and clearly flag the unresolved blocker; never fabricate completion.
