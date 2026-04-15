#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median, stdev

import altair as alt

RANK_ORDER = ["A", "B", "C", "D", "E", "F"]
RANK_LABELS = {
    "A": "A (1-5)",
    "B": "B (6-10)",
    "C": "C (11-20)",
    "D": "D (21-30)",
    "E": "E (31-40)",
    "F": "F (41+)",
}
RANK_THRESHOLDS = [5.5, 10.5, 20.5, 30.5, 40.5]


def run_radon(project_path: str) -> dict:
    """Run radon cc with JSON output and return parsed results."""
    result = subprocess.run(
        ["radon", "cc", project_path, "-s", "-j"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def extract_functions(radon_data: dict) -> list[dict]:
    """Extract all functions/methods from radon JSON output.

    Radon lists methods twice in the JSON: once as top-level items in
    the file, and once nested inside their class. We iterate top-level
    items and skip classes - their methods are already listed separately,
    and a class's CC is just the sum of its methods' CC.
    """
    functions: list[dict] = []
    for filepath, items in radon_data.items():
        for item in items:
            if item["type"] == "class":
                continue
            functions.append({
                "name": item["name"],
                "type": item["type"],  # "function" or "method"
                "complexity": item["complexity"],
                "rank": item["rank"],
                "file": filepath,
                "lineno": item["lineno"],
                "classname": item.get("classname"),
            })
    return functions


def compute_stats(functions: list[dict]) -> dict:
    """Compute summary statistics for the given functions."""
    if not functions:
        return {}

    complexities = [f["complexity"] for f in functions]
    rank_counts = Counter(f["rank"] for f in functions)
    above_10 = sum(1 for c in complexities if c > 10)

    return {
        "count": len(functions),
        "mean": mean(complexities),
        "median": median(complexities),
        "stdev": stdev(complexities) if len(complexities) >= 2 else 0.0,
        "rank_counts": {r: rank_counts.get(r, 0) for r in RANK_ORDER},
        "above_10_count": above_10,
        "above_10_pct": 100.0 * above_10 / len(complexities),
        "max": max(complexities),
    }


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions, sorted by CC descending."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]


def _rank_for(cc: int) -> str:
    if cc <= 5:
        return "A"
    if cc <= 10:
        return "B"
    if cc <= 20:
        return "C"
    if cc <= 30:
        return "D"
    if cc <= 40:
        return "E"
    return "F"


def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram as PNG using altair."""
    complexities = [f["complexity"] for f in functions]
    max_cc = max(complexities)

    # One bar per integer CC value, coloured by rank
    bin_counts: dict[int, int] = {}
    for c in complexities:
        bin_counts[c] = bin_counts.get(c, 0) + 1

    bars = [{"cc": c, "count": n, "rank": _rank_for(c)} for c, n in bin_counts.items()]
    thresholds = [{"x": t, "label": f"rank {RANK_ORDER[i]}/{RANK_ORDER[i + 1]}"}
                  for i, t in enumerate(RANK_THRESHOLDS) if t < max_cc + 1]

    bar_chart = (
        alt.Chart(alt.Data(values=bars))
        .mark_bar()
        .encode(
            x=alt.X("cc:Q", title="Cyclomatic complexity",
                    scale=alt.Scale(domain=[0, max_cc + 1]),
                    axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("count:Q", title="Number of functions"),
            color=alt.Color(
                "rank:N",
                scale=alt.Scale(
                    domain=RANK_ORDER,
                    range=["#2ca02c", "#bcbd22", "#ff7f0e", "#d62728", "#8c2d2d", "#4a0000"],
                ),
                legend=alt.Legend(title="Rank"),
            ),
            tooltip=["cc:Q", "count:Q", "rank:N"],
        )
    )

    rule_chart = (
        alt.Chart(alt.Data(values=thresholds))
        .mark_rule(strokeDash=[4, 4], color="gray")
        .encode(x="x:Q", tooltip="label:N")
    )

    chart = (
        (bar_chart + rule_chart)
        .properties(
            title=f"Cyclomatic complexity distribution ({len(functions)} functions)",
            width=700,
            height=380,
        )
    )
    chart.save(output_path, scale_factor=2)


def print_report(functions: list[dict], stats: dict) -> None:
    """Print formatted complexity report."""
    print(f"\n{'=' * 70}")
    print("CYCLOMATIC COMPLEXITY PROFILE")
    print(f"{'=' * 70}")

    print("\n--- Overall statistics ---")
    print(f"  Functions/methods:   {stats['count']}")
    print(f"  Mean CC:             {stats['mean']:.2f}")
    print(f"  Median CC:           {stats['median']:.1f}")
    print(f"  Stdev CC:            {stats['stdev']:.2f}")
    print(f"  Max CC:              {stats['max']}")
    print(f"  Functions CC > 10:   {stats['above_10_count']} "
          f"({stats['above_10_pct']:.1f}%)")

    print("\n--- Top 20 most complex ---")
    print(f"{'Rank':<5} {'CC':>4} {'Type':<8} {'Name':<45} {'File:line'}")
    print("-" * 95)
    for f in top_complex(functions):
        loc = f"{f['file']}:{f['lineno']}"
        if len(loc) > 32:
            loc = "..." + loc[-29:]
        display_name = f["name"]
        if f["classname"]:
            display_name = f"{f['classname']}.{display_name}"
        if len(display_name) > 43:
            display_name = display_name[:40] + "..."
        print(f"  {f['rank']:<3} {f['complexity']:>4} {f['type']:<8} "
              f"{display_name:<45} {loc}")

    print("\n--- Rank distribution ---")
    total = stats["count"]
    for rank in RANK_ORDER:
        n = stats["rank_counts"][rank]
        pct = 100.0 * n / total if total else 0.0
        bar = "#" * max(1, int(pct / 2)) if n else ""
        print(f"  {RANK_LABELS[rank]:<12} {n:>4} ({pct:>5.1f}%)  {bar}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python complexity_profiler.py <project_path> [histogram_path]")
        sys.exit(1)

    project_path = sys.argv[1]
    histogram_path = sys.argv[2] if len(sys.argv) > 2 else "complexity_histogram.png"

    if not Path(project_path).exists():
        print(f"Path does not exist: {project_path}")
        sys.exit(1)

    print(f"Analysing complexity: {project_path}")

    radon_data = run_radon(project_path)
    functions = extract_functions(radon_data)

    if not functions:
        print("No functions found. Is this a Python project?")
        sys.exit(1)

    stats = compute_stats(functions)
    print_report(functions, stats)
    plot_histogram(functions, histogram_path)
    print(f"\nHistogram saved to: {histogram_path}")


if __name__ == "__main__":
    main()
