#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
from statistics import mean, median, stdev
from typing import Counter

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
            functions.append(
                {
                    "name": item["name"],
                    "type": item["type"],  # "function" lub "method"
                    "complexity": item["complexity"],
                    "rank": item["rank"],
                    "file": filepath,
                    "lineno": item["lineno"],
                }
            )
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
    ranks = [f["rank"] for f in functions]

    c_rank = Counter(ranks)
    above_10_count = len([cc for cc in complexities if cc > 10])
    above_10_pct = (above_10_count / len(complexities)) * 100
    # TODO: Twój kod tutaj
    # 1. Policz mean(complexities), median(complexities)
    # 2. Policz stdev(complexities) - uwaga: wymaga >= 2 elementów!
    # 3. Policz rozkład rankingów: ile funkcji ma rank A, B, C, D, E, F
    #    (rank każdej funkcji masz w f["rank"])
    # 4. Policz ile funkcji ma CC > 10 i jaki to procent
    # 5. Zwróć to wszystko jako dict
    stdev_check = stdev(complexities) if len(complexities) >= 2 else 0.0
    return {
        "mean": mean(complexities),
        "median": median(complexities),
        "stdev": stdev_check(complexities),
        "rank_counts": dict(c_rank),
        "above_10_count": above_10_count,
        "above_10_pct": above_10_pct,
    }


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]


def plot_histogram(functions: list[dict], output_path: str) -> None:
    if not functions:
        print("Brak danych do wygenerowania wykresu.")
        return

    complexities = [f["complexity"] for f in functions]
    max_cc = max(complexities)

    plt.figure(figsize=(12, 6))

    n, bins, patches = plt.hist(
        complexities, bins=range(1, max_cc + 2), edgecolor="black", alpha=0.8
    )

    girl_palette = {
        "A": "#FFB6C1",  # LightPink (A)
        "B": "#FFDAB9",  # PeachPuff (B)
        "C": "#F08080",  # LightCoral (C)
        "D": "#FF69B4",  # HotPink (D)
        "E": "#DDA0DD",  # Plum (E)
        "F": "#9370DB",  # MediumPurple (F)
    }

    for patch in patches:
        cc_val = patch.get_x()
        if cc_val < 6:
            color = girl_palette["A"]
        elif cc_val < 11:
            color = girl_palette["B"]
        elif cc_val < 21:
            color = girl_palette["C"]
        elif cc_val < 31:
            color = girl_palette["D"]
        elif cc_val < 41:
            color = girl_palette["E"]
        else:
            color = girl_palette["F"]
        patch.set_facecolor(color)

    thresholds = [5.5, 10.5, 20.5, 30.5, 40.5]
    for t in thresholds:
        if t < max_cc:
            plt.axvline(
                x=t,
                color="#FF1493",
                linestyle="--",
                linewidth=1.5,
                alpha=0.6,
                label="Próg rankingu" if t == 5.5 else "",
            )

    plt.title(
        "Rozkład złożoności cyklomatycznej (Cyclomatic Complexity)",
        fontsize=14,
        color="#4B0082",
    )
    plt.xlabel("Complexity Value (CC)", fontsize=12, color="#4B0082")
    plt.ylabel("Liczba funkcji", fontsize=12, color="#4B0082")

    plt.grid(axis="y", alpha=0.3, color="#FFC0CB")

    plt.xticks(range(0, max_cc + 2, 5 if max_cc > 50 else 1), color="#4B0082")
    plt.yticks(color="#4B0082")

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
    print(f"  {'Średnia CC:':<21} {stats['mean']:.1f}")
    print(f"  {'Mediana CC:':<21} {stats['median']:.1f}")
    print(f"  {'Odch. standardowe:':<21} {stats['stdev']:.1f}")
    print(
        f"  {'Funkcje z CC > 10:':<21} {stats['above_10_count']} ({stats['above_10_pct']:.1f}%)"
    )

    print(f"\n--- TOP 20 najbardziej złożonych ---")
    print(f"{'Rank':<5} {'CC':>4} {'Typ':<8} {'Nazwa':<40} {'Plik:linia'}")
    print("-" * 90)
    for f in top_complex(functions):
        loc = f"{f['file']}:{f['lineno']}"
        if len(loc) > 30:
            loc = "..." + loc[-27:]
        print(
            f"  {f['rank']:<3} {f['complexity']:>4} {f['type']:<8} "
            f"{f['name']:<40} {loc}"
        )

    print(f"\n--- Rozkład rankingów ---")
    d = {
        "A": "A (1-5):",
        "B": "B (6-10):",
        "C": "C (11-20):",
        "D": "D (21-30):",
        "E": "E (31-40):",
        "F": "F (41+):",
    }

    max_len = max(len(v) for v in d.values())

    for key, val in d.items():
        count = stats["rank_counts"].get(key, 0)
        pct = (count * 100) / len(functions) if len(functions) > 0 else 0
        pasek = chr(9608) * int(pct / 2)

        print(f"   {val:<{max_len}} {count:>6} ({pct:>5.1f}%) {pasek}")


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
    print(f"\nHistogram w girl palette zapisany do: complexity_histogram.png")


if __name__ == "__main__":
    main()
