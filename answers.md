# Zadanie 1: porownanie radon vs lizard (projekt: requests)

### 5.1) Czy oba narzedzia zgadzaja sie co do "najgorszej" funkcji?

Tak. Oba narzedzia wskazuja te sama funkcje:

- `requests/models.py`, funkcja/metoda `_encode_files`, linia startowa 139
- `radon`: CC = 21, rank D
- `lizard`: CCN = 21, NLOC = 49, token_count = 311, parameter_count = 2, length = 67

Wniosek: co do lidera "complexity hell" wyniki sa zgodne 1:1.

### 5.2) Czy wartosci CC sa identyczne? Jesli nie, to dlaczego?

W wiekszosci tak, ale nie w 100%.

- wspolne rekordy (to samo `file + function_name + start_line`): 233
- identyczne CC: 228/233 (97.9%)
- rozne CC: 5/233 (2.1%)

Przyklady roznic:

- `requests/__init__.py::check_compatibility` (linia 58): `radon 10` vs `lizard 5`
- `requests/utils.py::super_len` (linia 135): `radon 18` vs `lizard 16`
- `requests/_internal_utils.py::unicode_is_ascii` (linia 39): `radon 3` vs `lizard 2`
- `requests/utils.py::extract_zipped_paths` (linia 257): `radon 7` vs `lizard 8`
- `requests/utils.py::set_environ` (linia 731): `radon 4` vs `lizard 5`

Dlaczego sa roznice:

- narzedzia maja inny parser i inna definicje tego, co dokladnie podbija CC,
- moga inaczej traktowac np. operatory logiczne, wyrazenia zlozone, szczegoly konstrukcji warunkowych,
- `lizard` jest bardziej jezykowo-agnostyczny, a `radon` jest stricte pod Pythona.

Wniosek: metryka jest porownywalna, ale nie jest matematycznie identyczna miedzy narzedziami.

### 5.3) Ktore narzedzie daje wiecej informacji?

To zalezy od celu:

- `radon` lepiej wspiera ocene jakosci kodu w Pythonie: ma ranki A-F i latwo laczy sie z `radon mi` (Maintainability Index).
- `lizard` daje bogatszy profil funkcji: poza CC ma od razu `NLOC`, `token_count`, `parameter_count`, `length` i wygodny CSV do dalszej analizy.

Praktycznie:

- do szybkiej oceny "czy to jest zbyt zlozone" i pracy stricte Pythonowej: `radon`,
- do tabel, raportow, porownan i dalszej obrobki danych: `lizard`.

## 6) analiza "najgorszej" funkcji

Analizowana funkcja: `_encode_files` w `requests/models.py` (139-205).

Ocena metryki:

- wynik `CC = 21` (D) jest wysoki i uzasadniony,
- funkcja obsluguje wiele przypadkow wejscia i ma kilka poziomow rozgalezien.

Co podbija zlozonosc:

- walidacja wejscia (`if not files`, `elif isinstance(data, basestring)`),
- normalizacja danych w 2 petlach (`for field, val ...` i `for k, v ...`),
- kilka galezi typu/ksztaltu danych (tuple 2/3/4 elementowe, str/bytes/file-like/None),
- dodatkowe warunki wewnatrz petli (`if v is not None`, `if not isinstance(v, bytes)`, itp.).

Czy funkcja jest "zla"?

- Jest trudniejsza w utrzymaniu i testowaniu niz przecietna funkcja.
- Jednoczesnie czesc zlozonosci jest domenowo uzasadniona: to warstwa I/O i normalizacji wielu formatow wejscia multipart/form-data.

Wniosek praktyczny: metryka poprawnie sygnalizuje ryzyko, ale nie oznacza automatycznie bledu projektowego. To dobry kandydat do refaktoryzacji na mniejsze helpery (np. osobno: normalizacja `fields`, dekodowanie tuple plikow, odczyt `fdata`).
