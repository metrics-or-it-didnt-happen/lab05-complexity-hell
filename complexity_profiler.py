#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
#
from collections import Counter, defaultdict
from statistics import mean, median, stdev

import matplotlib.pyplot as plt
#
from scipy.stats import pearsonr, spearmanr


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

# ==

def compute_file_avg_cc(functions: list[dict]) -> dict[str, float]:
    """Compute average CC per file based on extracted functions."""
    per_file: dict[str, list[int]] = defaultdict(list)
    for f in functions:
        per_file[f["file"]].append(f["complexity"])

    return {path: mean(values) for path, values in per_file.items()}


def count_bugfix_commits(repo_path: str) -> dict[str, int]:
    """Count bugfix commits per file using git log."""
    result = subprocess.run(
        [
            "git",
            "log",
            "--format=%s",
            "--name-only",
            "--grep=fix",
            "--grep=bug",
            "--grep=error",
        ],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )

    file_counts = Counter()
    lines = result.stdout.strip().split("\n") if result.stdout else []
    for line in lines:
        if line.endswith(".py"):
            file_counts[line] += 1

    return dict(file_counts)


def normalize_basename_map(file_map: dict[str, float]) -> dict[str, list[tuple[str, float]]]:
    """Map basenames to original paths and values for fuzzy path matching."""
    normalized: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for path, value in file_map.items():
        basename = path.split("/")[-1]
        normalized[basename].append((path, value))
    return normalized


def build_cc_bugfix_pairs(
    file_avg_cc: dict[str, float],
    bugfix_counts: dict[str, int],
) -> tuple[list[float], list[int]]:
    """Match CC and bugfix counts by basename and return aligned arrays."""
    cc_by_base = normalize_basename_map(file_avg_cc)
    bugfix_by_base = normalize_basename_map(bugfix_counts)

    x_vals: list[float] = []
    y_vals: list[int] = []
    for basename, cc_entries in cc_by_base.items():
        bug_entries = bugfix_by_base.get(basename)
        if not bug_entries:
            continue
        # If multiple files share a basename, take the mean CC and sum bugfixes.
        cc_mean = mean(value for _, value in cc_entries)
        bug_sum = sum(int(value) for _, value in bug_entries)
        x_vals.append(cc_mean)
        y_vals.append(bug_sum)

    return x_vals, y_vals


def plot_bugfix_correlation(x_vals: list[float], y_vals: list[int], output_path: str) -> None:
    """Plot CC vs bugfix commit counts scatter plot."""
    plt.figure(figsize=(7, 5))
    plt.scatter(x_vals, y_vals, alpha=0.7, edgecolors="black")
    plt.xlabel("Srednia zlozonosc cyklomatyczna (CC)")
    plt.ylabel("Liczba commitow bugfix")
    plt.title("Zaleznosc: zlozonosc a liczba bugfixow")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def print_correlation(x_vals: list[float], y_vals: list[int]) -> None:
    """Print correlation metrics if enough data points exist."""
    if len(x_vals) < 2 or len(y_vals) < 2:
        print("\nZa malo danych do policzenia korelacji (min. 2 punkty).")
        return

    pearson_r, pearson_p = pearsonr(x_vals, y_vals)
    spearman_r, spearman_p = spearmanr(x_vals, y_vals)
    print("\n--- Korelacja zlozonosc vs bugfix ---")
    print(f"  Pearson r:  {pearson_r:.3f} (p={pearson_p:.3g})")
    print(f"  Spearman ρ: {spearman_r:.3f} (p={spearman_p:.3g})")

# ==

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

# ==
    file_avg_cc = compute_file_avg_cc(functions)
    bugfix_counts = count_bugfix_commits(project_path)
    x_vals, y_vals = build_cc_bugfix_pairs(file_avg_cc, bugfix_counts)
    plot_bugfix_correlation(x_vals, y_vals, "complexity_bugfix_scatter.png")
    print(f"Histogram zapisany do: complexity_bugfix_scatter.png")
    print_correlation(x_vals, y_vals)

# ==

if __name__ == "__main__":
    main()
