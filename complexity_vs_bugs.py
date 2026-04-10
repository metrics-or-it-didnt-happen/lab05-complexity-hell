#!/usr/bin/env python3

import json
import math
import os
import subprocess
from collections import Counter

import matplotlib.pyplot as plt


def run_radon_json(source_path: str) -> dict:
    """Run radon cc and return parsed JSON output."""
    result = subprocess.run(
        ["radon", "cc", source_path, "-s", "-j"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def average_cc_by_basename(radon_data: dict) -> dict[str, float]:
    """Compute average CC per filename basename from radon data."""
    cc_values_by_file = {}

    for file_path, items in radon_data.items():
        base = os.path.basename(file_path)
        cc_values_by_file.setdefault(base, [])

        for item in items:
            # Skip class synthetic entries; methods/functions are enough.
            if item.get("type") == "class":
                continue
            cc_values_by_file[base].append(item["complexity"])

    avg_cc = {}
    for base, values in cc_values_by_file.items():
        if values:
            avg_cc[base] = sum(values) / len(values)

    return avg_cc

def count_bugfix_commits(repo_path: str) -> dict[str, int]:
    """Count bugfix commits per file using git log."""
    result = subprocess.run(
        ["git", "log", "--format=%s", "--name-only",
         "--grep=fix", "--grep=bug", "--grep=error"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    # Parsowanie: commit message, potem lista plików, potem pusta linia
    file_counts = Counter()
    lines = result.stdout.strip().split("\n")
    for line in lines:
        if line.endswith(".py"):
            file_counts[os.path.basename(line)] += 1

    return dict(file_counts)


def pearson_corr(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation without external dependencies."""
    if len(x) != len(y) or len(x) < 2:
        return float("nan")

    mx = sum(x) / len(x)
    my = sum(y) / len(y)
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y))

    if sx == 0 or sy == 0:
        return float("nan")
    return cov / (sx * sy)


def plot_complexity_vs_bugs(
    avg_cc: dict[str, float],
    bugfix_counts: dict[str, int],
    output_path: str,
) -> tuple[list[float], list[float]]:
    """Create scatter plot: X=avg CC per file, Y=bugfix commit count."""
    files = sorted(avg_cc.keys())
    x_vals = [avg_cc[f] for f in files]
    y_vals = [bugfix_counts.get(f, 0) for f in files]

    plt.figure(figsize=(10, 6))
    plt.scatter(x_vals, y_vals, alpha=0.75, edgecolors="black", linewidths=0.3)
    plt.xlabel("Srednia CC pliku")
    plt.ylabel("Liczba bugfix commitow")
    plt.title("Complexity vs Bugs")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return x_vals, y_vals


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Uzycie: python complexity_vs_bugs.py <repo_path> [source_path]")
        sys.exit(1)

    repo_path = sys.argv[1]
    source_path = sys.argv[2] if len(sys.argv) > 2 else repo_path

    print(f"Analizuje repozytorium: {repo_path}")
    print(f"Sciezka kodu dla radon: {source_path}")

    radon_data = run_radon_json(source_path)
    avg_cc = average_cc_by_basename(radon_data)
    bugfix_counts = count_bugfix_commits(repo_path)

    x_vals, y_vals = plot_complexity_vs_bugs(
        avg_cc,
        bugfix_counts,
        "complexity_vs_bugs.png",
    )

    corr = pearson_corr(x_vals, y_vals)

    print(f"\nLiczba plikow analizowanych (CC): {len(avg_cc)}")
    print(f"Liczba plikow z bugfix commitami: {len(bugfix_counts)}")
    if math.isnan(corr):
        print("Pearson r: n/a (za malo danych lub zerowa wariancja)")
    else:
        print(f"Pearson r: {corr:.3f}")
    print("Wykres zapisany do: complexity_vs_bugs.png")


if __name__ == "__main__":
    main()