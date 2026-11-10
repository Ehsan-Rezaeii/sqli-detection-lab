"""Trusted local artifact checks. Hashes are integrity checks, not signatures."""

import importlib.metadata
import subprocess
from pathlib import Path

import joblib

from .io import digest, read_json, write_json

PACKAGES = ("numpy", "scipy", "scikit-learn", "metaheuristics-lab", "sqli-detection-lab")


def versions():
    import json

    from .selection import DEPENDENCY_COMMIT

    direct = importlib.metadata.distribution("metaheuristics-lab").read_text("direct_url.json")
    info = json.loads(direct or "{}")
    if info.get("vcs_info", {}).get("commit_id") != DEPENDENCY_COMMIT:
        raise ValueError("Installed optimizer is not the approved Git dependency")
    return {p: importlib.metadata.version(p) for p in PACKAGES}


def source_hashes(root):
    paths = (
        sorted((root / "src").rglob("*.py"))
        + sorted((root / "experiments").glob("*.py"))
        + [root / "pyproject.toml"]
    )
    return {str(p.relative_to(root)): digest(p) for p in paths}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def save_model(model, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path, compress=3)
    return digest(path)


def verify_freeze(root: Path, *, committed=True):
    path = root / "results/freeze.json"
    freeze = read_json(path)
    if committed:
        stored = subprocess.check_output(
            ["git", "-C", str(root), "show", "HEAD:results/freeze.json"]
        )
        if stored != path.read_bytes():
            raise ValueError("Freeze must be committed and unchanged")
    if source_hashes(root) != freeze["source_hashes"]:
        raise ValueError("Frozen source changed")
    for name, expected in freeze["evidence_hashes"].items():
        if digest(root / name) != expected:
            raise ValueError(f"Evidence integrity mismatch: {name}")
    for name, expected in freeze["model_hashes"].items():
        if digest(root / f"results/models/{name}.joblib") != expected:
            raise ValueError(f"Model integrity mismatch: {name}")
    if freeze["versions"] != versions():
        raise ValueError("Model runtime version mismatch")
    return freeze


def load_model(root, name, freeze=None):
    freeze = freeze or verify_freeze(root)
    if name not in freeze["model_hashes"]:
        raise ValueError("Model not in trusted freeze")
    path = root / f"results/models/{name}.joblib"
    if digest(path) != freeze["model_hashes"][name]:
        raise ValueError("Model integrity mismatch")
    if freeze["versions"] != versions():
        raise ValueError("Model runtime version mismatch")
    # Only locally produced files named in the trusted freeze may reach joblib.
    return joblib.load(path)


def audit(root, *, require_final=False):
    freeze = verify_freeze(root)
    from .metrics import objective

    total_calls, total_fits, traces = 0, 0, 0
    for path in sorted((root / "results/development").glob("trace_*.json")):
        run = read_json(path)
        config = run["configuration"]
        if (
            config["constructor_kwargs"]["population_size"] != 12
            or config["instance_attributes"]["population_size"] != 12
            or config["optimize_kwargs"]["max_evaluations"] != 60
            or len(run["trace"]) != 60
            or run["objective_evaluations"] != 60
        ):
            raise ValueError("Invalid optimizer budget/configuration")
        calls, fits, incumbent = 0, 0, float("inf")
        for row, history in zip(run["trace"], run["history"], strict=True):
            mask = row["mask"]
            if len(mask) != 20 or not set(mask) <= {0, 1}:
                raise ValueError("Invalid saved structural mask")
            count = sum(mask)
            expected = objective(row["fold_metrics"], count / 20) if count else 1.02
            calls += 1
            fits += 3 if count else 0
            incumbent = min(incumbent, expected)
            if (
                abs(expected - row["fitness"]) > 1e-12
                or abs(incumbent - history) > 1e-12
                or row["evaluation"] != calls
                or row["cumulative_classifier_fits"] != fits
            ):
                raise ValueError("Invalid saved objective/fit accounting")
        if fits != run["classifier_fits"] or abs(incumbent - run["fitness"]) > 1e-12:
            raise ValueError("Invalid search result accounting")
        total_calls += calls
        total_fits += fits
        traces += 1
    if traces != 24:
        raise ValueError("Expected 12 outer and 12 full-development searches")
    if require_final:
        completion = read_json(root / "results/final/completion.json")
        if completion["freeze_sha256"] != digest(root / "results/freeze.json"):
            raise ValueError("Final freeze mismatch")
        for name, expected in completion["artifact_hashes"].items():
            if digest(root / name) != expected:
                raise ValueError(f"Final artifact integrity mismatch: {name}")
        import numpy as np

        from .metrics import metrics

        final = read_json(root / "results/final/metrics.json")
        for name, row in final.items():
            with np.load(root / f"results/final/scores_{name}.npz", allow_pickle=False) as data:
                y = np.repeat([0, 1], [int(sum(data["norm"])), int(sum(data["sqli"]))])
                score = np.concatenate(
                    [np.repeat(data["score"], data["norm"]), np.repeat(data["score"], data["sqli"])]
                )
            reconstructed = metrics(y, score >= 0.5, None if name == "rules" else score)
            if reconstructed != row["metrics"]:
                raise ValueError(f"Saved-score metric mismatch: {name}")
        if set(final) != set(freeze["model_hashes"]):
            raise ValueError("Missing final methods")
    report = {
        "freeze_sha256": digest(root / "results/freeze.json"),
        "models_verified": list(freeze["model_hashes"]),
        "search_traces_verified": traces,
        "objective_evaluations": total_calls,
        "search_classifier_fits": total_fits,
        "final_required": require_final,
        "status": "passed",
    }
    write_json(root / "results/artifact_audit.json", report)
    return report
