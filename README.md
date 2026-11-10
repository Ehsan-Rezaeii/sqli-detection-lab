# SQL Injection Detection Lab

A reproducible research project comparing **hand-engineered structural features**, **character n-gram TF-IDF**, a **hybrid representation**, and **Binary GA/GWO feature selection** for classifying SQL-injection-like HTTP parameter values. An experimental **FastAPI** inference interface is included in the approved scope.

> **Kickoff status:** research design and Codex implementation instructions are prepared. Code, experiments, final models, tests, and measured performance are **not yet completed or verified**. This README must be updated with genuine results only after execution and independent review.

## Research questions

- Do different feature representations change SQLi-positive Precision, Recall, F1 and false-positive rate?
- Can metaheuristic structural feature selection reduce feature count without sacrificing performance against simple baselines?
- What do duplicate groups, source-generated patterns, and computation cost reveal about generalization?

## Planned comparisons

- Deterministic rule-based baseline.
- All structural features + Logistic Regression.
- Character n-gram TF-IDF + Logistic Regression.
- Hybrid structural + sparse text features + Logistic Regression.
- SelectKBest on structural features.
- Binary GA, Binary GWO (S/V), and binary Random Search on **structural features only** using the actual pinned [Project 1 library](https://github.com/Ehsan-Rezaeii/metaheuristics-lab).

## Planned data and evaluation

Primary candidate: [HttpParamsDataset](https://github.com/Morzeux/HttpParamsDataset), specifically the immutable `payload_full.csv` at commit `926670a710283f87c05b554680facf3f9530548c`. The primary target distinguishes `norm` from `sqli`. The upstream source combines benign data with tool-generated payloads; therefore apparent test accuracy may not transfer to real HTTP traffic. Data rights for constituent sources must be audited before redistributing sample values.

The study will use group-disjoint development/holdout separation, training-fold-only vectorization and feature selection, a pre-committed final freeze, and saved reproducible numerical evidence. See [PROJECT_SPEC.md](docs/PROJECT_SPEC.md).

## Security limitations

**This is not a vulnerability scanner, WAF, or SQL injection prevention mechanism.** No database is queried and no supplied payload is executed. The API is a local demonstration only. Actual prevention depends on [parameterized queries, safe handling of dynamic query structure, and least privilege](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).

## Implementation instructions

Codex should first read [AGENTS.md](AGENTS.md) and [PROJECT_SPEC.md](docs/PROJECT_SPEC.md), then implement, test, execute real experiments, document limitations and open an unmerged PR. Do not insert fabricated result tables or success badges.

**Repository license:** To be chosen by the owner (MIT is suitable for original code). Upstream data licensing and attribution must be assessed independently; do not assume the repository license grants rights over all dataset content.
