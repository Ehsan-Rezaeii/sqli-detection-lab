"""SQLi label 1 metrics; undefined denominators produce JSON null."""

import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix


def ratio(a, b):
    return float(a / b) if b else None


def metrics(y, prediction, score=None):
    tn, fp, fn, tp = (int(v) for v in confusion_matrix(y, prediction, labels=[0, 1]).ravel())
    return {
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "support": len(y),
        "prevalence": ratio(tp + fn, len(y)),
        "precision": ratio(tp, tp + fp),
        "recall": ratio(tp, tp + fn),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
        "fpr": ratio(fp, fp + tn),
        "ap": float(average_precision_score(y, score))
        if score is not None and len(set(y)) == 2
        else None,
    }


def objective(fold_metrics, fraction):
    means = {key: np.mean([m[key] or 0.0 for m in fold_metrics]) for key in ("f1", "fpr", "recall")}
    return float(
        0.50 * (1 - means["f1"])
        + 0.30 * means["fpr"]
        + 0.20 * (1 - means["recall"])
        + 0.02 * fraction
    )


def summarize(rows):
    return {
        key: {"mean": float(np.mean(values)), "sd": float(np.std(values, ddof=1))}
        for key in ("precision", "recall", "f1", "fpr", "ap")
        if (values := [r[key] for r in rows if r[key] is not None])
    }
