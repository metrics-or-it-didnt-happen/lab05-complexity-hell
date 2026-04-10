#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
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
                continue  # pomijamy klasy - ich metody są już na liście
            functions.append({
                "name": item["name"],
                "type": item["type"],  # "function" lub "method"
                "complexity": item["complexity"],
                "rank": item["rank"],
                "file": filepath,
                "lineno": item["lineno"],
            })
    return functions


def compute_stats(functions: list[dict]) -> dict:
    """Compute summary statistics.

    Zwróć dict z kluczami (przykład):
        "mean", "median", "stdev",
        "rank_counts" (dict: {"A": 142, "B": 37, ...}),
        "above_10_count", "above_10_pct"
    Te klucze wykorzystasz potem w print_report().
    """
    if not functions:
        return {}

    complexities = [f["complexity"] for f in functions]

    mean_cc = mean(complexities)
    median_cc = median(complexities)
    stdev_cc = stdev(complexities) if len(complexities) >= 2 else 0.0

    rank_counts = {rank: 0 for rank in ["A", "B", "C", "D", "E", "F"]}
    for f in functions:
        rank = f.get("rank")
        if rank in rank_counts:
            rank_counts[rank] += 1

    above_10_count = sum(1 for cc in complexities if cc > 10)
    above_10_pct = (above_10_count / len(complexities)) * 100.0

    return {
        "mean": mean_cc,
        "median": median_cc,
        "stdev": stdev_cc,
        "rank_counts": rank_counts,
        "above_10_count": above_10_count,
        "above_10_pct": above_10_pct,
    }


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]


def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram."""
    complexities = [f["complexity"] for f in functions]

    plt.figure(figsize=(9, 5))
    plt.hist(complexities, bins=range(1, max(complexities) + 2), edgecolor="black")

    for x, label in [
        (5.5, "A/B"),
        (10.5, "B/C"),
        (20.5, "C/D"),
        (30.5, "D/E"),
        (40.5, "E/F"),
    ]:
        plt.axvline(x=x, color="gray", linestyle="--", linewidth=1, label=label)

    # Color bars by rank threshold for readability.
    for patch in plt.gca().patches:
        cc_val = patch.get_x() + 0.5
        if cc_val < 6:
            patch.set_facecolor("#3CB371")
        elif cc_val < 11:
            patch.set_facecolor("#F0E68C")
        elif cc_val < 21:
            patch.set_facecolor("#FFA500")
        elif cc_val < 31:
            patch.set_facecolor("#FF7F50")
        elif cc_val < 41:
            patch.set_facecolor("#CD5C5C")
        else:
            patch.set_facecolor("#8B0000")

    plt.xlabel("Zlozonosc cyklomatyczna (CC)")
    plt.ylabel("Liczba funkcji/metod")
    plt.title("Histogram zlozonosci cyklomatycznej")
    plt.tight_layout()
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
    print(
        f"  Funkcje z CC > 10:     {stats['above_10_count']} "
        f"({stats['above_10_pct']:.1f}%)"
    )

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
    rank_ranges = {
        "A": "(1-5)",
        "B": "(6-10)",
        "C": "(11-20)",
        "D": "(21-30)",
        "E": "(31-40)",
        "F": "(41+)",
    }
    total = len(functions)
    for rank in ["A", "B", "C", "D", "E", "F"]:
        count = stats["rank_counts"].get(rank, 0)
        pct = (count / total) * 100.0 if total else 0.0
        bar = "#" * int(pct)
        print(
            f"  {rank} {rank_ranges[rank]:<6} {count:>5} ({pct:>4.1f}%)  {bar}"
        )

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
