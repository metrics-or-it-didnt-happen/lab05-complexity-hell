# Answers - Lab 05

Analizowany projekt: **requests** (`https://github.com/psf/requests`)

## Zadanie 1: Porównanie radon vs lizard

### Krok 5 - porównanie wyników

**1. Czy oba narzędzia zgadzają się co do "najgorszej" funkcji?**

Tak, oba wskazują `_encode_files` w `models.py` jako najgorszą - CC = 21 zarówno w radonie, jak i w lizardzie. Top 3 jest w zasadzie identyczny: `_encode_files` (21), `send` w adapterach (19), `build_digest_header` (19).

**2. Czy wartości CC są identyczne?**

Dla większości funkcji wartości się zgadzają, ale nie zawsze. Przykładowo `super_len` w `utils.py` - radon daje 18, lizard daje 16. Różnica wynika pewnie z tego, jak narzędzia traktują operatory logiczne `and`/`or` w warunkach. Radon liczy każdy `and`/`or` jako dodatkową ścieżkę (zgodnie z podejściem McCabe'a), a lizard podchodzi do tego trochę inaczej - traktuje niektóre warunki bardziej zbiorczo.

Generalnie różnice nie są duże (1-2 punkty CC), ale warto mieć to na uwadze, żeby nie porównywać bezpośrednio wyników z różnych narzędzi.

**3. Które narzędzie daje więcej informacji?**

Lizard dostarcza więcej danych - oprócz CC pokazuje jeszcze NLOC (linie kodu bez komentarzy), liczbę tokenów, liczbę parametrów i długość funkcji. Daje też ładne podsumowanie per plik (średni CC, średni NLOC itd.). Radon z kolei ma Maintainability Index (`radon mi`), którego lizard nie oferuje, i lepiej radzi sobie z hierarchią klas w Pythonie (czytelniejszy output z rankingiem A-F). Oba narzędzia się dobrze uzupełniają - radon jest bardziej "pythonowy" i skupiony na metrykach jakości, lizard jest bardziej uniwersalny i daje więcej surowych danych.

### Krok 6 - analiza "najgorszej" funkcji

Najgorsza funkcja to `_encode_files` w `models.py` (linia 139), CC = 21, ranking D.

Ta metoda buduje body dla multipart/form-data requestów. Patrząc na kod - jest tam sporo rozgałęzień, ale wynikają one z obsługi różnych formatów wejściowych (tuple 2-, 3-, 4-elementowe, stringi vs bajty vs pliki z `read()`). Każdy wariant to osobny `if`/`elif`, więc CC rośnie szybko.

Czy naprawdę jest tak złożona? Średnio. Logicznie to taki parser/konwerter, który musi obsłużyć kilka przypadków - sam flow jest raczej liniowy (nie ma jakiejś szalonej rekurencji czy zagnieżdżonych pętli). CC = 21 brzmi groźnie, ale w praktyce jak czytasz tę funkcję od góry do dołu, to daje się ogarnąć bez większego problemu. Metryka tutaj trochę przesadza, bo te rozgałęzienia są dość niezależne od siebie - to bardziej "szeroka" logika niż "głęboka".

Z drugiej strony, gdyby ktoś chciał to refaktoryzować, mógłby wydzielić parsowanie tupli plików do osobnej funkcji i obsługę pól formularza do kolejnej. Ale szczerze - w bibliotece tak stabilnej jak requests pewnie nie warto tego ruszać.
