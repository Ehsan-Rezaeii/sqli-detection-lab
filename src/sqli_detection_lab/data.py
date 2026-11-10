"""Immutable acquisition and audits; dataset text is always inert and stays off Git."""

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from .io import digest, digest_bytes, write_json

DATA_COMMIT = "926670a710283f87c05b554680facf3f9530548c"
URL = f"https://raw.githubusercontent.com/Morzeux/HttpParamsDataset/{DATA_COMMIT}/payload_full.csv"
# Verified from raw bytes at the pinned source commit before training.
SHA256 = "a4e62ba13435ad3dd583c5790db2175629020fc41c56e1b26baa02a9ae45f03d"
BYTE_SIZE = 1996540
HEADER = ["payload", "length", "attack_type", "label"]
LABELS = {"norm": 0, "sqli": 1}


def canonical(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def group_id(value: str) -> str:
    return digest_bytes(canonical(value).encode())


def stress_group(value: str) -> str:
    value = "".join(c for c in canonical(value) if c.isalnum())
    return digest_bytes(re.sub(r"\d+", "0", value).encode())


def acquire(path: Path, *, offline: Path | None = None) -> Path:
    if offline is not None:
        raw = offline.read_bytes()
    elif path.exists():
        raw = path.read_bytes()
    else:
        with urlopen(URL, timeout=60) as response:
            raw = response.read(BYTE_SIZE + 1)
    if len(raw) != BYTE_SIZE or digest_bytes(raw) != SHA256:
        raise ValueError("Dataset integrity mismatch")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


@dataclass
class Cohort:
    x: np.ndarray
    y: np.ndarray
    groups: np.ndarray
    manifest: dict


def parse(path: Path, *, verify: bool = True) -> Cohort:
    if verify and (digest(path) != SHA256 or path.stat().st_size != BYTE_SIZE):
        raise ValueError("Dataset integrity mismatch")
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        if reader.fieldnames != HEADER:
            raise ValueError(f"Unexpected header: {reader.fieldnames}")
        rows = list(reader)
    counts, label_counts = Counter(), Counter()
    primary, invalid, mismatch = [], 0, 0
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed CSV row")
        counts[row["attack_type"]] += 1
        label_counts[row["label"]] += 1
        if row["attack_type"] not in {"norm", "sqli", "xss", "cmdi", "path-traversal"}:
            raise ValueError("Unknown attack category")
        expected = "norm" if row["attack_type"] == "norm" else "anom"
        if row["label"] != expected:
            raise ValueError("Inconsistent attack_type/label")
        try:
            mismatch += int(int(row["length"]) != len(row["payload"]))
        except ValueError as exc:
            raise ValueError("Invalid length metadata") from exc
        if row["attack_type"] in LABELS:
            if not row["payload"] or len(row["payload"]) > 100000:
                invalid += 1
                continue
            primary.append((row["payload"], LABELS[row["attack_type"]]))
    targets = defaultdict(set)
    for text, y in primary:
        targets[group_id(text)].add(y)
    conflicts = {g for g, ys in targets.items() if len(ys) > 1}
    quarantined = Counter(str(y) for text, y in primary if group_id(text) in conflicts)
    retained = [(text, y) for text, y in primary if group_id(text) not in conflicts]
    x = np.array([t for t, y in retained], dtype=object)
    y = np.array([y for t, y in retained], dtype=int)
    groups = np.array([group_id(t) for t in x])
    raw = Counter(t for t, y in primary)
    normalized = Counter(group_id(t) for t, y in primary)
    manifest = {
        "source_commit": DATA_COMMIT,
        "url": URL,
        "sha256": digest(path),
        "bytes": path.stat().st_size,
        "encoding": "utf-8",
        "header": HEADER,
        "records": len(rows),
        "attack_types": dict(counts),
        "labels": dict(label_counts),
        "length_metadata_mismatches": mismatch,
        "invalid_primary_rows": invalid,
        "all_empty_values": sum(not r["payload"] for r in rows),
        "max_length": max(len(r["payload"]) for r in rows),
        "raw_duplicate_excess_primary": sum(n - 1 for n in raw.values()),
        "canonical_duplicate_excess_primary": sum(n - 1 for n in normalized.values()),
        "raw_duplicated_groups_primary": sum(n > 1 for n in raw.values()),
        "canonical_duplicated_groups_primary": sum(n > 1 for n in normalized.values()),
        "conflict_groups": len(conflicts),
        "quarantined_by_class": dict(quarantined),
        "retained_rows": len(y),
        "retained_groups": len(set(groups)),
        "retained_class_counts": {str(c): int(sum(y == c)) for c in (0, 1)},
        "rights": "Upstream MIT; constituent rights not fully verified. No raw redistribution.",
        "policy": (
            "Quarantine empty/over-100000-character rows and entire conflicting groups; "
            "retain duplicates."
        ),
    }
    return Cohort(x, y, groups, manifest)


def folds(y, groups, *, n_splits=3, seed=2029):
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    pairs = list(splitter.split(np.zeros(len(y)), y, groups))
    for train, valid in pairs:
        if set(groups[train]) & set(groups[valid]):
            raise ValueError("Group overlap")
        if len(set(y[train])) != 2 or len(set(y[valid])) != 2:
            raise ValueError("Insufficient class support")
    return pairs


def describe(y, groups, indices):
    return {
        "rows": len(indices),
        "groups": len(set(groups[indices])),
        "class_counts": {str(c): int(sum(y[indices] == c)) for c in (0, 1)},
        "index_sha256": digest_bytes(np.asarray(indices, dtype="<i8").tobytes()),
        "group_sha256": digest_bytes("\n".join(sorted(set(groups[indices]))).encode()),
    }


def prepare(path: Path, output: Path):
    cohort = parse(path)
    dev, test = folds(cohort.y, cohort.groups, n_splits=5, seed=2027)[0]
    manifest = {
        "development": describe(cohort.y, cohort.groups, dev),
        "test": describe(cohort.y, cohort.groups, test),
        "group_overlap": 0,
        "protocol": "SGKF 5/2027 fold 0 holdout; outer 3/2028; inner 3/2029",
    }
    write_json(output / "dataset_manifest.json", cohort.manifest)
    write_json(output / "split_manifest.json", manifest)
    # Indices and group hashes stay local; public evidence contains aggregate hashes only.
    np.savez_compressed(path.parent / "split_indices.npz", development=dev, test=test)
    return cohort, dev, test
