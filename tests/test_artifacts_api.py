from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from sqli_detection_lab.api import create_app
from sqli_detection_lab.artifacts import (
    load_model,
    save_model,
    source_hashes,
    verify_freeze,
    versions,
)
from sqli_detection_lab.io import read_json, write_json
from sqli_detection_lab.models import make_model


@pytest.fixture
def local_model(tmp_path):
    x = np.array(["ordinary", "catalogue", "union select", "select item from table"] * 3)
    y = np.tile([0, 0, 1, 1], 3)
    model = make_model("structural").fit(x, y)
    checksum = save_model(model, tmp_path / "results/models/structural.joblib")
    frozen = {
        "model_hashes": {"structural": checksum},
        "versions": versions(),
        "demo_method": "structural",
    }
    write_json(tmp_path / "results/freeze.json", frozen)
    return tmp_path, frozen


def test_load_and_tampering(local_model):
    root, frozen = local_model
    assert load_model(root, "structural", frozen).predict(["ordinary"]).shape == (1,)
    with pytest.raises(ValueError, match="trusted"):
        load_model(root, "arbitrary", frozen)
    path = root / "results/models/structural.joblib"
    path.write_bytes(path.read_bytes() + b"tamper")
    with patch("sqli_detection_lab.artifacts.joblib.load") as unsafe:
        with pytest.raises(ValueError, match="integrity"):
            load_model(root, "structural", frozen)
        unsafe.assert_not_called()


def test_version_check(local_model):
    root, frozen = local_model
    frozen["versions"] = {}
    with pytest.raises(ValueError, match="version"):
        load_model(root, "structural", frozen)


def test_freeze_code_and_evidence_integrity(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/module.py").write_text("value = 1\n")
    (tmp_path / "pyproject.toml").write_text("")
    frozen = {
        "source_hashes": source_hashes(tmp_path),
        "evidence_hashes": {},
        "model_hashes": {},
        "versions": versions(),
    }
    write_json(tmp_path / "results/freeze.json", frozen)
    verify_freeze(tmp_path, committed=False)
    (tmp_path / "src/module.py").write_text("value = 2\n")
    with pytest.raises(ValueError, match="source changed"):
        verify_freeze(tmp_path, committed=False)


def test_api_validation_and_no_training(local_model):
    root, frozen = local_model
    with patch("sqli_detection_lab.api.verify_freeze", return_value=frozen):
        with patch(
            "sklearn.linear_model.LogisticRegression.fit", side_effect=AssertionError("training")
        ):
            with TestClient(create_app(root)) as client:
                assert client.get("/health").status_code == 200
                for value in ("", "é ١ Ａ", "%27%20", "union select item from table", "x" * 2048):
                    response = client.post("/predict", json={"value": value})
                    assert response.status_code == 200
                    data = response.json()
                    assert data["label"] in ("norm", "sqli")
                    assert 0 <= data["score"] <= 1
                    assert "not a prevention or WAF" in data["warning"]
                    assert client.post("/predict", json={"value": value}).json() == data
                for value in (1, None, [], "x" * 2049):
                    assert client.post("/predict", json={"value": value}).status_code == 422
                assert client.post("/predict", json={"value": "x", "url": "x"}).status_code == 422
                assert client.post("/predict", content="not-json").status_code == 422


def test_api_missing_model(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/health").status_code == 503
        assert client.post("/predict", json={"value": "inert"}).status_code == 503


@pytest.mark.final
def test_final_artifacts():
    from sqli_detection_lab.artifacts import audit

    root = Path(__file__).resolve().parents[1]
    if not (root / "results/final/completion.json").exists():
        pytest.skip("Pre-final phase: artifacts absent; final-head CI requires finalized artifacts")
    report = audit(root, require_final=True)
    assert report["status"] == "passed"
    frozen = read_json(root / "results/freeze.json")
    with TestClient(create_app(root)) as client:
        assert client.get("/health").status_code == 200
        result = client.post("/predict", json={"value": "synthetic ordinary catalogue"})
        assert result.status_code == 200
        assert result.json()["model_id"].startswith(frozen["demo_method"] + ":")
