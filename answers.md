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

1) Najgorsza funkcja dla Radona i Lizarda:
`RequestEncodingMixin._encode_files` 

2) Są identyczne (CC=21)
3) Lizard, bo Radon pokazuje wyłącznie złożoność cyklomatyczną i ranking.

### Krok 6
Nie jest najgorsza. Są dwa zagnieżdzone fory oraz złożona ifologia.
