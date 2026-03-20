#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import re
import subprocess
import sys
from pathlib import Path
from statistics import mean, median, stdev

import matplotlib.pyplot as plt

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


def run_radon(project_path: str) -> dict:
    """Run radon cc with JSON output and return parsed results."""
    result = subprocess.run(
        ["radon", "cc", project_path, "-s", "-j"],
        capture_output=True,
        text=True,
        check=True,
    )
    clean_output = ANSI_ESCAPE.sub('', result.stdout)
    return json.loads(clean_output)


def extract_functions(radon_data: dict) -> list[dict]:
    """Extract all functions/methods from radon JSON output.

    Returns list of dicts with keys:
        name, type, complexity, rank, file, lineno
    """
    functions = []
    for filepath, items in radon_data.items():
        for item in items:
            functions.append({
                "name": item["name"],
                "type": item["type"],  # "function", "method", "class"
                "complexity": item["complexity"],
                "rank": item["rank"],
                "file": filepath,
                "lineno": item["lineno"],
            })
            # Klasy mogą mieć zagnieżdżone metody
            for method in item.get("methods", []):
                functions.append({
                    "name": f"{item['name']}.{method['name']}",
                    "type": "method",
                    "complexity": method["complexity"],
                    "rank": method["rank"],
                    "file": filepath,
                    "lineno": method["lineno"],
                })
    return functions


def compute_stats(functions: list[dict]) -> dict:
    """Compute summary statistics."""
    if not functions:
        return {}

    complexities = [f["complexity"] for f in functions]

    rank_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    for f in functions:
        rank = f["rank"]
        if rank in rank_distribution:
            rank_distribution[rank] += 1

    high_complexity_count = sum(1 for c in complexities if c > 10)
    high_complexity_pct = (high_complexity_count / len(complexities)) * 100

    return {
        "mean": mean(complexities),
        "median": median(complexities),
        "stdev": stdev(complexities) if len(complexities) > 1 else 0.0,
        "min": min(complexities),
        "max": max(complexities),
        "total": len(complexities),
        "rank_distribution": rank_distribution,
        "high_complexity_count": high_complexity_count,
        "high_complexity_pct": high_complexity_pct,
    }


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]



def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram."""
    complexities = [f["complexity"] for f in functions]

    max_cc = max(complexities) if complexities else 30
    bins = range(1, max_cc + 2)

    plt.figure(figsize=(12, 6))
    plt.hist(complexities, bins=list(bins), edgecolor="black", linewidth=0.5)
    plt.xlabel("Złożoność cyklomatyczna (CC)")
    plt.ylabel("Liczba funkcji / metod")
    plt.title("Rozkład złożoności cyklomatycznej")
    plt.axvline(x=5.5,  color="gray", linestyle="--", linewidth=0.8, label="A/B (5)")
    plt.axvline(x=10.5, color="gray", linestyle="--", linewidth=0.8, label="B/C (10)")
    plt.axvline(x=20.5, color="gray", linestyle="--", linewidth=0.8, label="D/E (20)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def print_report(functions: list[dict], stats: dict) -> None:
    """Print formatted complexity report."""
    print(f"\n{'=' * 70}")
    print(f"PROFIL ZŁOŻONOŚCI CYKLOMATYCZNEJ")
    print(f"{'=' * 70}")

    print(f"\n--- Statystyki ogólne ---")
    print(f"  Liczba funkcji/metod : {stats['total']}")
    print(f"  Średnia CC           : {stats['mean']:.2f}")
    print(f"  Mediana CC           : {stats['median']:.1f}")
    print(f"  Odchylenie std       : {stats['stdev']:.2f}")
    print(f"  Min / Max            : {stats['min']} / {stats['max']}")
    print(f"  CC > 10 (wysokie)    : {stats['high_complexity_count']} "
          f"({stats['high_complexity_pct']:.1f}%)")

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
    dist = stats["rank_distribution"]
    total = stats["total"]
    rank_descriptions = {
        "A": "1–5   (prosta)",
        "B": "6–10  (umiarkowana)",
        "C": "11–15 (złożona)",
        "D": "16–20 (bardzo złożona)",
        "E": "21–25 (krytyczna)",
        "F": "26+   (nieakceptowalna)",
    }
    for rank, desc in rank_descriptions.items():
        count = dist.get(rank, 0)
        pct = (count / total * 100) if total else 0
        bar = "█" * int(pct / 2)
        print(f"  {rank}  CC {desc:<26}  {count:>5}  ({pct:5.1f}%)  {bar}")

    print()


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