# Verification record

All pass claims refer to executed commands. Machine-readable invocations, elapsed
time and exit codes are in `results/verification/commands.jsonl`; command stdout
and stderr are saved alongside it. Historical failures are preserved under
`results/verification/initial/` and in `execution_events.json`.

Local study runtime: Python 3.12.14. `results/environment.json` records platform
and pinned numeric/model versions; `requirements-observed.txt` records the full
observed installed environment. Installed Project 1 PEP 610 metadata confirms
commit `6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e`; signatures and source were
inspected at that commit before using its public API.

## Completed before final freeze

- `sqli-lab acquire --offline /tmp/project4-dataset/payload_full.csv`: exact bytes/hash validated.
- `sqli-lab prepare`: dataset and group split manifests persisted before training.
- `python experiments/audit_source.py /tmp/project4-dataset`: pinned repository, all CSVs, source documents and official split overlap audited.
- `sqli-lab development`: all nine methods, 3 outer × 3 inner CV, 12 outer searches, 12 full-development seed searches, 9 stress-group sensitivity fits and 9 final development model fits completed; stdout saved in `development.txt`.
- `python experiments/report.py`: measured development tables, plots and feature schema generated.
- `python experiments/verify.py`: core tests/coverage, lint/format, synthetic smoke, source/wheel build and clean wheel checks, with individual results in the command log.

The first test run failed (5 failed, 11 passed, 1 skipped): a constructor spy did
not expose mock `__name__`, and a synthetic API fixture lacked a freeze file.
The adapter now inspects the actual constructed instance type, and the fixture
writes the required local freeze. The first synthetic full-study integration
failed (1 failed, 16 passed, 1 skipped) because its numbered strings collapsed
into only two stress groups. Alphabetic synthetic identifiers corrected the
fixture; production split support checks were retained. Subsequent pre-final
verification passed 19 tests with one explicit final-artifact skip and 93%
statement coverage (see saved report). Warnings for constant ANOVA columns are
retained. A Starlette/AnyIO deprecation warning is non-failing.

Two early development runs were intentionally interrupted to tighten the bounded
rule pattern and correct dimension/split metadata; they were not final scoring.
Bounding every rule whitespace run to 32 characters was then verified to change
zero decisions on all 24,124 development strings (`rule_bound_check.json`). No
held-out decisions were inspected for that check. No LR, TF-IDF, threshold or
optimizer budget was tuned. Matplotlib used a temporary writable cache after
its home cache was read-only; plots were actually produced.

Git transport works. The installed `gh` API client returned Forbidden, so the
connected GitHub tools are used for PR creation and Actions inspection. This
is not reported as a successful CLI API check.

## Final verification

Pending until the separate freeze has been committed/pushed and its one final
scoring pass has completed. This section will be updated with measured outcomes.
Final-head CI uses Python 3.10/3.12/3.13, core/synthetic tests, coverage, lint,
format, smoke, build, clean wheel import and mandatory final artifact audit when
`results/FINALIZED` exists. Pre-final CI does not erroneously require artifacts
that have not been scored. Actual remote run URLs and conclusions will be recorded.
