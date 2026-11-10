# Implementation walkthrough

`data.py` acquires exact pinned bytes or validates an offline file, uses strict
UTF-8 CSV parsing, verifies category/label semantics and audits metadata.
It quarantines entire canonical conflict groups before constructing a binary
cohort, then enforces the seeded StratifiedGroupKFold protocol and class support.
Only `payload` is passed to models. Published manifests contain counts and hashes;
compressed integer split indices support reconstruction without publishing text
or row-aligned targets. The separate source-audit script checks all upstream CSVs.

`features.py` defines twenty ordered numeric features of raw Unicode text.
`Structural` is stateless; `Mask` validates a nonempty aligned binary subset.
Feature definitions are emitted to `results/feature_schema.json`.
`models.py` builds reusable scikit-learn pipelines: train-only structural scaling,
f_classif SelectKBest, char TF-IDF and a sparse FeatureUnion hybrid. Logistic
models share a fixed solver, C and class direction. `Rules` is a transparent
bounded-pattern comparator with no invented probability score. No sparse text
matrix is densified; CSR buffer bytes and actual output dimensions are measured.

`selection.py` imports Project 1's Problem, BinaryGA, BinaryGWO and RandomSearch.
Its adapter captures actual constructor arguments/defaults/attributes and the
separate optimize arguments. The installed PEP 610 Git commit is checked.
`Objective` builds three inner-training-only scalers, then fits three independent
LRs per nonempty mask. Reusing scaled columns is mathematically equivalent to
scaling after mask selection and does not use validation data. Empty masks cost
1.02 with no fits. No objective-value caching hides repeated proposals. Per-call
masks, per-fold confusion-derived metrics, fitness, fit counters and incumbent
history make the 60-evaluation budget independently auditable.

`experiment.py` owns the distinct development/freeze/final stages. Outer masks
are selected only using inner folds; outer validation is used only for reporting.
Full-development searches run seeds 0/1/2 and select masks by the declared tuple.
The demo method uses mean outer F1, then FPR/name, before final data are loaded.
Development fits all nine final models, records their hashes and fitting times,
and measures the separate alternative-grouping sensitivity diagnostic.

`artifacts.py` freezes and checks source, evidence, model and runtime identities.
The final command additionally requires Git commitment, clean state and a pushed
freeze; exclusive start/completion files document one scoring pass. Final inference
loads only those models and performs no fitting. Exact score/count histograms
permit independent reconstruction of metrics without publishing row identities.
Artifact audit rechecks all optimizer budgets/objectives/fit counts and checksums.
The committed freeze is a trust root, not a cryptographic signature.

`api.py` provides an explicit app factory and lifespan loader; strict Pydantic
validation accepts one <=2048-character string. Unavailable trusted artifacts
produce a clear 503. Positive probabilities identify `classes_ == 1`; all
responses carry a research-only warning. Input values never enter logs or a
database, shell, URL fetch or SQL interpreter. Artifacts are executable joblib
serialization and must be trusted locally. Serving does not retrain or download.

`cli.py` exposes explicit commands. `smoke.py` uses only labeled synthetic strings.
Tests cover parsing, conflicts, duplicate groups, class direction, metrics,
fold-local fit observations, sparse vocabulary isolation, actual optimizer
constructor/optimize kwargs, empty masks and deterministic traces. An isolated
synthetic Git repository tests development → commit → freeze → push → one final
pass, plus tampering and API lifecycle/validation with TestClient.
Final-artifact tests skip explicitly before artifacts exist; FINALIZED makes the
final-head CI require them. `experiments/verify.py` records actual command exits,
outputs, timing, builds and a clean wheel import outside the source directory.
`experiments/report.py` reads aggregate evidence only and never fits or chooses.
