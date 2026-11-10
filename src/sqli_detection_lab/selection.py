"""Adapter for the installed, pinned Project 1 optimizers. No optimizer implementation."""

import inspect
from time import perf_counter

import numpy as np
from metaheuristics_lab import BinaryGA, BinaryGWO, Problem, RandomSearch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .data import describe, folds
from .features import NAMES, Structural
from .metrics import metrics, objective
from .models import LR_CONFIG

DEPENDENCY_COMMIT = "6b4ef0fa3d72f608146f3dd7eabb84bf39fa896e"


def optimizer(method):
    if method == "ga":
        constructor, kwargs = BinaryGA, {"population_size": 12}
    elif method in ("gwo_s", "gwo_v"):
        constructor, kwargs = BinaryGWO, {"population_size": 12, "transfer": method[-1]}
    elif method == "random":
        constructor, kwargs = RandomSearch, {"population_size": 12, "domain": "binary"}
    else:
        raise ValueError("Unknown search method")
    instance = constructor(**kwargs)
    bound = inspect.signature(type(instance)).bind(**kwargs)
    bound.apply_defaults()
    config = {
        "class": type(instance).__name__,
        "constructor_kwargs": kwargs,
        "constructor_with_defaults": dict(bound.arguments),
        "instance_attributes": vars(instance).copy(),
        "domain": instance.domain,
        "dependency_commit": DEPENDENCY_COMMIT,
    }
    return instance, config


class Objective:
    """Scaler fitted once per inner training fold; no mask/objective caching.

    Structural extraction is stateless. Columnwise scaling commutes with masking,
    so sharing these fold-local scaled arrays does not share learned information
    across folds or masks. Each nonempty objective still fits three fresh LRs.
    """

    def __init__(self, x, y, groups):
        self.y = y
        matrix = Structural().fit_transform(x)
        self.fold_data, self.splits = [], []
        for train, valid in folds(y, groups):
            scaler = StandardScaler().fit(matrix[train])
            self.fold_data.append(
                (train, valid, scaler.transform(matrix[train]), scaler.transform(matrix[valid]))
            )
            self.splits.append(
                {
                    "train": describe(y, groups, train),
                    "validation": describe(y, groups, valid),
                    "group_overlap": 0,
                }
            )
        self.calls, self.fits, self.trace = 0, 0, []

    def __call__(self, raw_mask):
        mask = np.asarray(raw_mask)
        if mask.shape != (len(NAMES),) or not np.isin(mask, [0, 1]).all():
            raise ValueError("Invalid structural mask")
        mask = mask.astype(bool)
        self.calls += 1
        fold_results = []
        if not mask.any():
            value = 1.02
        else:
            for train, valid, a, b in self.fold_data:
                model = LogisticRegression(**LR_CONFIG).fit(a[:, mask], self.y[train])
                self.fits += 1
                score = model.predict_proba(b[:, mask])[:, list(model.classes_).index(1)]
                fold_results.append(metrics(self.y[valid], (score >= 0.5).astype(int), score))
            value = objective(fold_results, float(mask.mean()))
        self.trace.append(
            {
                "evaluation": self.calls,
                "mask": mask.astype(int).tolist(),
                "fitness": value,
                "fold_metrics": fold_results,
                "cumulative_classifier_fits": self.fits,
            }
        )
        return value


def search(method, x, y, groups, seed):
    instance, config = optimizer(method)
    config["optimize_kwargs"] = {"max_evaluations": 60, "seed": seed}
    start = perf_counter()
    target = Objective(x, y, groups)
    result = instance.optimize(Problem.binary(target, len(NAMES)), **config["optimize_kwargs"])
    if target.calls != result.n_evaluations or target.calls != 60:
        raise RuntimeError("Optimizer violated objective budget")
    return {
        "method": method,
        "seed": seed,
        "configuration": config,
        "mask": result.best_solution.astype(int).tolist(),
        "fitness": result.best_fitness,
        "selected_count": int(sum(result.best_solution)),
        "objective_evaluations": target.calls,
        "classifier_fits": target.fits,
        "seconds": perf_counter() - start,
        "history": result.history.tolist(),
        "trace": target.trace,
        "inner_splits": target.splits,
    }


def choose_seed(runs):
    return min(runs, key=lambda r: (r["fitness"], r["selected_count"], r["seed"], r["mask"]))
