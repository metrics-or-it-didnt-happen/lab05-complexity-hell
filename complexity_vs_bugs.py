#!/usr/bin/env python3
"""Correlation between cyclomatic complexity and bug fixes for Python projects."""

import subprocess
import sys
from collections import Counter, defaultdict
from scipy.stats import pearsonr
from complexity_profiler import run_radon, extract_functions
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  
plt.rcParams["font.family"] = "Times New Roman"

def compute_cc_per_file(functions: list[dict]) -> dict[str, float]:
    cc_by_file = defaultdict(list)
    for f in functions:
        cc_by_file[f["file"]].append(f["complexity"])

    return {
        file : sum(values)/len(values)
        for file, values in cc_by_file.items()
    }

def count_bugfix_commits(repo_path: str) -> dict[str, int]:
    """Count bugfix commits per file using git log."""
    result = subprocess.run(
        ["git", "log", 
         "--format=%s", "--name-only",
         "--grep=fix",
         "--grep=bug",
         "--grep=error"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    def normalize_path(path, root):
        return root+"/"+path.split(f"{root}/")[-1]

    file_counts = Counter()
    lines = result.stdout.strip().split("\n")
    for line in lines:
        if line.endswith(".py"):
            file_counts[normalize_path(line, repo_path)] += 1          

    return dict(file_counts)

def correlate_cc_and_bugs(cc_per_file: dict[str, float], bug_counts: dict[str, int]):
    data = []
    for file, cc in cc_per_file.items():
        bugs = bug_counts.get(file, 0)
        data.append({
            "file": file,
            "cc": cc,
            "bugs": bugs
        })
    return data

def plot_cc_vs_bugs(data: list[dict], output_path: str):
    x = [d["cc"] for d in data]
    y = [d["bugs"] for d in data]
    corr, _ = pearsonr(x, y)

    plt.figure()
    plt.scatter(x, y)

    plt.xlabel("Average CC per file")
    plt.ylabel("Bugfix commits")
    plt.title(f"Complexity vs Bugs (Correlation: {corr:.2f})")

    plt.savefig(output_path)
    plt.close()

    return corr

def main():
    if len(sys.argv) < 2:
        print("Użycie: python complexity_vs_bugs.py <ścieżka_do_projektu>")
        sys.exit(1)

    project_path = sys.argv[1]
    print(f"Analizuję CC vs. bugs: {project_path}")
    project_path = str(Path(project_path))

    radon_data = run_radon(project_path)
    functions = extract_functions(radon_data)
    if not functions:
        print("Nie znaleziono funkcji do analizy.")
        sys.exit(1)

    cc_per_per_file = compute_cc_per_file(functions)
    bug_counts = count_bugfix_commits(project_path)
    data = correlate_cc_and_bugs(cc_per_per_file, bug_counts)
    corr = plot_cc_vs_bugs(data, "complexity_vs_bugs.png")

    print(f"\nKorelacja CC vs. bugi: {corr:.3f}")
    print(f"\nWykres zapisany do: complexity_vs_bugs.png")


if __name__ == "__main__":
    main()