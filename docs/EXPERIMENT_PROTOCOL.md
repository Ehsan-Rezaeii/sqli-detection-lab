# Experiment protocol

The approved [specification](PROJECT_SPEC.md) controls this study. The primary unit
is one inert parameter string, with `norm=0`, `sqli=1`; other categories are excluded.
No database, target scanning, SQL execution or payload execution is involved.

Data quality rules were fixed before fitting: reject malformed schema, unknown
categories, or inconsistent `attack_type`/`label`; quarantine empty or over-100,000
character values and entire conflicting canonical groups. Preserve raw text and
multiplicity otherwise. Only text enters models. `length`, target metadata and
row position are never predictors. NFKC, casefold and whitespace collapse define
groups, but model inputs remain verbatim. No URL decoding is performed.

## Partitions and fitting

Reserve fold 0 of five-way StratifiedGroupKFold, shuffle=True, seed 2027.
Use only its complement for three outer folds (2028), each with three inner
folds (2029). Check class support and group disjointness for every split.
Publish split counts, ordered-index digests, sorted-group digests and compressed
integer indices, without payloads or row-aligned labels. Local acquisition
reconstructs groups and labels to reproduce all splits. Seeds do not make related
generated strings independent.

Structural extraction is stateless. Scale columns using only inner training data;
scaling precedes mask indexing because independent column scaling commutes with
masking. Reuse the three fold-local scaled arrays within a search, but never cache
objective values or fitted classifiers. Each nonempty objective call fits three
fresh logistic classifiers. Outer train fits its own scaler, filter and vocabulary;
validation sees only transforms. Text and hybrid vocabularies/IDF are learned from
their respective training partition. No calibrator or threshold fitting occurs.

## Fixed configurations

Twenty structural columns are defined in `results/feature_schema.json` and
`features.py`. LR uses `solver=liblinear`, `C=1`, `max_iter=1000`,
`random_state=2030`, default L2 penalty, intercept, and no class weighting.
Positive scores use the column explicitly identified by `classes_ == 1`.
Decision threshold is >=0.5 throughout. Text uses char (2,5) n-grams,
40,000 maximum features, min_df=2, sublinear_tf=True; remaining scikit-learn
TF-IDF defaults (lowercase, L2 normalization, smooth IDF) are retained.
Hybrid stacks dense scaled structural columns into a sparse union with text.
SelectKBest uses f_classif and k=8 before StandardScaler. Constant-column warnings
are preserved; they are not hidden or interpreted as predictive discoveries.

The rules look for union + whitespace + select, select ... from (intervening
non-newline text bounded to 256 characters), sleep/benchmark followed by an opening
parenthesis, or OR/AND followed by two 1–10 digit constants around `=`.
Whitespace runs in rules are bounded to 32 characters.
Case is ignored. These are keyword heuristics, not a SQL parser. Only binary
decisions are defined, so rule AP is null.

Project 1 is a real direct Git dependency at
`6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e`. Its installed PEP 610 commit is checked.
BinaryGA, BinaryGWO-S, BinaryGWO-V and RandomSearch(binary) constructors all receive
population_size=12. `.optimize()` receives max_evaluations=60 and an explicit seed.
No algorithm is reimplemented. Actual constructor kwargs, defaults, instance
attributes and optimize kwargs are saved in every trace and freeze. GA retains
crossover_rate=.9, mutation_rate=None (1/dimension), tournament_size=3; GWO uses
the declared transfer; RandomSearch samples binary masks.

Nonempty-mask fitness, minimized, is exactly:

`0.50*(1-mean_F1) + 0.30*mean_FPR + 0.20*(1-mean_Recall) + 0.02*selected/20`.

Empty masks have fixed penalty 1.02 and zero classifier fits. Objective calls and
fits are counted separately, including repeated masks. Each outer procedure uses
a fresh seed-0 search. Each full-development search uses seeds 0,1,2; choose mask
by (fitness, count, seed, lexicographic mask). Report all methods and seeds.
Search budgets are equal to one another; they are not equivalent to baseline cost.

## Decisions and freeze

Select the demo method by maximum mean outer F1; break ties by lower mean FPR,
then method name. This rule was recorded before development evaluation. No final
score changes that decision. Refit each final pipeline on all development data
using only frozen masks/configuration. Commit source, models and development
evidence; generate a separate freeze containing their hashes; commit and push it.
Only then may `sqli-lab final` run. It checks a clean working tree, committed
freeze, frozen source/evidence/model integrity and pushed HEAD. It creates an
exclusive start marker before loading test data and a completion marker after
all nine models. A partial failure remains visible and requires investigation;
there is no automatic retry or score replacement. Final inference has zero fits
and zero objective calls.

Hashes protect against accidental changes, not an attacker able to rewrite the
repository and trusted freeze. Joblib is executable serialization: load only the
locally produced checksummed artifacts from a trusted checkout; never accept a
model upload. The API does not download or train.

## Metrics and diagnostics

SQLi-positive precision=TP/(TP+FP), recall=TP/(TP+FN),
F1=2TP/(2TP+FP+FN), FPR=FP/(FP+TN). Undefined denominators yield JSON null;
fitness would substitute zero for undefined values, but every training/validation
split is required to contain both classes. AP is scikit-learn average precision
on continuous positive-class probabilities. Publish TN/FP/FN/TP and support.
Outer means and sample SD (ddof=1) describe fold variability, not confidence
intervals or significance. Three correlated folds do not establish population
uncertainty. Seed variation is an algorithm diagnostic, not independent evidence.

Report actual dimensions, CSR buffer bytes (a memory proxy, not peak RSS), fit/search
wall times, batch-amortized inference and up to 100 cold single-item predictions.
Single-thread BLAS limits avoid oversubscription. Runtime comparisons are local
observations, not production benchmarks. Report one representative per canonical
group as a duplicate-sensitivity diagnostic. With no primary duplicates it equals
row-level evidence.

Development-only stress groups retain only alphanumeric NFKC/casefold text and
replace digit runs with `0`. Measure their overlap across primary outer splits
and rerun three fixed representations using stress-disjoint folds. This heuristic
can merge unrelated benign values and does not remove all template similarity.
It is a sensitivity analysis, never a new winner selection or test redefinition.
No full template clustering or independent source holdout is claimed.

Held-out diagnostics use fixed length <=20, 21–100, >100 strata, percent-encoding
presence, and select/union/sleep token presence. They are descriptive, not tuning
inputs. Error summaries publish counts only. Final exact score/count histograms
have no row IDs or raw values and permit independent metric reconstruction.
