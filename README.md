# Lab 05: Complexity Hell - zakamarki złożoności cyklomatycznej

![Gruszka po code review funkcji z CC > 50](gruszka.jpg)

## Czy wiesz, że...

Według badań (które właśnie wymyśliłem), rekord świata w złożoności cyklomatycznej jednej funkcji wynosi 2347. Funkcja ta obsługiwała formularz podatkowy w USA. Nikt nie wie, czy działa poprawnie, bo nikt nie jest w stanie napisać tylu testów.

## Kontekst

Na poprzednim labie liczyliśmy linie kodu - prosta metryka, ale mało mówi o tym, jak skomplikowana jest logika. Funkcja z 50 liniami prostych przypisań jest prostsza od funkcji z 20 liniami pełnymi zagnieżdżonych if-else.

Złożoność cyklomatyczna (Cyclomatic Complexity, CC) Thomasa McCabe'a z 1976 roku mierzy liczbę niezależnych ścieżek przez kod. Każdy `if`, `elif`, `for`, `while`, `and`, `or`, `except`, `assert` dodaje jedną ścieżkę. Im więcej ścieżek, tym trudniej zrozumieć funkcję, tym więcej testów potrzeba, i tym większe ryzyko bugów.

W praktyce CC służy do: identyfikacji funkcji wymagających refaktoryzacji, szacowania nakładu testowania, oceny jakości kodu w code review, i jako input do modeli predykcji defektów (które będziemy budować na labach 10-12).

## Cel laboratorium

Po tym laboratorium będziesz potrafić:
- wyjaśnić co mierzy złożoność cyklomatyczna i jak się ją liczy,
- używać narzędzi `radon` i `lizard` do analizy złożoności kodu Python,
- napisać skrypt generujący profil złożoności projektu z histogramem,
- interpretować wyniki i identyfikować funkcje wymagające refaktoryzacji.

## Wymagania wstępne

- Python 3.9+
- Pakiety z `requirements.txt`:
  ```bash
  python -m venv .venv
  source .venv/bin/activate   # Linux/Mac
  # .venv\Scripts\activate    # Windows
  pip install -r requirements.txt
  ```
- Sklonowany projekt open-source **w Pythonie**, z co najmniej kilkudziesięcioma plikami `.py`. `radon` działa wyłącznie z Pythonem - jeśli weźmiecie projekt w innym języku, radon zwróci pusty output. `lizard` obsługuje wiele języków, ale na tym labie pracujemy z radonem jako głównym narzędziem.

## Trochę teorii

### Jak liczyć CC?

Złożoność cyklomatyczna to: **CC = E - N + 2P**

Gdzie:
- E = liczba krawędzi w grafie przepływu
- N = liczba węzłów
- P = liczba połączonych komponentów (zwykle 1 dla jednej funkcji)

W praktyce liczy się prościej - zaczynamy od 1 i dodajemy 1 za każdy:
- `if`, `elif`
- `for`, `while`
- `and`, `or` (w warunkach)
- `except`
- `assert`

### Interpretacja wyników

| CC | Ranking | Znaczenie |
|----|---------|-----------|
| 1-5 | A | Prosta, łatwa do zrozumienia |
| 6-10 | B | Umiarkowana, do ogarnięcia |
| 11-20 | C | Złożona, kandydat do refaktoryzacji |
| 21-30 | D | Bardzo złożona, trudna w utrzymaniu |
| 31-40 | E | Alarmująca, na granicy zrozumienia |
| 41+ | F | Nie do utrzymania, refaktoryzuj natychmiast |

## Zadania

### Zadanie 1: radon i lizard (30 min)

Dwa narzędzia, dwa podejścia. Porównajmy.

**Krok 1:** Sklonuj projekt OSS (jeśli jeszcze nie masz):

> **WAŻNE:** Klonujcie repozytoria do `/tmp` albo innego katalogu POZA waszym repozytorium labowym. Jeśli sklonujecie je do katalogu roboczego i zrobicie `git add .`, commitniecie tysiące cudzych plików. Nie chcecie tego. Nikt tego nie chce.

```bash
cd /tmp
git clone https://github.com/psf/requests.git
```

Możesz wybrać inny projekt Pythonowy. Kilka propozycji:
- `https://github.com/pallets/flask.git` (flask - web framework)
- `https://github.com/encode/httpx.git` (httpx - klient HTTP)
- `https://github.com/psf/black.git` (black - formatter kodu)

Ważne żeby miał co najmniej kilkadziesiąt plików `.py` - inaczej analiza będzie zbyt uboga.

> **Uwaga o ścieżkach:** `requests` trzyma kod źródłowy w `src/requests/`. Inne projekty mogą mieć inną strukturę (np. `flask` trzyma kod w `src/flask/`, a `httpx` w `httpx/`). Sprawdźcie gdzie są pliki `.py` w waszym projekcie (`find /tmp/wasz-projekt -name "*.py" | head`) i dostosujcie ścieżki w komendach poniżej. W przykładach używamy `/tmp/requests/src/` - zamieńcie na właściwą ścieżkę do waszego projektu.

**Krok 2:** radon - złożoność cyklomatyczna:

```bash
# Analiza całego projektu
# -s = pokaż wartość CC przy każdej funkcji
# -a = pokaż średnią na końcu
radon cc /tmp/requests/src/ -s -a

# Tylko funkcje z rankingiem C i gorszym (CC >= 11)
# -n C = filtruj: pokaż ranking C, D, E, F (pomiń A i B)
radon cc /tmp/requests/src/ -s -n C

# Output jako JSON (przyda się w zadaniu 2 do zrozumienia struktury)
# -j = output w formacie JSON
radon cc /tmp/requests/src/ -s -j > radon_output.json
```

> Plik `radon_output.json` wyląduje w katalogu, w którym aktualnie jesteście w terminalu. Warto zajrzeć do niego w edytorze, żeby zobaczyć jak wygląda struktura JSON-a - przyda się w zadaniu 2.

**Krok 3:** radon - Maintainability Index:

```bash
# Indeks utrzymywalności (0-100, im wyżej tym lepiej)
# -s = pokaż wartość MI przy każdym pliku
radon mi /tmp/requests/src/ -s
```

**Krok 4:** lizard - wielojęzyczny analizator:

```bash
# Analiza z domyślnymi progami
lizard /tmp/requests/src/

# Tylko funkcje przekraczające próg CC > 10
# -C 10 = pokaż ostrzeżenia dla funkcji z CC > 10
lizard /tmp/requests/src/ -C 10

# Output jako CSV
lizard /tmp/requests/src/ --csv > lizard_output.csv
```

**Krok 5:** Porównaj wyniki radon vs lizard:

1. Czy oba narzędzia zgadzają się co do "najgorszej" funkcji?
2. Czy wartości CC są identyczne? Jeśli nie - dlaczego?
3. Które narzędzie daje więcej informacji?

**Krok 6:** Znajdź "najgorszą" funkcję w projekcie - otwórz ją i oceń: czy naprawdę jest aż tak złożona, jak mówi metryka?

Odpowiedzi z kroków 5 i 6 zapiszcie w `answers.md`.

### Zadanie 2: Complexity Profiler (60 min)

Napiszcie skrypt `complexity_profiler.py`, który generuje kompletny profil złożoności projektu.

**Co skrypt ma robić:**

1. Uruchomić radon na wskazanym katalogu (JSON output)
2. Sparsować wyniki
3. Wygenerować:
   - Ranking: top 20 najbardziej złożonych funkcji/metod
   - Statystyki: średnia CC, mediana, odchylenie standardowe
   - Rozkład: ile funkcji w każdym rankingu (A/B/C/D/E/F)
   - Procent funkcji z CC > 10
   - Histogram złożoności (matplotlib)

**Punkt startowy:**

```python
#!/usr/bin/env python3
"""Complexity Profiler - cyclomatic complexity analysis of Python projects."""

import json
import subprocess
import sys
from statistics import mean, median, stdev

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

    # TODO: Twój kod tutaj
    # 1. Policz mean(complexities), median(complexities)
    # 2. Policz stdev(complexities) - uwaga: wymaga >= 2 elementów!
    # 3. Policz rozkład rankingów: ile funkcji ma rank A, B, C, D, E, F
    #    (rank każdej funkcji masz w f["rank"])
    # 4. Policz ile funkcji ma CC > 10 i jaki to procent
    # 5. Zwróć to wszystko jako dict
    pass


def top_complex(functions: list[dict], n: int = 20) -> list[dict]:
    """Return top N most complex functions."""
    return sorted(functions, key=lambda f: f["complexity"], reverse=True)[:n]


def plot_histogram(functions: list[dict], output_path: str) -> None:
    """Plot and save complexity histogram."""
    complexities = [f["complexity"] for f in functions]

    # TODO: Twój kod tutaj
    # 1. plt.hist(complexities, bins=range(1, max(complexities)+2))
    #    - to da histogram z jednym słupkiem na każdą wartość CC
    # 2. Dodaj linie pionowe oznaczające progi rankingów:
    #    plt.axvline(x=5.5, color="...", linestyle="--", label="A/B")
    #    (analogicznie dla 10.5, 20.5, 30.5, 40.5)
    # 3. Opcjonalnie: kolorowanie słupków per rank
    #    Po plt.hist() możesz iterować po patches:
    #    for patch in plt.gca().patches:
    #        cc_val = patch.get_x()
    #        patch.set_facecolor("green" if cc_val < 6 else "yellow" if ...)
    # 4. plt.xlabel(...), plt.ylabel(...), plt.title(...)
    # 5. plt.savefig(output_path, dpi=150) - WAŻNE: zapisz do pliku!
    #    (sam plt.show() nie tworzy pliku PNG)
    pass


def print_report(functions: list[dict], stats: dict) -> None:
    """Print formatted complexity report."""
    print(f"\n{'=' * 70}")
    print(f"PROFIL ZŁOŻONOŚCI CYKLOMATYCZNEJ")
    print(f"{'=' * 70}")

    print(f"\n--- Statystyki ogólne ---")
    print(f"  Liczba funkcji/metod: {len(functions)}")
    # TODO: wydrukuj resztę statystyk ze słownika stats
    # (mean, median, stdev, procent z CC > 10)

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
    # TODO: wydrukuj rozkład A/B/C/D/E/F ze stats["rank_counts"]
    # Format: "  A (1-5):    142 (75.9%)  ████████████"
    # Pasek: np. chr(9608) * int(procent) albo "#" * int(procent)


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
```

**Oczekiwany output (przykład dla `requests`, kwiecień 2026):**

```
Analizuję złożoność: /tmp/requests/src/

======================================================================
PROFIL ZŁOŻONOŚCI CYKLOMATYCZNEJ
======================================================================

--- Statystyki ogólne ---
  Liczba funkcji/metod: 233
  Średnia CC:            3.5
  Mediana CC:            2.0
  Odch. standardowe:     3.7
  Funkcje z CC > 10:     13 (5.6%)

--- TOP 20 najbardziej złożonych ---
Rank   CC Typ      Nazwa                                    Plik:linia
------------------------------------------------------------------------------------------
  D    21 method   _encode_files                            ...requests/models.py:139
  C    19 method   build_digest_header                      ...requests/auth.py:126
  C    19 method   send                                     ...requests/adapters.py:591
  C    18 function super_len                                ...requests/utils.py:135
  C    17 method   prepare_url                              ...requests/models.py:411
  C    17 method   prepare_body                             ...requests/models.py:496
  ...

--- Rozkład rankingów ---
  A (1-5):    188 (80.7%)  ████████████████████████████████
  B (6-10):    32 (13.7%)  █████
  C (11-20):   12 (5.2%)   ██
  D (21-30):    1 (0.4%)
  E (31-40):    0 (0.0%)
  F (41+):      0 (0.0%)
```

> **Uwaga:** Wyniki mogą się nieco różnić w zależności od wersji `requests`. Ważne, żeby format i logika były poprawne - konkretne liczby mogą być inne.

### Zadanie 3: Złożoność vs bugi (45 min) - dla ambitnych

> **Uwaga:** Do tego zadania potrzebujecie pełnej historii repozytorium. Jeśli klonowaliście projekt z `--depth 1`, `git log` nie zwróci żadnych wyników. Sklonujcie ponownie bez tej flagi albo użyjcie `git fetch --unshallow`.

Czy pliki o wyższej złożoności mają więcej bugów? Sprawdźmy prostą korelację.

**Pomysł:**
- Dla każdego pliku `.py` w projekcie policz średnią CC (z radona)
- Z `git log` wyciągnij liczbę commitów z "fix"/"bug"/"error" w message dotyczących tego pliku
- Narysuj scatter plot: oś X = średnia CC, oś Y = liczba bugfix commitów (`plt.scatter(...)`)
- Policz korelację: `scipy.stats.pearsonr(x, y)` lub `scipy.stats.spearmanr(x, y)` (`pip install scipy`)

```python
import subprocess
from collections import Counter

def count_bugfix_commits(repo_path: str) -> dict[str, int]:
    """Count bugfix commits per file using git log."""
    result = subprocess.run(
        ["git", "log", "--format=%s", "--name-only",
         "--grep=fix", "--grep=bug", "--grep=error"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    # Parsowanie: commit message, potem lista plików, potem pusta linia
    file_counts = Counter()
    lines = result.stdout.strip().split("\n")
    for line in lines:
        if line.endswith(".py"):
            file_counts[line] += 1

    return dict(file_counts)
```

Uwaga: wiele flag `--grep` działa jako OR (commit pasuje, jeśli message zawiera "fix" LUB "bug" LUB "error"). Jeśli chcesz AND (wszystkie naraz), dodaj `--all-match`.

Uwaga 2: ścieżki plików w `git log` mogą nie zgadzać się ze ścieżkami z radona. Np. `requests` kiedyś trzymał kod w `requests/`, a teraz w `src/requests/`. Przy dopasowywaniu plików warto porównywać po samej nazwie pliku (np. `models.py`), nie po pełnej ścieżce.

## Co oddajecie

W swoim branchu `lab05_nazwisko1_nazwisko2`:

1. **`complexity_profiler.py`** - działający skrypt z zadania 2
2. **`complexity_histogram.png`** - wygenerowany histogram
3. **`answers.md`** - odpowiedzi z zadania 1 (porównanie radon vs lizard, analiza "najgorszej" funkcji)
4. *(opcjonalnie)* **`complexity_vs_bugs.png`** - scatter plot z zadania 3

## Kryteria oceny

- Skrypt poprawnie parsuje output radona (JSON)
- Statystyki (średnia, mediana, stdev) są wyliczone poprawnie
- Ranking top 20 jest posortowany malejąco po CC
- Rozkład rankingów A/B/C/D/E/F sumuje się do 100%
- Histogram jest czytelny i zawiera progi (5, 10, 20, 30, 40)
- Porównanie radon vs lizard w answers.md jest konkretne

## FAQ

**P: radon i lizard dają różne wartości CC dla tej samej funkcji.**
O: To normalne. Narzędzia mogą różnić się w szczegółach (np. czy `and`/`or` w warunkach zwiększa CC). Opisz różnice - to część zadania.

**P: Radon mówi, że klasa ma CC = 35, ale żadna metoda nie przekracza 10.**
O: CC klasy to suma CC jej metod. Klasa z 7 prostymi metodami po CC=5 będzie mieć CC=35. To niekoniecznie źle - patrzmy na metody, nie na klasę.

**P: Co to jest Maintainability Index?**
O: Wzór łączący CC, Halstead Volume i LOC. Skala 0-100 (im wyżej, tym łatwiej utrzymać). `radon mi` go liczy. Przydatny jako "quick glance", ale nie zastępuje szczegółowej analizy.

**P: Moja "najgorsza" funkcja to parser/dispatcher z wielkim switchem. Czy naprawdę jest zła?**
O: Niekoniecznie. CC karze rozgałęzienia, ale dispatcher z 20 prostymi case'ami może być łatwiejszy do zrozumienia niż skomplikowana rekurencja z CC=5. Metryka to nie wyrok - to sygnał do przyjrzenia się.

**P: `stdev()` wywala się z błędem gdy mam mało funkcji.**
O: `statistics.stdev()` wymaga co najmniej 2 elementów. Jeśli analizujesz mały projekt z jedną funkcją, musisz to obsłużyć - np. zwrócić 0.0 albo `None` i wypisać stosowny komunikat.

## Przydatne linki

- [radon documentation](https://radon.readthedocs.io/)
- [lizard documentation](https://github.com/terryyin/lizard)
- [McCabe's Cyclomatic Complexity (Wikipedia)](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Halstead complexity measures](https://en.wikipedia.org/wiki/Halstead_complexity_measures)
- [A Complexity Measure (McCabe, 1976) - oryginalny paper](https://doi.org/10.1109/TSE.1976.233837)

---
*"Prostota jest warunkiem koniecznym niezawodności."* - Edsger Dijkstra (ten cytat jest prawdziwy)
