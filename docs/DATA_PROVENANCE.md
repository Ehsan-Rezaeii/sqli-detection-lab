# Data provenance and rights

Primary repository: https://github.com/Morzeux/HttpParamsDataset at immutable
commit `926670a710283f87c05b554680facf3f9530548c` (inspected local checkout).
`results/dataset_manifest.json` records the actual primary audit;
`results/source_audit.json` records all four CSV files, source document hashes
and official train/test overlap. The full UTF-8 CSV is 1,996,540 bytes,
SHA-256 `a4e62ba13435ad3dd583c5790db2175629020fc41c56e1b26baa02a9ae45f03d`.
Its schema is `payload,length,attack_type,label`. CSV parsing preserves quoted
commas and multiline text. 31,067 records comprise 19,304 norm, 10,852 sqli,
532 xss, 89 cmdi and 290 path-traversal. Labels are norm/anom; only norm/sqli
enter the primary supervised cohort. Fifteen length mismatches are all XSS.
There are no empty values, exact/canonical duplicates or category conflicts in
the full source. Primary retained rows/groups total 30,156 with no quarantine.
Maximum source value length is 1,058 Unicode characters. Counts are measured,
not inferred from the README (whose introductory "over 3100" wording is imprecise).

The source README attributes normal values to CSIC2010 benign HTTP parameters,
SQLi to sqlmap generation, and other categories to XSSYA, Vega and FuzzDB.
The source supplies no per-row generator lineage, deployment sampling frame,
timestamp or independently adjudicated vulnerability outcome. These categories
are source labels, not proof that a value exploits any application. Label and
generator are confounded. No independent provenance-separated evaluation can
be reconstructed from these fields. High benchmark scores may reflect formatting,
length and generator vocabulary rather than real SQL injection detection.

The repository LICENSE is MIT, copyright 2016 Morzeux. It grants use of the
repository materials as provided, but the README does not provide a full rights
chain for each constituent source. No separate constituent-licensing verification
was established. This study performs local research use and does not redistribute
raw CSVs, examples, full payload text or source-row-aligned labels. Keep raw files
under ignored `data/raw/`. Do not interpret the original-code MIT license as a
data clearance. Published model artifacts contain coefficients/scaling/filter
state and, for text models, short 2–5 character vocabulary fragments; they contain
no stored training rows. Review constituent rights again before broader reuse
or distribution. Anonymous score/label histograms and aggregate error strata
have no source-row identities.

Official `payload_train.csv` and `payload_test.csv` have zero raw/canonical
intersection at this commit, but that does not establish template independence.
Their measured sizes are 20,712 and 10,355 records. They are not used for model
selection or scoring. `payload_test_lexical.csv` has 1,106 records and distinct
`sql-syntax`/`js-syntax` categories; it is audited only and never silently remapped.

Acquire with the package's immutable URL and timeout or supply `--offline` with
the exact pinned file. Byte size and SHA-256 must match before parsing/training.
No code is downloaded at API runtime, no payload is interpreted as SQL, and no
request is made to an application target.
