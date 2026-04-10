# Zadanie 1 — Porównanie radon vs lizard

## Porównanie wyników radon vs lizard

### 1. Czy oba narzędzia zgadzają się co do „najgorszej" funkcji?

**Tak** — oba narzędzia wskazują tę samą funkcję jako najgorszą:

| Narzędzie | Najgorsza funkcja | Plik | CC |
|-----------|--------------------|------|----|
| radon | `_encode_files` | `models.py:139` | **21** (rank D) |
| lizard | `_encode_files` | `models.py:139` | **21** |

Pozostałe funkcje z czołówki również się pokrywają (z drobnymi różnicami w kolejności):

| Funkcja | radon CC | lizard CC |
|---------|----------|-----------|
| `_encode_files` | 21 | 21 |
| `build_digest_header` | 19 | 19 |
| `HTTPAdapter.send` | 19 | 19 |
| `super_len` | 18 | 16 |
| `prepare_url` | 17 | 17 |
| `prepare_body` | 17 | 17 |
| `should_bypass_proxies` | 17 | 17 |
| `resolve_redirects` | 15 | 15 |
| `cert_verify` | 14 | 14 |
| `get_netrc_auth` | 12 | 12 |

### 2. Czy wartości CC są identyczne? Jeśli nie — dlaczego?

Wartości CC są **w większości identyczne**, ale pojawiają się drobne różnice, np. dla `super_len`: radon = 18, lizard = 16.

Przyczyny rozbieżności:

- **Różne traktowanie `and`/`or` w warunkach złożonych.** Radon domyślnie liczy każdy operator logiczny `and`/`or` jako osobną ścieżkę (zwiększając CC o 1 za każdy). Lizard z kolei traktuje cały warunek jako jedno rozgałęzienie — stąd radon może dać wyższe wartości dla funkcji z wieloma warunkami złożonymi.
- **Obsługa `assert`.** Radon liczy `assert` jako punkt rozgałęzienia (bo `assert` to w istocie `if not ...: raise`). Lizard nie zawsze je uwzględnia.
- **Klasyfikacja funkcji vs metod.** Radon wyróżnia klasy i ich metody osobno (277 „bloków" w analizie, łącznie z klasami). Lizard nie liczy klas — raportuje tylko 240 funkcji/metod. To wpływa na średnie statystyki.

### 3. Które narzędzie daje więcej informacji?

| Cecha | radon | lizard |
|-------|-------|--------|
| Wartość CC per funkcja | ✅ | ✅ |
| Ranking literowy (A–F) | ✅ | ❌ |
| Maintainability Index (MI) | ✅ (`radon mi`) | ❌ |
| NLOC (linie kodu per funkcja) | ❌ | ✅ |
| Liczba tokenów | ❌ | ✅ |
| Liczba parametrów | ❌ | ✅ |
| Wielojęzyczność | ❌ (tylko Python) | ✅ (C/C++, Java, JS...) |
| Output JSON | ✅ | ❌ (CSV) |
| Output CSV | ❌ | ✅ |
| Średnie per plik | ❌ | ✅ |

**Podsumowanie:** Radon daje lepszy obraz jakości kodu Python (rankingi A–F, MI, JSON do automatyzacji). Lizard daje więcej informacji o samych funkcjach (NLOC, tokeny, parametry) i jest przydatny w projektach wielojęzycznych. Do analizy czysto pythonowego projektu **radon jest bardziej kompletny**, ale lizard lepiej nadaje się do identyfikacji funkcji, które są problematyczne pod wieloma kątami jednocześnie (długie, złożone i z wieloma parametrami).

---

## Analiza „najgorszej" funkcji

### Funkcja: `RequestEncodingMixin._encode_files` (CC = 21, rank D)

**Plik:** `src/requests/models.py`, linia 139  
**Co robi:** Buduje body dla requestu `multipart/form-data` — koduje pola formularza i pliki do postaci gotowej do wysłania przez HTTP.

### Kod (fragment kluczowy):

```python
def _encode_files(files, data):
    if not files:                              # +1
        raise ValueError(...)
    elif isinstance(data, basestring):         # +1
        raise ValueError(...)

    for field, val in fields:                  # +1
        if isinstance(val, basestring) or not hasattr(val, "__iter__"):  # +1, +1 (or)
            val = [val]
        for v in val:                          # +1
            if v is not None:                  # +1
                if not isinstance(v, bytes):   # +1
                    v = str(v)
                # ... isinstance checks for encoding: +1, +1

    for k, v in files:                         # +1
        if isinstance(v, (tuple, list)):       # +1
            if len(v) == 2:                    # +1
                ...
            elif len(v) == 3:                  # +1
                ...
            else:                              # (domyślna gałąź, nie liczy się)
                ...
        else:                                  # (domyślna gałąź)
            ...
        if isinstance(fp, (str, bytes, bytearray)):  # +1
            ...
        elif hasattr(fp, "read"):              # +1
            ...
        elif fp is None:                       # +1
            continue
```

### Ocena: Czy naprawdę jest aż tak złożona?

**Częściowo tak, częściowo nie.**

**Argumenty „nie jest aż tak źle":**
- Funkcja jest **liniowa w logice** — nie ma skomplikowanej rekurencji ani nieoczywistych efektów ubocznych. Każda gałąź `if/elif` obsługuje inny format wejścia (2-tuple, 3-tuple, 4-tuple) — to typowy pattern "parser/adapter" dla elastycznego API.
- Kod jest dobrze udokumentowany i czytelny — programista Pythona zrozumie go bez problemu.
- CC = 21 wynika głównie z **wielu `isinstance` i `or` w warunkach**, a nie z głęboko zagnieżdżonej logiki.

**Argumenty „jest faktycznie złożona":**
- Funkcja robi **dwie różne rzeczy**: kodowanie pól formularza (linie 157–173) i kodowanie plików (linie 175–201). Mogłaby być rozbita na dwie mniejsze.
- Obsługuje **wiele formatów wejścia** (string, bytes, tuple o 2/3/4 elementach, file-like object, None). To zwiększa liczbę testów potrzebnych do pełnego pokrycia — CC = 21 oznacza minimum 21 ścieżek testowych.
- Przy CC > 20 (rank D) funkcja jest kandydatem do refaktoryzacji — np. wyodrębnienie `_encode_form_fields()` i `_encode_file_entry()` zmniejszyłoby CC każdej z nich do ~10.

**Werdykt:** Metryka CC = 21 jest **uzasadniona** — funkcja faktycznie obsługuje wiele scenariuszy. Nie jest „nie do utrzymania" (rank D, nie F), ale mogłaby skorzystać na wydzieleniu podoperacji. Jest to dobry przykład sytuacji, gdy CC trafnie identyfikuje kandydata do refaktoryzacji, nawet jeśli aktualny kod jest czytelny.
