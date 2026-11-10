from unittest.mock import patch

import pytest

from sqli_detection_lab.cli import main
from sqli_detection_lab.models import make_model, scores


def test_synthetic_smoke_cli(capsys):
    with patch("sys.argv", ["sqli-lab", "smoke"]):
        main()
    assert "synthetic_only" in capsys.readouterr().out


def test_explicit_class_direction():
    import numpy as np

    class Reversed:
        classes_ = [1, 0]

        def predict_proba(self, x):
            return np.array([[0.8, 0.2]])

    assert scores(Reversed(), ["inert"])[0] == 0.8
    with pytest.raises(ValueError, match="Unknown method"):
        make_model("unknown")
    with pytest.raises(ValueError, match="explicit frozen mask"):
        make_model("ga")
