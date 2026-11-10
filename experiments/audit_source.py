"""Audit a local checkout of the immutable upstream repository; emit no payloads."""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from sqli_detection_lab.data import DATA_COMMIT, canonical
from sqli_detection_lab.io import digest, write_json


def audit_source(source):
    import subprocess

    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != DATA_COMMIT:
        raise ValueError("Wrong source commit")
    report, values = {}, {}
    for path in sorted(source.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file, strict=True)
            rows = list(reader)
        raw = Counter(r["payload"] for r in rows)
        normalized = Counter(canonical(r["payload"]) for r in rows)
        labels = defaultdict(set)
        for row in rows:
            labels[canonical(row["payload"])].add(row["attack_type"])
        report[path.name] = {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "records": len(rows),
            "header": reader.fieldnames,
            "categories": dict(Counter(r["attack_type"] for r in rows)),
            "raw_duplicate_excess": sum(n - 1 for n in raw.values()),
            "canonical_duplicate_excess": sum(n - 1 for n in normalized.values()),
            "multicategory_canonical_groups": sum(len(v) > 1 for v in labels.values()),
            "length_mismatches_by_category": dict(
                Counter(r["attack_type"] for r in rows if int(r["length"]) != len(r["payload"]))
            ),
        }
        values[path.name] = {"raw": set(raw), "canonical": set(normalized)}
    report["official_train_test_overlap"] = {
        key: len(values["payload_train.csv"][key] & values["payload_test.csv"][key])
        for key in ("raw", "canonical")
    }
    report["source_document_hashes"] = {
        name: digest(source / name) for name in ("README.md", "LICENSE")
    }
    report["source_commit"] = commit
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    write_json("results/source_audit.json", audit_source(args.source))
