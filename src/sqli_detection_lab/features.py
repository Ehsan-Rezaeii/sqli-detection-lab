"""Twenty deterministic string features; no dataset metadata is accepted."""

import re
import string

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

NAMES = (
    "length",
    "digit_ratio",
    "letter_ratio",
    "space_ratio",
    "punctuation_ratio",
    "single_quotes",
    "double_quotes",
    "parentheses",
    "semicolons",
    "equals",
    "dash_comments",
    "block_comments",
    "hashes",
    "backslashes",
    "percent_encoded",
    "tokens",
    "sql_keywords",
    "boolean_keywords",
    "unique_char_ratio",
    "non_ascii_ratio",
)
SQL = re.compile(r"\b(?:select|union|insert|update|delete|drop|from|where|sleep|benchmark)\b", re.I)
BOOL = re.compile(r"\b(?:or|and|not|true|false|null)\b", re.I)
PERCENT = re.compile(r"%[0-9a-fA-F]{2}")


def row_features(value: str) -> list[float]:
    n = len(value)
    denominator = max(1, n)
    return [
        n,
        sum(c.isdigit() for c in value) / denominator,
        sum(c.isalpha() for c in value) / denominator,
        sum(c.isspace() for c in value) / denominator,
        sum(c in string.punctuation for c in value) / denominator,
        value.count("'"),
        value.count('"'),
        value.count("(") + value.count(")"),
        value.count(";"),
        value.count("="),
        value.count("--"),
        value.count("/*") + value.count("*/"),
        value.count("#"),
        value.count("\\"),
        len(PERCENT.findall(value)),
        len(value.split()),
        len(SQL.findall(value)),
        len(BOOL.findall(value)),
        len(set(value)) / denominator,
        sum(ord(c) > 127 for c in value) / denominator,
    ]


class Structural(BaseEstimator, TransformerMixin):
    def fit(self, x, y=None):
        self.n_features_out_ = len(NAMES)
        return self

    def transform(self, x):
        return np.asarray([row_features(str(v)) for v in x], dtype=np.float64).reshape(
            -1, len(NAMES)
        )

    def get_feature_names_out(self, input_features=None):
        return np.array(NAMES, dtype=object)


class Mask(BaseEstimator, TransformerMixin):
    def __init__(self, mask):
        self.mask = mask

    def fit(self, x, y=None):
        bits = np.asarray(self.mask)
        if bits.shape != (x.shape[1],) or not np.isin(bits, [0, 1]).all() or not bits.any():
            raise ValueError("Mask must be nonempty and binary with the structural dimension")
        return self

    def transform(self, x):
        return x[:, np.asarray(self.mask, dtype=bool)]
