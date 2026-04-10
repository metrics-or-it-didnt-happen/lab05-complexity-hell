#!/usr/bin/env python3
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from scipy.stats import pearsonr


def get_cc_per_file(repo_path: Path) -> dict[str, float]:
    result = subprocess.run(
        ["radon", "cc", str(repo_path), "-j"],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(result.stdout)
    cc_map = {}

    for filepath, elements in data.items():
        if not elements:
            continue

        complexities = [item["complexity"] for item in elements]
        for item in elements:
            complexities.extend(m["complexity"] for m in item.get("methods", []))

        if complexities:
            abs_path = str((repo_path / filepath).resolve())
            cc_map[abs_path] = sum(complexities) / len(complexities)

    return cc_map


def count_bugfix_commits(repo_path: Path) -> dict[str, int]:
    result = subprocess.run(
        ["git", "log", "-i", "-E", "--grep=fix|bug|error", "--name-only", "--format="],
        cwd=str(repo_path),
        capture_output=True,
        text=True
    )

    file_counts = Counter()
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.endswith(".py"):
            abs_path = str((repo_path / line).resolve())
            file_counts[abs_path] += 1

    return dict(file_counts)


def main():
    if len(sys.argv) < 2:
        sys.exit("Użycie: python complexity_vs_bugs.py <ścieżka_do_repo>")

    repo_path = Path(sys.argv[1]).resolve()
    print(f"Analizowanie repozytorium: {repo_path}...")

    cc_data = get_cc_per_file(repo_path)
    bug_data = count_bugfix_commits(repo_path)

    x_cc = []
    y_bugs = []

    for filepath, cc in cc_data.items():
        x_cc.append(cc)
        y_bugs.append(bug_data.get(filepath, 0))

    if not x_cc:
        sys.exit("Brak danych do analizy (nie znaleziono plików .py lub brak historii git).")

    corr, p_value = pearsonr(x_cc, y_bugs)

    print("-" * 50)
    print(f"Przeanalizowano plików: {len(x_cc)}")
    print(f"Korelacja Pearsona:    {corr:.4f}")
    print(f"Wartość p-value:       {p_value:.4e}")
    print("-" * 50)

    plt.figure(figsize=(10, 6))
    plt.scatter(x_cc, y_bugs, alpha=0.6, edgecolors="k", color="#1f77b4")
    plt.title("Korelacja: Średnia Złożoność Cyklomatyczna vs Liczba Bugfixów")
    plt.xlabel("Średnia CC na plik (Radon)")
    plt.ylabel("Liczba commitów fix/bug/error (Git)")
    plt.grid(True, linestyle="--", alpha=0.7)

    output_file = "complexity_vs_bugs.png"
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Wykres zapisano jako {output_file}")


if __name__ == "__main__":
    main()