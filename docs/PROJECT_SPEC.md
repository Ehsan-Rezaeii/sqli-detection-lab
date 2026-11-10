# Project 4 — SQL Injection Detection Lab: Research and Engineering Specification

**Status:** Approved kickoff design. No implementation, experiment, test pass, model, performance improvement, or API is claimed completed by this document.

## 1. Motivation and research questions

Build an experimentally defensible comparison of fixed rules, manually engineered **structural features**, sparse **character n-gram TF-IDF**, and limited **binary metaheuristic structural feature selection** for classifying the **value of one HTTP request parameter** as a benign value or SQLi-labeled value.

- **RQ1 — Representation:** How do structural, character n-gram, and combined representations compare in SQLi-positive Precision, Recall, F1 and false-positive rate (FPR)?
- **RQ2 — Optimization:** Under the same objective-evaluation budget, do Binary GA/GWO meaningfully reduce the structural feature count or improve cross-validated performance relative to all structural features, SelectKBest, and binary Random Search?
- **RQ3 — Generalization and cost:** How sensitive are estimates to duplicate/normalized-string overlap, generator-derived patterns, sparse representation size, and inference/optimization cost?
- **RQ4 — Engineering:** Can a frozen detector be served safely through a limited, tested FastAPI **demonstration** without claiming prevention or production security?

## 2. Data source, labels and provenance

Primary source: <https://github.com/Morzeux/HttpParamsDataset> at immutable Git commit `926670a710283f87c05b554680facf3f9530548c`.

Immutable primary URL:
`https://raw.githubusercontent.com/Morzeux/HttpParamsDataset/926670a710283f87c05b554680facf3f9530548c/payload_full.csv`

The upstream README reports 19,304 `norm` values and 10,852 `sqli` values, in addition to XSS, CMDI and path-traversal categories. **Treat these as upstream claims until the actual CSV is audited.** The dataset is assembled from heterogeneous sources (CSIC2010 benign HTTP values, sqlmap-generated SQLi, and other scanners), which may cause source confounding and overoptimistic benchmark scores. Repository-level MIT text alone does not establish redistribution rights over all constituent third-party data.

Required acquisition:
- Download from immutable URL with timeout, integrity validation and an optional offline local raw-file path. Compute SHA-256, byte size, number of records, exact CSV header/schema, encoding and format from the actual file; record in `results/.../dataset_manifest.json` before training. Never hardcode an unverified SHA-256.
- Read text verbatim as inert strings; no SQL execution and no live target requests. Parse CSV robustly, including quoted commas and multiline values. Do not use `length`, `attack_type`, `label`, row identifiers, or file/split origin as predictive features (other than deriving the target).
- Main supervised cohort: `attack_type == 'norm'` mapped to `y=0`, `attack_type == 'sqli'` mapped to `y=1`, with consistency checks against the available `label` column. **Verify actual schema first**; if upstream semantics differ, document the mapping rather than inventing one.
- Exclude other attack categories from the primary binary study. Optionally analyze their behavior only as a separate, clearly labeled non-SQLi anomaly diagnostic; no classification as benign and no reuse to optimize the main study.
- Explicitly audit null/empty values, unreasonable lengths, malformed CSV, duplicated raw strings, normalized collisions, conflicting target labels, label proportions and source limitations. Define deterministic handling/quarantine of ambiguous label conflicts **before model fitting**, with per-class counts. Do not inspect final model errors while deciding data-cleaning rules.
- Keep raw third-party dataset under ignored `data/raw/`; publish source URLs, hashes, aggregated summaries and safely selected model/metric evidence instead. Recheck rights before redistributing any raw row text or row-aligned source labels. All sourced ideas/code/datasets must be credited.

The upstream `payload_train.csv`, `payload_test.csv`, `payload_test_lexical.csv` are **not** a license to assume an independent or correctly grouped holdout. Use `payload_full.csv` for the primary protocol and inspect official split overlap only if feasible as a separate dataset audit. `payload_test_lexical.csv` includes a distinct `sql-syntax` label and must not be silently mapped to `sqli` in the primary benchmark.

## 3. Predeclared split and leakage policy

**Primary unit of evaluation:** one raw HTTP parameter value, never a complete HTTP request or live web application.

1. Freeze a deterministic conservative grouping key based only on the raw value: Unicode NFKC, case folding, and whitespace normalization. Keep the original string intact as the actual model input. Record both raw-exact and grouping-key duplicates; never claim this guarantees all near duplicates are eliminated.
2. Build the primary cohort and resolve conflicting-label groups with a documented deterministic policy. Use `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=2027)` and reserve fold index `0` as approximately 20% **held-out test**, all remaining groups as **development**. Validate both classes have adequate support, and record actual group/class sizes; exact 80/20 cannot be guaranteed under groups. Any necessary fallback must be chosen and documented before model evaluation, using structural diagnostics rather than test model performance.
3. On development only, use three outer `StratifiedGroupKFold` folds (`random_state=2028`), with fresh three-way inner group-aware folds (`random_state=2029`) to select structural masks and assess their full procedures. Only inner-training folds fit all training-dependent transformations; outer-validation folds are never used inside selection. Record split indices/group hashes and class counts.
4. Once all comparison configurations and model-selection rules are fixed from development, commit **study source, split manifest and development evidence**. Commit a new freeze manifest (code hashes, dataset hash, group/split IDs, seeds, CV protocols, class mapping, method settings, budget, feature schema, inference config) before final test scoring. Store a one-time start/completion marker; never replace the final score with whichever result looks best. A previously viewed holdout cannot be represented as fresh.
5. No raw test payloads, test labels, test scores or test-derived feature vocabulary may be inspected by the search optimizer or tuning loop. Dataset-quality audits can record aggregate size and duplicate overlaps but cannot be used to tune model thresholds. Use primary held-out test once after freeze; all models report against the same partition.
6. Provide a **sensitivity diagnostic** for conservative alternative grouping (e.g. additional whitespace/punctuation normalization or a predeclared near-duplicate heuristic) on development only. If near-duplicate analysis is too costly, document exact overlap and sampled similarity diagnostics, limitations and computation; do not invent robustness evidence.

Avoid using the source's supplied train/test split as if it were group-disjoint without verifying. Do not treat CV folds, rows with correlated template strings, or three optimizer seeds as independent external populations.

## 4. Representations and fixed classifiers

All feature extraction and modeling must be reusable Python components with explicit ordering and known dimensions.

### 4.1 Structural representation (small, interpretable, dense)

Implement ~15–25 deterministic numeric features of the **input string** (not the target label), including length, digits/letters/whitespace counts or ratios, punctuation/quote/parenthesis/comment-marker counts, token counts, escape/percent-encoding indicators, keyword-like pattern counters, and lexical diversity. Clearly document definitions and normalization semantics; use reasonable clipping/validation to avoid overflow. A keyword/pattern feature is a model input, **not a claim of vulnerability**. Build a `StandardScaler -> LogisticRegression` train-only pipeline.

### 4.2 Character n-gram representation (sparse)

Use `TfidfVectorizer(analyzer='char', ngram_range=(2,5), max_features=40000, min_df=2, sublinear_tf=True)` as a transparent starting configuration; choose feasible fixed parameters using development/pilot data only and record any pre-test change. Fit vocabulary and IDF on each training fold only; preserve sparse CSR matrices, never call `.toarray()` for a large text matrix. Use LogisticRegression, with a consistent fixed solver/regularization and deterministic seed.

### 4.3 Hybrid representation

Combine train-only scaled structural features and sparse char TF-IDF using `ColumnTransformer`, `FeatureUnion` or an equally clear sparse-safe pipeline. Measure actual feature dimensions, peak-memory proxy, training and prediction latency. This combines representations; it does **not** itself prove GA/GWO improvements.

### 4.4 Fixed rule-based comparator

A small, transparent, deterministic heuristic for SQLi-like strings is a baseline, not a firewall. Define rule criteria **before test scoring**, count false positives and false negatives, and explain how patterns overfit generated data. No unbounded regular expressions; avoid catastrophic regex patterns. Rules may produce only binary decisions; AP should be `N/A` unless justified continuous scores are defined in advance.

### 4.5 Structural feature selection

- Structural all-feature LR.
- `SelectKBest` on structural features, fixed `k=min(8, feature_count)` or another single development-predeclared value (report the final exact value).
- `BinaryGA`, `BinaryGWO(transfer='s')`, `BinaryGWO(transfer='v')`, `RandomSearch(domain='binary')`, all imported from pinned Project 1.
- All binary optimizers use `population_size=12`, `max_evaluations=60`, and fixed optimizer seeds; record the **actual instance settings** in each run/freeze.
- Optimize **structural subset only**, not all character n-grams. A mask is a 0/1 vector aligned with the declared structural schema. Empty masks receive a documented deterministic penalty and never silently fit a classifier. Do not cache repeated masks unless exact objective counts remain honest; if caching is enabled, report actual model fits separately from objective evaluations.
- Inner fitness for a nonempty mask (minimize):

  `0.50 * (1 - mean_F1) + 0.30 * mean_FPR + 0.20 * (1 - mean_Recall) + 0.02 * selected_feature_fraction`

  All terms are computed from inner validation folds using SQLi label `1`; report their per-fold values. Fitness weights are engineering choices, not measured deployment costs. Report selection variance, feature counts, wall time, actual classifier fits and optimizer objective evaluations. Make no assumption that optimizers beat SelectKBest.
- Outer comparison uses one fresh search per outer training fold for each optimizer. Full-development search runs seeds `(0, 1, 2)` for each optimizer; select the final mask deterministically by `(fitness, selected_count, seed, lexicographic_mask)`. Keep test untouched throughout.

**Initial method count: nine** — fixed rules; structural LR; char TF-IDF LR; hybrid LR; SelectKBest structural LR; BinaryGA structural LR; BinaryGWO-S structural LR; BinaryGWO-V structural LR; RandomSearch structural LR. The FastAPI demo must serve one explicitly frozen model chosen **from development evidence only** and document that decision. Do not promote the highest test score as the serving-model selection rule.

## 5. Metrics, analysis and results

On outer CV and once on held-out test:

- SQLi-positive Precision, Recall, F1, FPR=`FP/(FP+TN)`, confusion matrix, support, prevalence; optional Average Precision for models providing an appropriate continuous score. Undefined metrics must have explicit, justified `null` handling.
- Rule baseline metrics, representation dimensions, structural selected feature counts, model fit/predict time, measured per-item/batch prediction latency, sparse memory proxy, objective evaluations, classifier fits and mean/SD over development folds.
- Analyze exact/normalized duplicates, label conflicts, false-positive types (without publishing full third-party text payloads), confusion matrix costs, generator-derived string artifacts, prediction performance on relevant held-out length/token/encoding strata when support permits.
- Predeclare model selection before holdout and make one primary model-choice report based on outer development estimates. Never pick a different 'winner' after seeing test scores.
- Report statistical uncertainty; do not claim statistical significance from three correlated folds or post hoc selection. No attack-evasion, production WAF, or cross-source generalization claims without actual evidence.

Raw/synthetic data, numerical results, and sample payload snippets must be clearly labeled. Protect source data licensing and avoid storing raw payloads in API logs.

## 6. FastAPI experimental demonstration

Implement `GET /health` and `POST /predict` for **one text parameter value**. Input must use Pydantic validation (`value: str` with a fixed moderate max length, initially 2048 characters); reject wrong types, oversize inputs, malformed requests and missing local model artifacts clearly. Return a non-authoritative prediction (`label`, `score` if probabilistic, `model_id`, and a clear research-only warning); never call a database, interpolate a query, fetch an URL or execute payloads. No remote scan endpoints. The server must not train automatically or download external files during startup. Model file must be produced locally from a frozen training process with checksums; document risks of untrusted pickle/joblib loads and permit loading only a trusted locally generated file. Test with `TestClient` using benign and synthetic inert strings, bounds, lifecycle, determinism, schema and no model-training side effects.

Explicit security notice: ML-based text screening cannot replace parameterized queries/prepared statements, appropriate allowlists and least privilege. Cite OWASP guidance in README.

## 7. Engineering deliverables and success criteria

Expected repository structure (adapt only when justified):

```
README.md
AGENTS.md
pyproject.toml
src/sqli_detection_lab/{__init__,data,features,models,selection,experiment,api,cli}.py
tests/
experiments/
docs/{PROJECT_SPEC,EXPERIMENT_PROTOCOL,RESULTS,IMPLEMENTATION_WALKTHROUGH,VERIFICATION,HANDOFF}.md
results/{dataset_manifest,development,final,freeze,...}
.github/workflows/ci.yml
.gitignore
```

**Definition of done:** actual pinned dataset verified, labeled and audited; no raw proprietary dataset silently checked in; meaningful structural/text/hybrid/rule comparators; installed Project 1 dependency exercised; fair optimizer budgets; leakage-safe development and final split; genuine experiments and plots; repeatable saved evidence, tested freeze; installed package and CLI; API/validation tests; lint/format, builds and clean-wheel imports; CI (e.g. Python 3.10, 3.12, 3.13 if compatible) passing; English README, limitations and precise attribution; unmerged PR for independent review. Any blocked work must be called blocked, not complete.

**Reference links:**
- Dataset: https://github.com/Morzeux/HttpParamsDataset
- Scikit-learn TF-IDF: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- Scikit-learn StratifiedGroupKFold: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- OWASP SQL Injection Prevention: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- Project 1 dependency: https://github.com/Ehsan-Rezaeii/metaheuristics-lab/tree/6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e
