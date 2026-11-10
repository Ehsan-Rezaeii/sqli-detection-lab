# Owner handoff

The research prototype is implemented; consult [results](RESULTS.md) for measured
comparisons and [verification](VERIFICATION.md) for actual executed checks and
remote CI status. The repository remains a reviewable, unmerged feature branch.
The completion record will name the development and freeze commits, final head,
artifact digest and PR after those operations actually complete.

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
