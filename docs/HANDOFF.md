# Owner handoff

The research prototype is implemented; consult [results](RESULTS.md) for measured
comparisons and [verification](VERIFICATION.md) for actual executed checks and
remote CI status. The repository remains a reviewable, unmerged feature branch.
Development evidence is committed at `3d59540`; freeze is
`9184886cab5b1c851e2ad00237455b641979cece`, with SHA-256
`ef9a9a33ef62fe41fb45908493cfd7458ef78b5e597e01009ba08e630859f9db`.
Final start/completion markers record one scoring pass after the pushed freeze.
[PR #1](https://github.com/Ehsan-Rezaeii/sqli-detection-lab/pull/1) is open against main
and must remain unmerged for owner review. [Actions evidence](https://github.com/Ehsan-Rezaeii/sqli-detection-lab/actions/runs/42898191861)
passed Python 3.10/3.12/3.13, each 20 tests and 93% coverage, plus all engineering
and artifact checks. The final completion message supplies the latest head/run.
The [changed-file inventory](../results/changed_files.txt) lists every changed path.
The PR/head and CI links are supplied in the completion report and CI record.

The demo model is **hybrid**, selected solely by the declared development outer
F1/FPR/name rule. It is not chosen from held-out scores. All nine methods remain
in the comparison. Fixed rules miss many source-labeled positives; the optimizer
masks reduce structural count but do not beat the all-structural baseline on mean
outer F1. Do not describe the study as proof of GA/GWO superiority.

Use the README installation and local loopback API commands. Audit before loading
joblib; trust both checkout and committed freeze. Data are acquired separately
with exact immutable integrity validation, not downloaded by the service.
Preserve final start/completion markers. Do not repeat a viewed holdout and call
it fresh. To extend the study, create a new clearly identified protocol/history
and acknowledge existing test exposure. Threshold changes, new features or
candidate selection require development-only analysis and a new evaluation plan.

Owner decisions for any further deployment: obtain independent benign/attack
traffic with legitimate rights and provenance, adjudicate labels, evaluate by
source/time/application, measure consequential false positives, consider stronger
near-duplicate/template grouping, and design authentication, rate limits and
privacy safeguards. None of those production capabilities is established here.
Avoid deploying the demonstration as a blocking security control.

The benign/SQLi generators are confounded; primary grouping cannot remove all
near duplicates. Three folds and three seeds are correlated and do not support
significance claims. Unknown constituent redistribution rights remain unresolved;
raw CSVs, payload examples and row-aligned source targets stay outside Git.
Text artifacts contain short n-gram vocabulary fragments. Measured CSR buffer
size is not peak RSS; local inference latency is not a throughput guarantee.
The API is experimental, read-only and not SQL injection prevention or a WAF.
Parameterized queries and OWASP's primary defenses remain necessary.

The frozen hybrid held-out result is precision 0.999536, recall 1.0, F1 0.999768,
FPR 0.000258: TN=3,878, FP=1, FN=0, TP=2,153. Structural has the same final confusion
counts, despite the development rule choosing hybrid. No model switch was made.
The held-out percent-encoded stratum has zero support; synthetic Unicode/encoding
API acceptance tests establish input handling only. Optimizers can retain constant
columns under finite budgets. Full masks and exact runtime settings are frozen;
these are research comparisons, not optimality guarantees.
