"""Render measured evidence; never fit or select models and never load raw data."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sqli_detection_lab.features import NAMES
from sqli_detection_lab.io import read_json, write_json
from sqli_detection_lab.models import METHODS


def report(root=None):
    root = Path.cwd() if root is None else root
    results = root / "results"
    summary = read_json(results / "development/summary.json")
    selection = read_json(results / "development/selection.json")
    final = (
        read_json(results / "final/metrics.json")
        if (results / "final/metrics.json").exists()
        else None
    )
    plots = results / "plots"
    plots.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    positions = np.arange(len(METHODS))
    ax.bar(
        positions,
        [summary[m]["f1"]["mean"] for m in METHODS],
        yerr=[summary[m]["f1"]["sd"] for m in METHODS],
        label="Development outer mean ± SD",
    )
    if final:
        ax.scatter(
            positions,
            [final[m]["metrics"]["f1"] for m in METHODS],
            c="black",
            label="Single held-out pass",
            zorder=3,
        )
    ax.set(xticks=positions, xticklabels=METHODS, ylabel="SQLi-positive F1", ylim=(0, 1.03))
    ax.legend()
    fig.tight_layout()
    fig.savefig(plots / "f1.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    for method in ("ga", "gwo_s", "gwo_v", "random"):
        for seed in (0, 1, 2):
            trace = read_json(results / f"development/trace_full_{method}_{seed}.json")
            ax.plot(np.arange(1, 61), trace["history"], label=f"{method} / {seed}")
    ax.set(xlabel="Actual objective evaluations", ylabel="Best inner fitness (minimize)")
    ax.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(plots / "convergence.png", dpi=160)
    plt.close(fig)
    if final:
        chosen = selection["demo_method"]
        row = final[chosen]["metrics"]
        matrix = np.array([[row["tn"], row["fp"]], [row["fn"], row["tp"]]])
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.imshow(matrix, cmap="Blues")
        for (i, j), value in np.ndenumerate(matrix):
            ax.text(j, i, str(value), ha="center", va="center")
        ax.set(
            xticks=[0, 1],
            yticks=[0, 1],
            xticklabels=["norm", "sqli"],
            yticklabels=["norm", "sqli"],
            xlabel="Predicted",
            ylabel="Source label",
            title=f"Frozen demo: {chosen}",
        )
        fig.tight_layout()
        fig.savefig(plots / "confusion.png", dpi=160)
        plt.close(fig)
    lines = [
        "# Measured results",
        "",
        "All values below come from saved experiment artifacts.",
        "",
        f"Demo selected using development only: **{selection['demo_method']}**.",
        "",
        "## Development outer CV",
        "",
        "| Method | Precision | Recall | F1 mean ± sample SD | FPR | AP |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        row = summary[method]
        ap = f"{row['ap']['mean']:.6f}" if "ap" in row else "N/A"
        lines.append(
            f"| {method} | {row['precision']['mean']:.6f} | {row['recall']['mean']:.6f} | "
            f"{row['f1']['mean']:.6f} ± {row['f1']['sd']:.6f} | {row['fpr']['mean']:.6f} | {ap} |"
        )
    if final:
        lines += [
            "",
            "## One frozen held-out pass",
            "",
            "| Method | Precision | Recall | F1 | FPR | AP | TN/FP/FN/TP | Dim |",
            "|---|---:|---:|---:|---:|---:|---|---:|",
        ]
        for method in METHODS:
            row = final[method]["metrics"]
            ap = "N/A" if row["ap"] is None else f"{row['ap']:.6f}"
            counts = "/".join(str(row[k]) for k in ("tn", "fp", "fn", "tp"))
            dim = final[method]["representation"]["vector_dimension"]
            lines.append(
                f"| {method} | {row['precision']:.6f} | {row['recall']:.6f} | "
                f"{row['f1']:.6f} | {row['fpr']:.6f} | {ap} | {counts} | {dim} |"
            )
    lines += [
        "",
        "## Cost and seed variation",
        "",
        "Each search has 60 objective calls; each nonempty call fits three LRs.",
        "12 outer + 12 full-development searches use 1,440 objective calls.",
        "Nonsearch methods do not incur those costs. Final scoring performs no fits.",
        "",
        "| Method | Outer fits | Search s | Full-dev fits | Fitness seeds 0/1/2 | Features |",
        "|---|---:|---:|---:|---|---:|",
    ]
    outer = read_json(results / "development/outer.json")
    for method in METHODS:
        runs = selection["seed_variation"].get(method, [])
        fitness = "/".join(f"{r['fitness']:.6f}" for r in runs) or "N/A"
        fits = (
            sum(r["classifier_fits"] for r in runs)
            + selection["full_development_fits"][method]["classifier_fits"]
        )
        count = selection["full_development_fits"][method]["representation"]["selected_count"]
        lines.append(
            f"| {method} | {sum(r['classifier_fits'] for r in outer[method])} | "
            f"{sum(r['search_seconds'] for r in outer[method]):.3f} | "
            f"{fits} | {fitness} | {count} |"
        )
    lines += [
        "",
        "Masks, seed counts, metrics, timings, CSR bytes and strata are in `results/`.",
        "CSR bytes measure buffers, not peak RAM. Folds/seeds are correlated;",
        "SD is descriptive and no statistical significance or deployment effectiveness is claimed.",
        "",
        "## Development grouping stress test",
        "",
    ]
    sensitivity = read_json(results / "development/sensitivity.json")
    lines.append(
        f"Primary groups: {sensitivity['primary_groups']}; "
        f"stress groups: {sensitivity['stress_groups']}. "
        "Stress-group overlap in primary outer folds: "
        f"{sensitivity['stress_group_overlap_in_primary_outer_folds']}."
    )
    for method, rows in sensitivity["stress_cv"].items():
        scores = [r["metrics"]["f1"] for r in rows]
        lines.append(
            f"- {method}: stress-disjoint F1 {np.mean(scores):.6f} ± {np.std(scores, ddof=1):.6f}."
        )
    lines += [
        "",
        "The heuristic merges strings aggressively and is not a source-separated holdout.",
        "No primary duplicates: representative-group metrics equal row metrics.",
        "Benign CSIC values and sqlmap-generated SQLi remain source-confounded. High scores are",
        "not evidence of generalization to deployed attacks. The rule baseline's misses and every",
        "optimizer's unfavorable comparisons are retained. False positives use aggregate",
        "length/encoding/keyword strata only; no third-party payloads are republished.",
        "",
        "![F1 comparison](../results/plots/f1.png)",
        "",
        "![Full-development search traces](../results/plots/convergence.png)",
    ]
    (root / "docs/RESULTS.md").write_text("\n".join(lines) + "\n")
    definitions = [
        "Character length",
        "Unicode digit count / max(1,length)",
        "Unicode alphabetic count / max(1,length)",
        "Unicode whitespace count / max(1,length)",
        "ASCII string.punctuation count / max(1,length)",
        "Single quote count",
        "Double quote count",
        "Opening plus closing parenthesis count",
        "Semicolon count",
        "Equals count",
        "Nonoverlapping -- count",
        "Nonoverlapping /* plus */ counts",
        "Hash count",
        "Backslash count",
        "%HH hexadecimal occurrences",
        "Whitespace-separated token count",
        "select/union/insert/update/delete/drop/from/where/sleep/benchmark tokens",
        "or/and/not/true/false/null tokens",
        "Unique codepoints / max(1,length)",
        "Non-ASCII count / max(1,length)",
    ]
    write_json(
        results / "feature_schema.json",
        {
            "features": [
                {"index": i, "name": name, "definition": definition}
                for i, (name, definition) in enumerate(zip(NAMES, definitions, strict=True))
            ],
            "semantics": "Verbatim input; no URL decoding; keyword counters ignore case.",
        },
    )


if __name__ == "__main__":
    report()
