## Zadanie 1

### Krok 5
Lizard

`lizard /tmp/requests/src/ -C 20`

```
===========================================================================================================
!!!! Warnings (cyclomatic_complexity > 20 or length > 1000 or nloc > 1000000 or parameter_count > 100) !!!!
================================================
  NLOC    CCN   token  PARAM  length  location  
------------------------------------------------
      49     21    311      2      67 _encode_files@139-205@/tmp/requests/src/requests/models.py
==========================================================================================
```
Radon

 `radon cc /tmp/requests/src/ -s -n D`

`/tmp/requests/src/requests/models.py
    M 139:4 RequestEncodingMixin._encode_files - D (21)`

1) Najgorsza funkcja dla Radona i Lizarda (CC=21):
`RequestEncodingMixin._encode_files` w pliku `models.py`

2) W przypadku najgorszej funkcji złożoność cyklomatyczna wyświetlana przez oba narzędzia jest taka sama. Natomiast, gdy spojrzymy na inne funkcje to możemy znaleźć różnice.
Przykłady różnic:
- `super_len` w `utils.py`: 18 (radon) vs 16 (lizard)
- 'extract_zipped_path' w `utils.py`: 7 (radon) vs 8 (lizard)
- 'set_environ' w 'utils.py': 4 (radon) vs 5 (lizard)

Te różnice mogą wynikać z tego, że radon jest dedykowanym narzędziem dla pythona, a lizard jest wielojęzycznym narzędziem.
Znaleźliśmy informację, że radon korzysta z analizy AST (Abstract Syntax Tree), dzięki temu może "lepiej" rozumieć składnię pythona.
Natomiast lizard może korzystać z innych sposobów analizy, a wskazywać na to może prezentacja liczby tokenów.


3) Lizard, bo Radon pokazuje wyłącznie złożoność cyklomatyczną i ranking. Natomiast lizard wyświetla nam dodatkowo NLOC, liczbę tokenów, liczbę parametrów
i długość funkcji. Lizard również pozwala nam wyświetlać warningi jak dodamy `-C (liczba CC)`. Na końcu outputu lizard generuje podsumowanie, które zawiera
sumę NLOC, średnie NLOC, średnie CC, średnią liczbę tokenów, liczbę funkcji i liczbę funkcji z warningami. Natomiast na korzyść radona jest możliwość wyświetlenia maintainability index dla każdego pliku w katalogu.

### Krok 6
Pomimo wysokiej wartości CC najgorsza funkcja jest czytelna. Złożoność cyklomatyczna głównie wynika z wymagań, które ma spełniać ta funkcja.
Odpowiada ona za budowę ciała (formatowanie i przygotowanie danych) do formatu `multipart/form-data request`. Możemy mieć tutaj 3 różne rodzaje tupli (2,3,4-elementowe),
więc bardziej złożona ifologia czy dwa zagnieżdżone fory, są jak najbardziej wymagane. Nie mamy tutaj bardzo skomplikowanej logiki, ani nadmiarowej złożoności samego kodu.
W tym przypadku pomimo dużego CC, jest przejrzyście.
