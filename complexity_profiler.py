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
    """Extract all functions/methods from radon JSON output."""
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

    mean_val = mean(complexities)
    median_val = median(complexities)
    stdev_val = stdev(complexities) if len(complexities) >= 2 else 0.0

    rank_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    for f in functions:
        if f["rank"] in rank_counts:
            rank_counts[f["rank"]] += 1

    above_10_count = sum(1 for c in complexities if c > 10)
    above_10_pct = (above_10_count / len(complexities)) * 100 if complexities else 0.0

    return {
        "mean": mean_val,
        "median": median_val,
        "stdev": stdev_val,
        "rank_counts": rank_counts,
        "above_10_count": above_10_count,
        "above_10_pct": above_10_pct
    }


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]


def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram."""
    complexities = [f["complexity"] for f in functions]
    if not complexities:
        return

    max_cc = max(complexities)
    plt.figure(figsize=(10, 6))

    # Histogram
    bins = range(1, max_cc + 2)
    n, bins_edges, patches = plt.hist(complexities, bins=bins, edgecolor='black', alpha=0.7)

    # Kolorowanie słupków zależnie od progu (Ranking)
    for patch in patches:
        cc_val = patch.get_x()
        if cc_val <= 5:
            patch.set_facecolor('green')  # A
        elif cc_val <= 10:
            patch.set_facecolor('yellowgreen')  # B
        elif cc_val <= 20:
            patch.set_facecolor('gold')  # C
        elif cc_val <= 30:
            patch.set_facecolor('orange')  # D
        elif cc_val <= 40:
            patch.set_facecolor('red')  # E
        else:
            patch.set_facecolor('darkred')  # F

    # Linie pionowe oznaczające progi
    plt.axvline(x=5.5, color='green', linestyle='--', label='A/B (5)')
    plt.axvline(x=10.5, color='olive', linestyle='--', label='B/C (10)')
    plt.axvline(x=20.5, color='orange', linestyle='--', label='C/D (20)')
    plt.axvline(x=30.5, color='red', linestyle='--', label='D/E (30)')
    plt.axvline(x=40.5, color='darkred', linestyle='--', label='E/F (40)')

    plt.xlabel('Złożoność cyklomatyczna (CC)')
    plt.ylabel('Liczba funkcji/metod')
    plt.title('Histogram Złożoności Cyklomatycznej')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)

    plt.savefig(output_path, dpi=150)
    plt.close()


def print_report(functions: list[dict], stats: dict) -> None:
    """Print formatted complexity report."""
    print(f"\n{'=' * 70}")
    print(f"PROFIL ZŁOŻONOŚCI CYKLOMATYCZNEJ")
    print(f"{'=' * 70}")

    print(f"\n--- Statystyki ogólne ---")
    print(f"  Liczba funkcji/metod: {len(functions)}")
    print(f"  Średnia CC:            {stats['mean']:.1f}")
    print(f"  Mediana CC:            {stats['median']:.1f}")
    print(f"  Odch. standardowe:     {stats['stdev']:.1f}")
    print(f"  Funkcje z CC > 10:     {stats['above_10_count']} ({stats['above_10_pct']:.1f}%)")

    print(f"\n--- TOP 20 najbardziej złożonych ---")
    print(f"{'Rank':<5} {'CC':>4} {'Typ':<8} {'Nazwa':<40} {'Plik:linia'}")
    print("-" * 90)
    for f in top_complex(functions):
        loc = f"{f['file']}:{f['lineno']}"
        if len(loc) > 30:
            loc = "..." + loc[-27:]
        print(f"  {f['rank']:<3} {f['complexity']:>4} {f['type']:<8} "
              f"{f['name']:<40} {loc}")

    print(f"\n--- Rozkład rankingów ---")
    total = len(functions)
    rank_labels = {
        "A": "A (1-5):  ",
        "B": "B (6-10): ",
        "C": "C (11-20):",
        "D": "D (21-30):",
        "E": "E (31-40):",
        "F": "F (41+):  "
    }
    for rank in ["A", "B", "C", "D", "E", "F"]:
        count = stats["rank_counts"][rank]
        pct = (count / total) * 100 if total > 0 else 0
        bar = chr(9608) * int(pct)  # Użycie pełnego bloku do paska postępu
        print(f"  {rank_labels[rank]} {count:>4} ({pct:>4.1f}%)  {bar}")


def main():
    if len(sys.argv) < 2:
        print("Użycie: python complexity_profiler.py <ścieżka_do_projektu>")
        sys.exit(1)

    project_path = sys.argv[1]
    print(f"Analizuję złożoność: {project_path}")

    try:
        radon_data = run_radon(project_path)
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas uruchamiania radona: {e}")
        sys.exit(1)

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