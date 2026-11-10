"""Run actual validation commands, save outputs and exit codes, fail on any error."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"


def run(name, args, *, cwd=ROOT):
    output = ROOT / "results/verification"
    output.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    with (output / f"{name}.txt").open("w") as file:
        result = subprocess.run(
            args,
            cwd=cwd,
            stdout=file,
            stderr=subprocess.STDOUT,
            env={**os.environ, "MPLBACKEND": "Agg"},
        )
    entry = {
        "name": name,
        "argv": [str(a) for a in args],
        "cwd": str(cwd),
        "exit_code": result.returncode,
        "seconds": perf_counter() - start,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    with (output / "commands.jsonl").open("a") as file:
        file.write(json.dumps(entry) + "\n")
    print(name, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    run("ruff_lint", [PYTHON, "-m", "ruff", "check", "."])
    run("ruff_format", [PYTHON, "-m", "ruff", "format", "--check", "."])
    run(
        "pytest",
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "--cov=sqli_detection_lab",
            "--cov-report=term-missing",
            "--cov-report=json:results/verification/coverage.json",
        ],
    )
    run("smoke", [ROOT / ".venv/bin/sqli-lab", "smoke"])
    if "--final" in sys.argv:
        run("artifact_audit", [ROOT / ".venv/bin/sqli-lab", "audit", "--require-final"])
    run("build", [PYTHON, "-m", "build"])
    wheel_env = ROOT / ".venv/wheel-check"
    run("wheel_venv", [PYTHON, "-m", "venv", wheel_env])
    run("wheel_install", [wheel_env / "bin/pip", "install", *sorted((ROOT / "dist").glob("*.whl"))])
    run(
        "wheel_package_refresh",
        [
            wheel_env / "bin/pip",
            "install",
            "--force-reinstall",
            "--no-deps",
            *sorted((ROOT / "dist").glob("*.whl")),
        ],
    )
    run(
        "wheel_import",
        [
            wheel_env / "bin/python",
            "-c",
            "from sqli_detection_lab.api import create_app; "
            "from metaheuristics_lab import BinaryGA; "
            "assert BinaryGA(population_size=12).population_size == 12; "
            "print(create_app().title)",
        ],
        cwd=Path("/tmp"),
    )


if __name__ == "__main__":
    main()
