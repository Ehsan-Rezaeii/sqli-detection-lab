import csv
from unittest.mock import patch

import numpy as np
import pytest
from scipy import sparse
from sklearn.preprocessing import StandardScaler

from sqli_detection_lab.data import HEADER, acquire, canonical, folds, parse
from sqli_detection_lab.features import NAMES, Mask, Structural
from sqli_detection_lab.metrics import metrics, objective
from sqli_detection_lab.models import METHODS, SEARCHES, make_model, representation, scores
from sqli_detection_lab.selection import Objective, choose_seed, optimizer, search


@pytest.fixture
def synthetic():
    x = np.array(
        [f"ordinary item {i}" for i in range(18)]
        + [f"synthetic union select item from table {i}" for i in range(18)],
        dtype=object,
    )
    y = np.repeat([0, 1], 18)
    return x, y, np.array([str(i) for i in range(36)])


def test_csv_labels_conflicts_and_duplicates(tmp_path):
    path = tmp_path / "source.csv"
    rows = [
        ("a,\nquoted", "norm", "norm"),
        ("A", "norm", "norm"),
        ("a", "sqli", "anom"),
        ("duplicate", "norm", "norm"),
        ("duplicate", "norm", "norm"),
        ("other attack", "xss", "anom"),
        ("", "norm", "norm"),
        ("UNION SELECT", "sqli", "anom"),
    ]
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for text, category, label in rows:
            writer.writerow([text, len(text), category, label])
    data = parse(path, verify=False)
    assert data.manifest["conflict_groups"] == 1
    assert data.manifest["quarantined_by_class"] == {"0": 1, "1": 1}
    assert data.manifest["invalid_primary_rows"] == 1
    assert len(data.y) == 4
    assert list(data.y) == [0, 0, 0, 1]
    assert data.x[0] == "a,\nquoted"
    assert data.manifest["raw_duplicate_excess_primary"] == 1
    with pytest.raises(ValueError, match="integrity"):
        acquire(tmp_path / "raw", offline=path)
    path.write_text("payload,length,attack_type,label\na,1,sqli,norm\n")
    with pytest.raises(ValueError, match="Inconsistent"):
        parse(path, verify=False)
    path.write_text("wrong,header\n")
    with pytest.raises(ValueError, match="header"):
        parse(path, verify=False)


def test_grouping_and_splits(synthetic):
    assert canonical(" Ａ \tB\n") == "a b"
    x, y, groups = synthetic
    groups = np.array([str(i // 2) for i in range(36)])
    first = folds(y, groups)
    second = folds(y, groups)
    for (a, b), (c, d) in zip(first, second, strict=True):
        assert not set(groups[a]) & set(groups[b])
        np.testing.assert_array_equal(a, c)
        np.testing.assert_array_equal(b, d)


def test_feature_robustness():
    x = ["", "é ١ Ａ", "%27%20'", "x" * 100000]
    matrix = Structural().fit_transform(x)
    assert matrix.shape == (4, 20)
    assert np.isfinite(matrix).all()
    assert list(Structural().get_feature_names_out()) == list(NAMES)
    assert matrix[0, 0] == 0
    assert matrix[2, 14] == 2
    with pytest.raises(ValueError, match="nonempty"):
        Mask([0] * 20).fit(matrix)


def test_metric_definitions_and_direction():
    row = metrics([0, 0, 0, 1, 1], [0, 0, 1, 0, 1], [0.1, 0.2, 0.8, 0.4, 0.9])
    assert (row["tn"], row["fp"], row["fn"], row["tp"]) == (2, 1, 1, 1)
    assert row["precision"] == 0.5 and row["recall"] == 0.5
    assert row["fpr"] == 1 / 3 and row["f1"] == 0.5
    assert objective([row] * 3, 0.5) == pytest.approx(0.46)
    assert metrics([0], [0])["precision"] is None
    assert metrics([1], [1])["fpr"] is None


@pytest.mark.parametrize("method", SEARCHES)
def test_actual_constructor_and_budget_kwargs(method, synthetic):
    from metaheuristics_lab import BinaryGA, BinaryGWO, RandomSearch

    import sqli_detection_lab.selection as module

    constructor = {"ga": BinaryGA, "gwo_s": BinaryGWO, "gwo_v": BinaryGWO, "random": RandomSearch}[
        method
    ]
    with patch.object(module, constructor.__name__, wraps=constructor) as factory:
        instance, config = optimizer(method)
        assert factory.call_args.kwargs["population_size"] == 12
        assert instance.population_size == 12 and instance.domain == "binary"
        if method.startswith("gwo"):
            assert instance.transfer == method[-1]
        if method == "random":
            assert factory.call_args.kwargs["domain"] == "binary"
        assert config["instance_attributes"]["population_size"] == 12
    x, y, groups = synthetic
    with patch.object(
        constructor, "optimize", autospec=True, side_effect=constructor.optimize
    ) as call:
        first = search(method, x, y, groups, 0)
        assert call.call_args.kwargs == {"max_evaluations": 60, "seed": 0}
    second = search(method, x, y, groups, 0)
    assert first["mask"] == second["mask"]
    assert first["history"] == second["history"]
    assert first["objective_evaluations"] == 60
    assert first["classifier_fits"] == 3 * sum(bool(sum(r["mask"])) for r in first["trace"])
    assert first["configuration"]["optimize_kwargs"] == {"max_evaluations": 60, "seed": 0}


def test_empty_mask_and_fold_locality(synthetic):
    x, y, groups = synthetic
    fits = []
    original = StandardScaler.fit

    def spy(self, matrix, *args, **kwargs):
        fits.append(matrix.copy())
        return original(self, matrix, *args, **kwargs)

    with patch.object(StandardScaler, "fit", spy):
        target = Objective(x, y, groups)
    matrix = Structural().fit_transform(x)
    for observed, (train, _valid) in zip(fits, folds(y, groups), strict=True):
        np.testing.assert_array_equal(observed, matrix[train])
    assert target(np.zeros(20)) == 1.02
    assert target.calls == 1 and target.fits == 0
    with pytest.raises(ValueError, match="Invalid"):
        target(np.zeros(21))


def test_sparse_and_training_only_vocabulary(synthetic):
    x, y, groups = synthetic
    for method in ("text", "hybrid"):
        model = make_model(method).fit(x, y)
        assert sparse.issparse(model[:-1].transform(["unseen ΩΩΩΩ"]))
        before = model[:-1].transform(["unseen ΩΩΩΩ"]).shape[1]
        assert before == model[:-1].transform(x).shape[1]
        transformer = model["features"]
        vectorizer = transformer if method == "text" else dict(transformer.transformer_list)["text"]
        assert not any("Ω" in key for key in vectorizer.vocabulary_)
        assert representation(model, x)["sparse"] is True
        assert scores(model, [x[0], x[-1]])[0] < scores(model, [x[0], x[-1]])[1]


def test_all_baselines_and_seed_selection(synthetic):
    x, y, _ = synthetic
    for method in METHODS:
        model = make_model(method, [1] * 20 if method in SEARCHES else None).fit(x, y)
        assert set(model.predict(x)) <= {0, 1}
    assert make_model("rules").fit(x, y).predict(["union select 1", "catalogue"]).tolist() == [1, 0]
    runs = [{"fitness": 1, "selected_count": 2, "seed": s, "mask": [1, 1]} for s in [2, 0, 1]]
    assert choose_seed(runs)["seed"] == 0
