# Internal milestone plan

1. Read contract and inspect pinned optimizer API and upstream data (completed before implementation).
2. Implement auditable acquisition, conflict quarantine, fixed group splits, features, sparse pipelines and budgeted adapter; verify on synthetic data.
3. Execute all nine methods in nested development CV; full-development optimizer seeds 0/1/2; sensitivity diagnostics. Save aggregate evidence without payloads.
4. Choose demo by development mean outer F1 (ties: lower FPR, then method name); fit development models. Commit source/evidence, then commit and push a separate freeze before final scoring.
5. Score all frozen models once. Preserve start/completion event markers, measured metrics and aggregate errors. Audit exported model and freeze.
6. Complete documentation, tests/coverage, lint/format, synthetic smoke, build/clean wheel, final artifact audit and GitHub Actions matrix. Open one unmerged PR.

No thresholds or classifier hyperparameters will be tuned: LR liblinear, C=1,
max_iter=1000, random_state=2030, threshold >=0.5; TF-IDF as specified;
SelectKBest f_classif k=8. Empty structural masks cost 1.02 with zero fits.
All conflict groups are quarantined in full; other duplicate rows retain their
multiplicity and are constrained to one partition. Additional development-only
sensitivity groups remove all non-alphanumeric characters and replace digit runs
with `0`; this is a stress diagnostic, not an independence guarantee.
