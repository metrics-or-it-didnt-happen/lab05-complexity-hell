#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
from statistics import mean, median, stdev
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  
plt.rcParams["font.family"] = "Times New Roman"

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
    """
    functions = []
    for filepath, items in radon_data.items():
        for item in items:
            if item["type"]=="class":
                continue
            functions.append({
                "name": item["name"],
                "type": item["type"],  # "function", "method", "class"
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

    mean_cc = mean(complexities)
    median_cc = median(complexities)
    stdev_cc = stdev(complexities) if len(complexities)>1 else 0

    high_cc = [c for c in complexities if c>10]
    percent_high_cc = (len(high_cc)/len(complexities))*100

    rank_counts = defaultdict(int)
    for f in functions:
        rank_counts[f["rank"]] += 1

    stats_dict = {
        "mean": mean_cc,
        "median": median_cc,
        "stdev": stdev_cc,
        "rank_counts": dict(rank_counts),
        "high_cc_count": len(high_cc),
        "percent_high_cc": percent_high_cc
    }

    return stats_dict

def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]

def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram."""
    complexities = [f["complexity"] for f in functions]
    max_cc = max(complexities)
    max_x = max(max_cc, 25)
    bins = list(range(0, max_x+2))

    # Kolorowanie: zielony (A), żółty (B), pomarańczowy (C),
    #              czerwony (D), ciemnoczerwony (F)
    ranges = [
        (0, 5, "green"),          # A
        (5, 10, "yellow"),        # B
        (10, 20, "orange"),       # C
        (20, 50, "red"),          # D
        (50, max_x, "darkred"),   # F
    ]

    plt.figure()
    for low, high, color in ranges:
        subset = [c-1 for c in complexities if low<c<=high or (low==0 and c<=high)]
        if subset:
            plt.hist(subset, bins=bins, color=color)

    # Dodaj linie pionowe oznaczające progi (5, 10, 20)
    for threshold in [5, 10, 20, 30, 50]:
        plt.axvline(threshold)

    plt.xlim(0, max_x)
    plt.xlabel("Cyclomatic Complexity")
    plt.ylabel("Number of functions")
    plt.title("Cyclomatic Complexity Distribution")

    plt.savefig(output_path)
    plt.close()

def print_rank_distribution(rank_counts: dict, total: int) -> None:
    """Print distribution of ranks A/B/C/D/F."""

    rank_labels = {
        "A": "A (1-5)",
        "B": "B (6-10)",
        "C": "C (11-20)",
        "D": "D (21-50)",
        "E": "E (51-100)",
        "F": "F (>100)"
    }

    for rank in ["A", "B", "C", "D", "E", "F"]:
        count = rank_counts.get(rank, 0)
        percent = (count/total)* 100 if total>0 else 0

        bar = "█"*int(percent/2)           # 1 znak -> 2%
        print(f"  {rank_labels[rank]:<10}: {count:>5} ({percent:>4.1f}%)  {bar}")

def print_report(functions: list[dict], stats: dict) -> None:
    """Print formatted complexity report."""
    print(f"\n{'=' * 70}")
    print(f"PROFIL ZŁOŻONOŚCI CYKLOMATYCZNEJ")
    print(f"{'=' * 70}")

    print(f"\n--- Statystyki ogólne ---")
    print(f"  Liczba funkcji/metod: {len(functions)}")
    print(f"  Średnia CC:           {stats['mean']:.1f}")
    print(f"  Mediana CC:           {stats['median']:.1f}")
    print(f"  Odch. standardowe:    {stats['stdev']:.1f}")
    print(f"  Funkcje z CC > 10:    {stats['high_cc_count']} ({stats['percent_high_cc']:.1f}%)")

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
    print_rank_distribution(stats["rank_counts"], len(functions))

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