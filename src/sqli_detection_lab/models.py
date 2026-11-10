"""Fixed comparators with fold-local fitting and sparse text/hybrid transforms."""

import re

import numpy as np
from scipy import sparse
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler

from .features import Mask, Structural

LR_CONFIG = {"solver": "liblinear", "C": 1.0, "max_iter": 1000, "random_state": 2030}
TEXT_CONFIG = {
    "analyzer": "char",
    "ngram_range": (2, 5),
    "max_features": 40000,
    "min_df": 2,
    "sublinear_tf": True,
}
METHODS = ("rules", "structural", "text", "hybrid", "kbest", "ga", "gwo_s", "gwo_v", "random")
SEARCHES = METHODS[5:]
# Fixed bounded token/substring checks; no decoding, query construction or execution.
RULE = re.compile(
    r"\b(?:union\s{1,32}select|select\s{1,32}[^\n]{1,256}?\s{1,32}from|sleep\s{0,32}\(|benchmark\s{0,32}\()",
    re.I,
)
BOOLEAN_RULE = re.compile(r"\b(?:or|and)\s{1,32}\d{1,10}\s{0,32}=\s{0,32}\d{1,10}\b", re.I)


class Rules(ClassifierMixin, BaseEstimator):
    def fit(self, x, y=None):
        self.classes_ = np.array([0, 1])
        return self

    def predict(self, x):
        return np.array([int(bool(RULE.search(t) or BOOLEAN_RULE.search(t))) for t in x])


def structural_steps(mask=None, kbest=False):
    steps = [("extract", Structural())]
    if mask is not None:
        steps.append(("mask", Mask(mask)))
    if kbest:
        steps.append(("select", SelectKBest(f_classif, k=8)))
    steps.append(("scale", StandardScaler()))
    return steps


def make_model(method, mask=None):
    if method == "rules":
        return Rules()
    if method not in METHODS:
        raise ValueError("Unknown method")
    if method in SEARCHES and mask is None:
        raise ValueError("Search model requires an explicit frozen mask")
    if method == "text":
        steps = [("features", TfidfVectorizer(**TEXT_CONFIG))]
    elif method == "hybrid":
        steps = [
            (
                "features",
                FeatureUnion(
                    [
                        ("structural", Pipeline(structural_steps())),
                        ("text", TfidfVectorizer(**TEXT_CONFIG)),
                    ]
                ),
            )
        ]
    else:
        steps = structural_steps(mask=mask, kbest=method == "kbest")
    return Pipeline(steps + [("lr", LogisticRegression(**LR_CONFIG))])


def scores(model, x):
    if isinstance(model, Rules):
        return None
    index = list(model.classes_).index(1)
    return model.predict_proba(x)[:, index]


def representation(model, x):
    if isinstance(model, Rules):
        return {"vector_dimension": 0, "matrix_bytes": 0, "sparse": False, "selected_count": 0}
    matrix = model[:-1].transform(x)
    is_sparse = sparse.issparse(matrix)
    if is_sparse:
        matrix = matrix.tocsr()
        size = matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
    else:
        size = matrix.nbytes
    dimension = matrix.shape[1]
    return {
        "vector_dimension": dimension,
        "matrix_bytes": size,
        "sparse": is_sparse,
        "selected_count": (
            0
            if "features" in model.named_steps and isinstance(model["features"], TfidfVectorizer)
            else 20
            if dimension > 20
            else dimension
        ),
    }
