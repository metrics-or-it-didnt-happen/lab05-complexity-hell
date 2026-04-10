#!/usr/bin/env python3
import json
import subprocess
import sys
from statistics import mean, median, stdev

import matplotlib.pyplot as plt


def run_radon(project_path: str) -> dict:
    result = subprocess.run(
        ["radon", "cc", project_path, "-s", "-j"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def extract_functions(radon_data: dict) -> list[dict]:
    functions = []
    for filepath, items in radon_data.items():
        for item in items:
            functions.append({
                "name": item["name"],
                "type": item["type"],
                "complexity": item["complexity"],
                "rank": item["rank"],
                "file": filepath,
                "lineno": item["lineno"],
            })
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
    if not functions:
        return {}

    cc = [f["complexity"] for f in functions]
    total = len(cc)
    cc_gt_10 = sum(1 for c in cc if c > 10)

    ranks = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    for f in functions:
        if f["rank"] in ranks:
            ranks[f["rank"]] += 1

    return {
        "total": total,
        "mean": mean(cc),
        "median": median(cc),
        "stdev": stdev(cc) if total > 1 else 0.0,
        "cc_gt_10_count": cc_gt_10,
        "cc_gt_10_pct": (cc_gt_10 / total) * 100 if total > 0 else 0.0,
        "ranks": ranks,
    }


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]


def plot_histogram(functions: list[dict], output_path: str) -> None:
    if not functions:
        return

    complexities = [f["complexity"] for f in functions]
    max_cc = max(complexities) if complexities else 10
    bins = range(1, max_cc + 2)

    fig, ax = plt.subplots(figsize=(10, 6))
    n, bins_edges, patches = ax.hist(complexities, bins=bins, edgecolor="black", align="left")

    for bin_edge, patch in zip(bins_edges[:-1], patches):
        if bin_edge <= 5:
            patch.set_facecolor("green")
        elif bin_edge <= 10:
            patch.set_facecolor("yellow")
        elif bin_edge <= 20:
            patch.set_facecolor("orange")
        elif bin_edge <= 30:
            patch.set_facecolor("red")
        elif bin_edge <= 40:
            patch.set_facecolor("darkred")
        else:
            patch.set_facecolor("purple")

    ax.axvline(x=5.5, color="green", linestyle="--", alpha=0.7)
    ax.axvline(x=10.5, color="yellow", linestyle="--", alpha=0.7)
    ax.axvline(x=20.5, color="orange", linestyle="--", alpha=0.7)

    ax.set_xlabel("Złożoność cyklomatyczna (CC)")
    ax.set_ylabel("Liczba funkcji")
    ax.set_title("Histogram złożoności cyklomatycznej")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def print_report(functions: list[dict], stats: dict) -> None:
    print(f"\n{'=' * 70}")
    print("PROFIL ZŁOŻONOŚCI CYKLOMATYCZNEJ")
    print(f"{'=' * 70}")

    print("\n--- Statystyki ogólne ---")
    print(f"  Liczba funkcji/metod: {stats['total']}")
    print(f"  Średnia CC:            {stats['mean']:.1f}")
    print(f"  Mediana CC:            {stats['median']:.1f}")
    print(f"  Odch. standardowe:     {stats['stdev']:.1f}")
    print(f"  Funkcje z CC > 10:     {stats['cc_gt_10_count']} ({stats['cc_gt_10_pct']:.1f}%)")

    print("\n--- TOP 20 najbardziej złożonych ---")
    print(f"{'Rank':<5} {'CC':>4} {'Typ':<8} {'Nazwa':<40} {'Plik:linia'}")
    print("-" * 90)
    for f in top_complex(functions):
        loc = f"{f['file']}:{f['lineno']}"
        if len(loc) > 30:
            loc = "..." + loc[-27:]
        print(f"  {f['rank']:<3} {f['complexity']:>4} {f['type']:<8} "
              f"{f['name']:<40} {loc}")

    print("\n--- Rozkład rankingów ---")
    ranges = {
        "A": "1-5", "B": "6-10", "C": "11-20",
        "D": "21-30", "E": "31-40", "F": "41+"
    }
    for rank in ["A", "B", "C", "D", "E", "F"]:
        count = stats["ranks"].get(rank, 0)
        pct = (count / stats["total"]) * 100 if stats["total"] > 0 else 0
        bar_len = int((pct / 100) * 40)
        bar = "█" * bar_len
        print(f"  {rank} ({ranges[rank]:>5}): {count:>5} ({pct:>5.1f}%)  {bar}")


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
    print("\nHistogram zapisany do: complexity_histogram.png")


if __name__ == "__main__":
    main()