#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
from statistics import mean, median, stdev
from collections import Counter  # Przeniesione na górę

import matplotlib.pyplot as plt

def run_radon(project_path: str) -> dict:
    """Run radon cc with JSON output and return parsed results."""
    try:
        result = subprocess.run(
            ["radon", "cc", project_path, "-s", "-j"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("Błąd: Polecenie 'radon' nie zostało znalezione. Zainstaluj je przez 'pip install radon'.")
        sys.exit(1)

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

def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return Top N most complex functions"""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]

def compute_stats(functions: list[dict]) -> dict:
    """Compute summary statistics."""
    if not functions:
        return {}

    complexities = [f["complexity"] for f in functions]
    total_count = len(functions)
    
    avg_cc = mean(complexities)
    med_cc = median(complexities)
    std_cc = stdev(complexities) if total_count > 1 else 0.0

    counts = Counter([f["rank"] for f in functions])
    rank_counts = {r: counts.get(r, 0) for r in "ABCDEF"}

    above_10 = [c for c in complexities if c > 10]
    above_10_count = len(above_10)
    above_10_pct = (above_10_count / total_count) * 100

    return {
        "mean": avg_cc,
        "median": med_cc,
        "stdev": std_cc,
        "rank_counts": rank_counts,
        "above_10_count": above_10_count,
        "above_10_pct": above_10_pct
    }

def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram with rank coloring."""
    if not functions: return
    
    complexities = [f["complexity"] for f in functions]
    max_cc = max(complexities)
    
    plt.figure(figsize=(10, 6))
    n, bins, patches = plt.hist(complexities, bins=range(1, max_cc + 2), 
                                edgecolor='black', align='left', alpha=0.8)

    for patch in patches:
        cc_val = patch.get_x()
        if cc_val <= 5: color = '#2ecc71'
        elif cc_val <= 10: color = '#f1c40f'
        elif cc_val <= 20: color = '#e67e22'
        else: color = '#e74c3c'
        patch.set_facecolor(color)

    plt.title(f"Rozkład Złożoności Cyklomatycznej (N={len(functions)})")
    plt.xlabel("Complexity (CC)")
    plt.ylabel("Liczba funkcji")
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
    rank_desc = {"A": "1-5", "B": "6-10", "C": "11-20", "D": "21-30", "E": "31-40", "F": "41+"}
    total = len(functions)
    
    for r in "ABCDEF":
        count = stats["rank_counts"][r]
        pct = (count / total) * 100
        bar = "█" * int(pct / 2.5)
        print(f"  {r} ({rank_desc[r]:<5}): {count:>5} ({pct:>5.1f}%)  {bar}")

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
