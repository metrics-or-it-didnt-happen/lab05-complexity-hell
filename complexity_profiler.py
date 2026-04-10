#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
from statistics import mean, median, stdev

import matplotlib.pyplot as plt


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

    Returns list of dicts with keys:
        name, type, complexity, rank, file, lineno

    Uwaga: radon w JSON-ie listuje metody podwójnie - raz jako
    top-level items, raz zagnieżdżone w klasach. Bierzemy tylko
    top-level items i pomijamy klasy (ich CC to suma CC metod,
    a metody są już wylistowane osobno).
    """
    functions = []
    for filepath, items in radon_data.items():
        for item in items:
            if item["type"] == "class":
                continue
            functions.append({
                "name": item["name"],
                "type": item["type"],
                "complexity": item["complexity"],
                "rank": item["rank"],
                "file": filepath,
                "lineno": item["lineno"],
            })
    return functions


def compute_stats(functions: list[dict]) -> dict:
    """Compute summary statistics."""
    if not functions:
        return {}

    complexities = [f["complexity"] for f in functions]

    cc_mean = mean(complexities)
    cc_median = median(complexities)
    cc_stdev = stdev(complexities) if len(complexities) >= 2 else 0.0

    rank_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    for f in functions:
        rank_counts[f["rank"]] += 1

    above_10 = sum(1 for c in complexities if c > 10)

    return {
        "mean": cc_mean,
        "median": cc_median,
        "stdev": cc_stdev,
        "rank_counts": rank_counts,
        "above_10_count": above_10,
        "above_10_pct": above_10 / len(functions) * 100,
    }


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]


def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram."""
    complexities = [f["complexity"] for f in functions]

    plt.figure(figsize=(12, 6))
    n, bins, patches = plt.hist(
        complexities,
        bins=range(1, max(complexities) + 2),
        edgecolor="black",
        linewidth=0.5,
    )

    for patch in plt.gca().patches:
        cc_val = patch.get_x()
        if cc_val < 6:
            patch.set_facecolor("#4CAF50")
        elif cc_val < 11:
            patch.set_facecolor("#FFC107")
        elif cc_val < 21:
            patch.set_facecolor("#FF9800")
        elif cc_val < 31:
            patch.set_facecolor("#F44336")
        elif cc_val < 41:
            patch.set_facecolor("#9C27B0")
        else:
            patch.set_facecolor("#212121")

    plt.axvline(x=5.5, color="green", linestyle="--", alpha=0.7, label="A/B (5)")
    plt.axvline(x=10.5, color="orange", linestyle="--", alpha=0.7, label="B/C (10)")
    plt.axvline(x=20.5, color="red", linestyle="--", alpha=0.7, label="C/D (20)")
    plt.axvline(x=30.5, color="purple", linestyle="--", alpha=0.7, label="D/E (30)")
    plt.axvline(x=40.5, color="black", linestyle="--", alpha=0.7, label="E/F (40)")

    plt.xlabel("Złożoność cyklomatyczna (CC)")
    plt.ylabel("Liczba funkcji")
    plt.title("Rozkład złożoności cyklomatycznej")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def print_report(functions: list[dict], stats: dict) -> None:
    """Print formatted complexity report."""
    print(f"\n{'=' * 70}")
    print("PROFIL ZŁOŻONOŚCI CYKLOMATYCZNEJ")
    print(f"{'=' * 70}")

    print("\n--- Statystyki ogólne ---")
    print(f"  Liczba funkcji/metod: {len(functions)}")
    print(f"  Średnia CC:            {stats['mean']:.1f}")
    print(f"  Mediana CC:            {stats['median']:.1f}")
    print(f"  Odch. standardowe:     {stats['stdev']:.1f}")
    print(f"  Funkcje z CC > 10:     {stats['above_10_count']} "
          f"({stats['above_10_pct']:.1f}%)")

    print(f"\n--- TOP 20 najbardziej złożonych ---")
    print(f"{'Rank':<5} {'CC':>4} {'Typ':<8} {'Nazwa':<40} {'Plik:linia'}")
    print("-" * 90)
    for f in top_complex(functions):
        loc = f"{f['file']}:{f['lineno']}"
        if len(loc) > 30:
            loc = "..." + loc[-27:]
        print(f"  {f['rank']:<3} {f['complexity']:>4} {f['type']:<8} "
              f"{f['name']:<40} {loc}")

    print("\n--- Rozkład rankingów ---")
    total = len(functions)
    labels = {
        "A": "A (1-5)  ",
        "B": "B (6-10) ",
        "C": "C (11-20)",
        "D": "D (21-30)",
        "E": "E (31-40)",
        "F": "F (41+)  ",
    }
    for rank in ["A", "B", "C", "D", "E", "F"]:
        count = stats["rank_counts"][rank]
        pct = count / total * 100 if total > 0 else 0
        bar = "\u2588" * int(pct)
        print(f"  {labels[rank]}: {count:>5} ({pct:>5.1f}%)  {bar}")


def main():
    if len(sys.argv) < 2:
        print("Użycie: python complexity_profiler.py <ścieżka_do_projektu>")
        sys.exit(1)

    project_path = sys.argv[1]
    print(f"Analizuję złożoność: {project_path}")

    radon_data = run_radon(project_path)
    functions = extract_functions(radon_data)

    if not functions:
        print("Nie znaleziono funkcji do analizy.")
        sys.exit(1)

    stats = compute_stats(functions)
    print_report(functions, stats)
    plot_histogram(functions, "complexity_histogram.png")
    print(f"\nHistogram zapisany do: complexity_histogram.png")


if __name__ == "__main__":
    main()
