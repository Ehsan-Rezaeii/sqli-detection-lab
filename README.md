# SQL Injection Detection Lab

An installable research prototype comparing nine classifiers of inert HTTP
parameter values: fixed rules, structural logistic regression, sparse character
TF-IDF, hybrid, SelectKBest, and structural-only Binary GA/GWO-S/GWO-V/RandomSearch.
The optimizers are imported from the actual pinned [Project 1](https://github.com/Ehsan-Rezaeii/metaheuristics-lab/tree/6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e)
dependency. See [measured results](docs/RESULTS.md), [protocol](docs/EXPERIMENT_PROTOCOL.md)
and [verification](docs/VERIFICATION.md) for the evidence and completion status.

**Experimental classifier, not a prevention or WAF control.** No SQL is executed,
no database is contacted, and no target is scanned. Actual SQL injection prevention
requires [OWASP's primary defenses](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html):
parameterized queries/prepared statements, allowlists for dynamic identifiers,
least privilege and secure application design.

## Install and verify

Python 3.10, 3.12 and 3.13 are the CI targets; the local study uses Python 3.12.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q --cov=sqli_detection_lab
ruff check .
ruff format --check .
sqli-lab smoke                 # synthetic-only; not benchmark evidence
python -m build
```

The direct Git dependency requires Git and network access during installation.
Pinned numeric/model versions are enforced before loading trusted frozen models.
`results/requirements-observed.txt` records the full observed environment;
`pyproject.toml` pins the direct dependencies. CI does not download the raw dataset.

## Reproduce the scientific stages

Raw data remain outside Git. [Provenance/rights](docs/DATA_PROVENANCE.md) identifies
the exact upstream commit, byte size, SHA-256 and source limitations. From a clean
work branch **without an existing freeze/final result**, run:

```bash
sqli-lab acquire                # immutable URL, timeout, exact size/hash checks
# or: sqli-lab acquire --offline /path/to/payload_full.csv
sqli-lab prepare                # persist provenance and split audit before training
sqli-lab development            # all nested CV, seeds, stress grouping, development fits
python experiments/report.py    # development tables, schema and plots
python experiments/verify.py    # real checks and clean wheel installation
# Commit development source, models, audit and evidence here.
sqli-lab freeze
# Commit results/freeze.json separately and push that commit here.
# If the checkout fetches only main, fetch the exact feature branch into origin first.
sqli-lab final                  # one exclusive, frozen held-out scoring pass
python experiments/report.py
sqli-lab audit --require-final
python experiments/verify.py --final
```

An existing finalized checkout is for auditing/inference. Do not delete its markers
or overwrite its results to make another run appear fresh. For independent
reproduction use a new clearly named result history and identify prior holdout
exposure. The final command refuses an uncommitted freeze, dirty source, unpushed
HEAD, changed models/evidence or an existing start marker. Recovery from partial
failure requires an honest event log and a new documented decision; there is no
automatic retry. Frozen pipelines are fitted only on development data.

## Local read-only API demonstration

Run from the trusted repository root after verifying its artifacts:

```bash
sqli-lab audit --require-final
uvicorn sqli_detection_lab.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

`GET /health` reports readiness. `POST /predict` takes exactly one JSON object,
for example `{"value":"synthetic catalogue item"}`. Only strings of at most
2,048 characters are accepted, including empty strings; extra fields, wrong
types and oversized strings receive 422. Replies contain `label`, positive-class
`score`, `model_id`, and the experimental warning. Missing/untrusted artifacts
produce 503. No raw input logging is implemented. There is no download, training,
SQL connection, query construction, URL fetch or payload execution at startup
or prediction time. The demo is intentionally bound to loopback and provides no
production authentication, monitoring, throughput or adversarial robustness claim.

Joblib files can execute code when loaded. Only use these locally produced files
from a trusted checkout and its committed checksum freeze. Checksums are not
signatures and cannot defend against an attacker replacing both model and trust
manifest. No model-upload endpoint is provided. Text-model exports contain short
n-gram vocabulary fragments but do not store source rows.

## Evidence and limitations

The primary cohort has 30,156 values: 24,124 development and 6,032 held-out, all
canonical groups disjoint. Primary exact/canonical duplicates and conflicts are
absent at the pinned source commit; stronger template similarity remains. Outer
CV is three group-aware folds with inner three-fold mask search. Every optimizer
run uses population 12 and exactly 60 objective evaluations; classifier fits are
reported separately. Model choice uses development only; all nine final methods
are reported together after a separate committed/pushed freeze.

CSIC benign values versus sqlmap-generated SQLi create substantial source
confounding. Source labels do not prove exploitability. A grouping stress test
is not independent real-world validation. Fold SD and seed variability are
not evidence of statistical significance. False positives and false negatives
remain consequential. There is no production-security, attack-evasion or
cross-source generalization claim. Constituent data redistribution rights remain
unverified; raw payloads and source-row-aligned labels are not published.

[Walkthrough](docs/IMPLEMENTATION_WALKTHROUGH.md) · [Handoff](docs/HANDOFF.md) ·
[Specification](docs/PROJECT_SPEC.md) · [Data audit](results/dataset_manifest.json)

Original code: MIT (see LICENSE). Dataset and Project 1 attribution are separate;
this repository's license does not clear constituent data rights.
