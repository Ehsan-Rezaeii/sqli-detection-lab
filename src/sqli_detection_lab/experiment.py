"""Development, explicit freeze, and one-shot final study orchestration."""

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_limits

from .artifacts import git, load_model, save_model, source_hashes, verify_freeze, versions
from .data import describe, folds, parse, prepare, stress_group
from .features import NAMES
from .io import digest, read_json, write_json
from .metrics import metrics, summarize
from .models import LR_CONFIG, METHODS, SEARCHES, TEXT_CONFIG, make_model, representation, scores
from .selection import choose_seed, optimizer, search


def utc():
    return datetime.now(timezone.utc).isoformat()


def evaluate(model, x, y, groups):
    start = perf_counter()
    score = scores(model, x)
    prediction = model.predict(x) if score is None else (score >= 0.5).astype(int)
    seconds = perf_counter() - start
    unique = np.unique(groups, return_index=True)[1]
    strata = {}
    lengths = np.array([len(t) for t in x])
    encoded = np.array([bool(re.search(r"%[0-9a-fA-F]{2}", t)) for t in x])
    keyword = np.array([bool(re.search(r"\b(?:select|union|sleep)\b", t, re.I)) for t in x])
    for key, mask in {
        "length_le_20": lengths <= 20,
        "length_21_100": (lengths > 20) & (lengths <= 100),
        "length_gt_100": lengths > 100,
        "percent_encoded": encoded,
        "no_percent_encoded": ~encoded,
        "keyword": keyword,
        "no_keyword": ~keyword,
    }.items():
        strata[key] = metrics(y[mask], prediction[mask], None if score is None else score[mask])
    # Cold single-item inference, separate from full-batch amortized latency.
    start = perf_counter()
    for value in x[: min(100, len(x))]:
        model.predict([value])
    single_seconds = (perf_counter() - start) / min(100, len(x))
    row = {
        "metrics": metrics(y, prediction, score),
        "group_representative_metrics": metrics(
            y[unique], prediction[unique], None if score is None else score[unique]
        ),
        "strata": strata,
        "predict_seconds": seconds,
        "batch_seconds_per_item": seconds / len(x),
        "single_seconds_per_item": single_seconds,
        "representation": representation(model, x),
    }
    return row, prediction if score is None else score


def fit_evaluate(method, mask, x, y, groups, train, valid):
    model = make_model(method, mask)
    start = perf_counter()
    model.fit(x[train], y[train])
    elapsed = perf_counter() - start
    row, _ = evaluate(model, x[valid], y[valid], groups[valid])
    row.update(
        {
            "fit_seconds": elapsed,
            "classifier_fits": int(method != "rules"),
            "objective_evaluations": 0,
        }
    )
    return row


def development(raw: Path, root: Path):
    output = root / "results"
    if (output / "freeze.json").exists():
        raise ValueError(
            "A frozen study cannot be overwritten; use a new checkout/results directory"
        )
    cohort, dev, _ = prepare(raw, output)
    x, y, groups = cohort.x[dev], cohort.y[dev], cohort.groups[dev]
    outer, split_rows = {m: [] for m in METHODS}, []
    split_indices = {"development": dev}
    for inner_index, (a, b) in enumerate(folds(y, groups)):
        split_indices[f"full_inner{inner_index}_train"] = dev[a]
        split_indices[f"full_inner{inner_index}_validation"] = dev[b]
    for index, (train, valid) in enumerate(folds(y, groups, seed=2028)):
        split_rows.append(
            {
                "train": describe(y, groups, train),
                "validation": describe(y, groups, valid),
                "group_overlap": 0,
            }
        )
        split_indices[f"outer{index}_train"] = dev[train]
        split_indices[f"outer{index}_validation"] = dev[valid]
        for inner_index, (a, b) in enumerate(folds(y[train], groups[train])):
            split_indices[f"outer{index}_inner{inner_index}_train"] = dev[train[a]]
            split_indices[f"outer{index}_inner{inner_index}_validation"] = dev[train[b]]
        for method in METHODS:
            print(f"outer={index} method={method}", flush=True)
            run = None
            if method in SEARCHES:
                run = search(method, x[train], y[train], groups[train], seed=0)
                write_json(output / f"development/trace_outer{index}_{method}.json", run)
            row = fit_evaluate(
                method, None if run is None else run["mask"], x, y, groups, train, valid
            )
            row["fold"] = index
            row["mask"] = None if run is None else run["mask"]
            row["objective_evaluations"] = 0 if run is None else run["objective_evaluations"]
            row["classifier_fits"] += 0 if run is None else run["classifier_fits"]
            row["search_seconds"] = 0 if run is None else run["seconds"]
            outer[method].append(row)
            write_json(output / "development/outer.json", outer)
    summary = {m: summarize([r["metrics"] for r in rows]) for m, rows in outer.items()}
    selected = min(METHODS, key=lambda m: (-summary[m]["f1"]["mean"], summary[m]["fpr"]["mean"], m))
    # Three full-development searches per optimizer, deterministic fitness tie breaking.
    masks, seed_variation = {}, {}
    for method in SEARCHES:
        runs = []
        for seed in (0, 1, 2):
            print(f"full-development method={method} seed={seed}", flush=True)
            run = search(method, x, y, groups, seed)
            write_json(output / f"development/trace_full_{method}_{seed}.json", run)
            runs.append(run)
        winner = choose_seed(runs)
        masks[method] = winner["mask"]
        seed_variation[method] = [
            {
                k: r[k]
                for k in (
                    "seed",
                    "fitness",
                    "mask",
                    "selected_count",
                    "objective_evaluations",
                    "classifier_fits",
                    "seconds",
                )
            }
            for r in runs
        ]
    sensitivity = sensitivity_diagnostic(x, y, groups, masks)
    hashes, final_fits = {}, {}
    for method in METHODS:
        model = make_model(method, masks.get(method))
        start = perf_counter()
        model.fit(x, y)
        final_fits[method] = {
            "seconds": perf_counter() - start,
            "classifier_fits": int(method != "rules"),
            "representation": representation(model, x),
            "parameters": str(model.get_params(deep=True)),
        }
        hashes[method] = save_model(model, output / f"models/{method}.joblib")
    np.savez_compressed(output / "development/split_indices.npz", **split_indices)
    write_json(output / "development/splits.json", split_rows)
    write_json(output / "development/summary.json", summary)
    write_json(
        output / "development/selection.json",
        {
            "demo_method": selected,
            "rule": "maximum mean outer F1, then minimum FPR, then name",
            "threshold": 0.5,
            "masks": masks,
            "seed_variation": seed_variation,
            "model_hashes": hashes,
            "full_development_fits": final_fits,
            "development_rows": len(y),
            "completed_at": utc(),
        },
    )
    write_json(output / "development/sensitivity.json", sensitivity)
    write_json(
        output / "environment.json",
        {
            "versions": versions(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    )
    return summary


def sensitivity_diagnostic(x, y, groups, masks):
    stress = np.array([stress_group(t) for t in x])
    # Predeclared stress grouping can merge distinct strings and even opposing classes.
    # Keep labels, group them together, and assess fixed nonsearch representations.
    rows = {m: [] for m in ("structural", "text", "hybrid")}
    overlap = []
    for train, valid in folds(y, groups, seed=2028):
        overlap.append(len(set(stress[train]) & set(stress[valid])))
    for train, valid in folds(y, stress, seed=2028):
        for method in rows:
            print(f"sensitivity method={method}", flush=True)
            row = fit_evaluate(method, None, x, y, stress, train, valid)
            rows[method].append(row)
    return {
        "group_definition": "NFKC/casefold; retain alphanumeric; digit runs to 0",
        "primary_groups": len(set(groups)),
        "stress_groups": len(set(stress)),
        "stress_group_overlap_in_primary_outer_folds": overlap,
        "stress_cv": rows,
        "scope": "Development-only fixed representations; no search or winner changes.",
    }


def freeze(root):
    if git(root, "status", "--porcelain"):
        raise ValueError("Commit all development source/evidence before freezing")
    selection = read_json(root / "results/development/selection.json")
    evidence = sorted((root / "results/development").glob("*.json"))
    evidence += sorted((root / "results/development").glob("*.npz"))
    evidence += [
        root / f"results/{n}.json"
        for n in ("dataset_manifest", "split_manifest", "environment", "source_audit")
    ]
    evidence += [
        p
        for p in (
            root / "results/feature_schema.json",
            root / "results/requirements-observed.txt",
            root / "docs/EXPERIMENT_PROTOCOL.md",
            root / "docs/PROJECT_SPEC.md",
        )
        if p.exists()
    ]
    configs = {}
    for method in SEARCHES:
        _, config = optimizer(method)
        config["optimize_kwargs"] = {"max_evaluations": 60, "seeds": [0, 1, 2], "outer_seed": 0}
        configs[method] = config
    value = {
        "created_at": utc(),
        "development_commit": git(root, "rev-parse", "HEAD"),
        "source_hashes": source_hashes(root),
        "versions": versions(),
        "evidence_hashes": {str(p.relative_to(root)): digest(p) for p in evidence},
        "model_hashes": selection["model_hashes"],
        "demo_method": selection["demo_method"],
        "masks": selection["masks"],
        "features": list(NAMES),
        "lr": LR_CONFIG,
        "text": TEXT_CONFIG,
        "kbest": {"score_func": "f_classif", "k": 8},
        "optimizer_configurations": configs,
        "threshold": 0.5,
        "api_max_length": 2048,
        "class_mapping": {"norm": 0, "sqli": 1},
        "objective": ".50*(1-F1)+.30*FPR+.20*(1-Recall)+.02*feature_fraction",
        "empty_mask_penalty": 1.02,
        "cache_masks": False,
        "protocol": read_json(root / "results/split_manifest.json"),
    }
    write_json(root / "results/freeze.json", value)
    return value


def final(raw, root):
    frozen = verify_freeze(root)
    if git(root, "status", "--porcelain"):
        raise ValueError("Final scoring requires clean committed freeze")
    if not git(root, "branch", "-r", "--contains", "HEAD"):
        raise ValueError("Push freeze before final scoring")
    output = root / "results/final"
    output.mkdir(parents=True, exist_ok=True)
    marker = output / "started.json"
    with marker.open("x") as file:
        import json

        json.dump(
            {
                "started_at": utc(),
                "freeze_commit": git(root, "rev-parse", "HEAD"),
                "freeze_sha256": digest(root / "results/freeze.json"),
            },
            file,
            indent=2,
        )
    # No final optimizer fitting, model selection or threshold changes.
    cohort = parse(raw)
    dev, test = folds(cohort.y, cohort.groups, n_splits=5, seed=2027)[0]
    if describe(cohort.y, cohort.groups, test) != frozen["protocol"]["test"]:
        raise ValueError("Final split mismatch")
    result = {}
    for method in METHODS:
        model = load_model(root, method, frozen)
        row, score = evaluate(model, cohort.x[test], cohort.y[test], cohort.groups[test])
        row["classifier_fits"] = 0
        row["objective_evaluations"] = 0
        result[method] = row
        # Unlinked aggregate score/label counts permit exact independent metric audits.
        values, inverse = np.unique(score, return_inverse=True)
        counts = [np.bincount(inverse[cohort.y[test] == c], minlength=len(values)) for c in (0, 1)]
        np.savez_compressed(
            output / f"scores_{method}.npz", score=values, norm=counts[0], sqli=counts[1]
        )
    write_json(output / "metrics.json", result)
    files = list(output.glob("*.npz")) + [marker, output / "metrics.json"]
    write_json(
        output / "completion.json",
        {
            "completed_at": utc(),
            "final_passes": 1,
            "freeze_sha256": digest(root / "results/freeze.json"),
            "artifact_hashes": {str(p.relative_to(root)): digest(p) for p in files},
        },
    )
    return result


def run_limited(function, *args):
    # Avoid BLAS oversubscription; reproducible single-thread numerical execution.
    with threadpool_limits(limits=1):
        return function(*args)
