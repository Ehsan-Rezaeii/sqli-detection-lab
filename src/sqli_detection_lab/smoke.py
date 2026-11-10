"""Explicitly synthetic-only end-to-end check, never scientific evidence."""

import numpy as np

from .metrics import metrics
from .models import METHODS, SEARCHES, make_model, scores
from .selection import search


def smoke():
    x = np.array(
        [f"ordinary catalogue item {i}" for i in range(18)]
        + [f"synthetic union select item from table {i}" for i in range(18)],
        dtype=object,
    )
    y = np.repeat([0, 1], 18)
    groups = np.array([str(i) for i in range(len(x))])
    evidence = {}
    for method in METHODS:
        run = search(method, x, y, groups, 0) if method in SEARCHES else None
        model = make_model(method, None if run is None else run["mask"]).fit(x, y)
        evidence[method] = {
            "synthetic_training_metrics": metrics(y, model.predict(x), scores(model, x)),
            "objective_evaluations": 0 if run is None else run["objective_evaluations"],
        }
    return {"synthetic_only": True, "methods": evidence}
