### Porównanie wyników `radon` vs. `lizard`

1. **Czy oba narzędzia zgadzają się co do "najgorszej" funkcji?**
    
    **Tak.** Jest to metoda `_encode_files` klasy `RequestEncodingMixin` w pliku `requests/src/requests/models.py` (linie 139-205) z wynikem **D (21).**
    
2. **Czy wartości CC są identyczne? Jeśli nie - dlaczego?**
    
    **Znalezione rozbieżności (na łącznie ~240 rekordów):**
    
    | plik | fukcja | linie | CC `radon`  | CC `lizard`  |
    | --- | --- | --- | --- | --- |
    | `requests/**init**.py` | `check_compatibility` | 58-90 | 10 | 5 |
    | `requests/_internal_utils.py` | `unicode_is_ascii` | 39-51 | 3 | 2 |
    | `requests/utils.py` | `super_len` | 135-203 | 18 | 16 |
    | `requests/utils.py` | `extract_zipped_paths` | 257-292 | 7 | 8 |
    | `requests/utils.py` | `set_environ` | 731-749 | 4 | 5 |
    
    Pojawia się także różnica liczby rekordów pomiędzy narzędziami, która wynika z odmiennego sposobu analizy kodu. `radon` raportuje złożoność na poziomie funkcji i metod, traktując funkcje zagnieżdżone jako część funkcji nadrzędnej. Natomiast `lizard` analizuje każdą funkcję, w tym funkcje zdefiniowane wewnątrz innych funkcji (closures), jako osobne jednostki. W rezultacie `lizard` zwraca dodatkowe rekordy odpowiadające funkcjom pomocniczym, które w `radon` nie są uwzględniane jako niezależne elementy.
    
    Konkretnie w naszym przykładnie `lizard` zwrócił **o 7 rekordów więcej**. Przykładowo dla funkcji `build_digest_header` z pliku `requests/auth.py`  (linie 126-234) o CC=19 wyodrębnił:

    - `build_digest_header.md5_utf8` (linie 145-148) → CC=2

    - `build_digest_header.sha_utf8` (linie 153-156) → CC=2

    - `build_digest_header.sha256_utf8` (linie 161-164) → CC=2

    - `build_digest_header.sha512_utf8` (linie 169-172) → CC=2
    
    OSTATECZNIE: wartości CC **nie są identyczne**.
    
    UZASADNINIE: 
    Chociaż oba narzędzia opierają się na tej samej definicji CC, to **mogą różnić się szczegółami interpretacji konstrukcji językowych, takich jak operatory logiczne, wyjątki czy złożone wyrażenia**. Dodatkowo **`radon` wykorzystuje analizę drzewa składniowego Pythona (AST)**, podczas gdy **`lizard` stosuje własny, bardziej ogólny mechanizm analizy kodu**. W konsekwencji poszczególne elementy kodu mogą być liczone w różny sposób, co prowadzi do pewnych (raczej niewielkich) rozbieżności w wynikach. 
    
3. **Które narzędzie daje więcej informacji?**

    Więcej informacji daje `lizard`, bo **raportuje dodatkowe metryki** (NLOC, liczba parametrów, tokeny), **analizuje funkcje zagnieżdżone** oraz **generuje podsumowania i ostrzeżenia**. `radon` skupia się głównie na złożoności cyklomatycznej, tworząc bardziej uproszczony raport, ale z drugiej strony oferuje **przejrzystą klasyfikację złożoności (A–F)**, co ułatwia szybką ocenę jakości kodu. Dodatkowo `radon` może analizować **inne metryki** (np. Maintainability Index czy metryki Halsteada), jednak nie są one domyślnie uwzględniane w analizie CC.

### Ocena “najgorszej” funkcji w projekcie

```python
def _encode_files(files, data):
    """Build the body for a multipart/form-data request.

    Will successfully encode files when passed as a dict or a list of
    tuples. Order is retained if data is a list of tuples but arbitrary
    if parameters are supplied as a dict.
    The tuples may be 2-tuples (filename, fileobj), 3-tuples (filename, fileobj, contentype)
    or 4-tuples (filename, fileobj, contentype, custom_headers).
    """
    if not files:
        raise ValueError("Files must be provided.")
    elif isinstance(data, basestring):
        raise ValueError("Data must not be a string.")

    new_fields = []
    fields = to_key_val_list(data or {})
    files = to_key_val_list(files or {})

    for field, val in fields:
        if isinstance(val, basestring) or not hasattr(val, "__iter__"):
            val = [val]
        for v in val:
            if v is not None:
                # Don't call str() on bytestrings: in Py3 it all goes wrong.
                if not isinstance(v, bytes):
                    v = str(v)

                new_fields.append(
                    (
                        field.decode("utf-8")
                        if isinstance(field, bytes)
                        else field,
                        v.encode("utf-8") if isinstance(v, str) else v,
                    )
                )

    for k, v in files:
        # support for explicit filename
        ft = None
        fh = None
        if isinstance(v, (tuple, list)):
            if len(v) == 2:
                fn, fp = v
            elif len(v) == 3:
                fn, fp, ft = v
            else:
                fn, fp, ft, fh = v
        else:
            fn = guess_filename(v) or k
            fp = v
            
        if isinstance(fp, (str, bytes, bytearray)):
            fdata = fp
        elif hasattr(fp, "read"):
            fdata = fp.read()
        elif fp is None:
            continue
        else:
            fdata = fp

        rf = RequestField(name=k, data=fdata, filename=fn, headers=fh)
        rf.make_multipart(content_type=ft)
        new_fields.append(rf)

    body, content_type = encode_multipart_formdata(new_fields)

    return body, content_type
```

**Czy powyższa funkcja naprawdę jest aż tak złożona, jak mówi metryka (CC=21 → D)?**

Wysoka wartość CC dla tej funkcji wiąże się z **dużą liczbą punktów dycyzyjne**, które wynikają z:

- defensywnej walidacji danych wejściowych (np. `if not files` )
- obsługi wielu formatów (stringi, obiekty iterowalne, różney typy wejścia)
- rozgałęzień dla różnych struktur plików: *(filename, file), (filename, file, type), (filename, file, type, headers)*
- obsługi różnych typów danych plików (np. `if isinstance(fp, (str, bytes, bytearray))` )

Zatem większość złożoności pochodzi **z sekwencyjnej obsługi przypadków**, a nie skomplikowanej logiki czy trudych zależności między warunkami. **Ostatecznie funkcja ta jest mocno złożona strukturalnie, a niekoniecznie poznawczo.** W takich przypadkach CC może przeszacowywać rzeczywistą trudność utrzymania kodu.

### Ważne uzupełnienie
![](duszka.png)
Gruszka jest wspaniała, a Duszka ją pozdrawia.