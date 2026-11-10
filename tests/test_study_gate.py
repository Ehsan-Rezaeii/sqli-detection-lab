"""Exercise the real multi-stage study on synthetic strings in an isolated Git repo."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from sqli_detection_lab import experiment
from sqli_detection_lab.artifacts import audit, verify_freeze
from sqli_detection_lab.data import Cohort, describe, folds, group_id
from sqli_detection_lab.io import write_json


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def test_synthetic_study_freeze_and_single_final_gate(tmp_path, monkeypatch):
    root = tmp_path / "study"
    root.mkdir()
    source = Path(__file__).resolve().parents[1]
    shutil.copytree(
        source / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info")
    )
    shutil.copy(source / "pyproject.toml", root / "pyproject.toml")
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Synthetic Test")
    git(root, "config", "user.email", "synthetic@example.invalid")
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    git(root, "remote", "add", "origin", str(remote))
    x = np.array(
        [f"ordinary catalogue value {chr(97 + i // 26)}{chr(97 + i % 26)}" for i in range(30)]
        + [
            f"synthetic union select item from table {chr(97 + i // 26)}{chr(97 + i % 26)}"
            for i in range(30)
        ],
        dtype=object,
    )
    y = np.repeat([0, 1], 30)
    groups = np.array([group_id(t) for t in x])
    cohort = Cohort(x, y, groups, {"synthetic_only": True})
    dev, test = folds(y, groups, n_splits=5, seed=2027)[0]

    def prepare(raw, output):
        write_json(output / "dataset_manifest.json", {"synthetic_only": True})
        write_json(output / "source_audit.json", {"synthetic_only": True})
        write_json(
            output / "split_manifest.json",
            {
                "development": describe(y, groups, dev),
                "test": describe(y, groups, test),
                "group_overlap": 0,
                "synthetic_only": True,
            },
        )
        return cohort, dev, test

    monkeypatch.setattr(experiment, "prepare", prepare)
    monkeypatch.setattr(experiment, "parse", lambda raw: cohort)
    raw = root / "ignored_synthetic.csv"
    summary = experiment.development(raw, root)
    assert len(summary) == 9
    with pytest.raises(ValueError, match="Commit all"):
        experiment.freeze(root)
    git(root, "add", ".")
    git(root, "commit", "-m", "Synthetic development")
    experiment.freeze(root)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        verify_freeze(root)
    git(root, "add", ".")
    git(root, "commit", "-m", "Synthetic freeze")
    verify_freeze(root)
    with pytest.raises(ValueError, match="Push freeze"):
        experiment.final(raw, root)
    git(root, "push", "-u", "origin", "main")
    final = experiment.final(raw, root)
    assert len(final) == 9
    assert all(row["classifier_fits"] == 0 for row in final.values())
    assert audit(root, require_final=True)["status"] == "passed"
    with pytest.raises(ValueError, match="frozen study"):
        experiment.development(raw, root)
    git(root, "add", ".")
    git(root, "commit", "-m", "Synthetic final")
    git(root, "push")
    with pytest.raises(FileExistsError):
        experiment.final(raw, root)
    # The audit refuses even one altered byte in final evidence.
    path = root / "results/final/metrics.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Final artifact"):
        audit(root, require_final=True)
