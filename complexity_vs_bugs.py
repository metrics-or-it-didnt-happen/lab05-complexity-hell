#!/usr/bin/env python3
"""Complexity vs Bugs - korelacja pomiędzy CC a liczbą bugfixów."""

import subprocess
import json
import sys
import os
from collections import Counter
from statistics import mean
import matplotlib.pyplot as plt

try:
    from scipy.stats import pearsonr
except ImportError:
    print("Błąd: Brak biblioteki scipy. Uruchom: pip install scipy")
    sys.exit(1)


def count_bugfix_commits(repo_path: str) -> dict[str, int]:
    """Zlicza commity typu bugfix dla każdego pliku, używając logów gita."""
    # Używamy flagi -i (case-insensitive) oraz -E (rozszerzone regexy) jako logiczne OR
    result = subprocess.run(
        ["git", "log", "--format=%s", "--name-only", "-i", "-E", "--grep=(fix|bug|error)"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    file_counts = Counter()
    lines = result.stdout.strip().split("\n")
    for line in lines:
        if line.endswith(".py"):
            # Pobieramy tylko nazwę pliku, co ułatwi parowanie z danymi z radona
            # (Git podaje inną ścieżkę wzgledną niż Radon)
            filename = os.path.basename(line)
            file_counts[filename] += 1

    return dict(file_counts)


def get_file_complexities(repo_path: str) -> dict[str, float]:
    """Uruchamia radona, parsuje JSON i zwraca średnią wartość CC dla plików."""
    result = subprocess.run(
        ["radon", "cc", repo_path, "-s", "-j"],
        capture_output=True,
        text=True,
    )

    if not result.stdout.strip():
        return {}

    radon_data = json.loads(result.stdout)
    file_cc_means = {}

    for filepath, items in radon_data.items():
        complexities = []
        for item in items:
            if item["type"] in ("function", "method"):
                complexities.append(item["complexity"])

        if complexities:
            filename = os.path.basename(filepath)
            file_cc_means[filename] = mean(complexities)

    return file_cc_means


def main():
    if len(sys.argv) < 2:
        print("Użycie: python complexity_vs_bugs.py <ścieżka_do_repo_git>")
        sys.exit(1)

    repo_path = sys.argv[1]
    print(f"Analizuję historię GIT i złożoność dla repozytorium: {repo_path} ...")

    # Pobranie danych z obu narzędzi
    bugfixes = count_bugfix_commits(repo_path)
    complexities = get_file_complexities(repo_path)

    if not complexities:
        print("Nie znaleziono danych o złożoności (upewnij się, że repozytorium zawiera kod Python).")
        sys.exit(1)

    # Parowanie danych po nazwie pliku
    x_cc = []
    y_bugs = []

    for filename, cc_mean in complexities.items():
        x_cc.append(cc_mean)
        # Jeśli plik nie wystąpił w commitach typu bugfix, przypisujemy 0
        y_bugs.append(bugfixes.get(filename, 0))

    if len(x_cc) < 2:
        print("Za mało danych, aby obliczyć korelację (minimum 2 pliki .py z funkcjami).")
        sys.exit(1)

    # Obliczanie korelacji Pearsona
    correlation, p_value = pearsonr(x_cc, y_bugs)
    print(f"Współczynnik korelacji Pearsona: {correlation:.3f} (p-value: {p_value:.3f})")

    # Rysowanie wykresu
    plt.figure(figsize=(10, 6))
    plt.scatter(x_cc, y_bugs, alpha=0.6, color='dodgerblue', edgecolors='black', s=50)

    plt.title(f"Złożoność cyklomatyczna vs. Liczba Bugfixów\nKorelacja Pearsona: {correlation:.2f}", fontsize=14)
    plt.xlabel("Średnia Złożoność Cyklomatyczna w pliku (CC)", fontsize=12)
    plt.ylabel("Liczba naprawionych błędów (Bugfix commits)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)

    # Zapis
    output_filename = "complexity_vs_bugs.png"
    plt.savefig(output_filename, dpi=150, bbox_inches='tight')
    print(f"Gotowe! Wykres zapisano do pliku: {output_filename}")


if __name__ == "__main__":
    main()