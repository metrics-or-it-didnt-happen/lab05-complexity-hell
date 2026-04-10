1. Czy oba narzędzia zgadzają się co do "najgorszej" funkcji
Tak, obydwa na rzędzia mówią, ze najgorszy co do zlozonosci jest _encode_files, z wynikiem CCN=21. 
Sa tez zgodne w przypadku 2giego miejsca np HttpAdapter.send i build_digest_header

2. Są identyczne dla wszystkich, ale super_len ma wg Radona 18, wg Lizarda 16.
Roznica w tej funkcji wynika z specyfikacji jezykowej i tego, ze radon uznaje obsulge bledow za dodatkowy element sciezki, co dzieje sie w except io.UnsupportedOperation, AttirbuteError.
Inna mozliwosc to rozgalezienia w ifie - jezeli mamy warunek A or B lub A and B moze to byc odpowiedon policzone przez radon jako 2 elementy, a lizard moglby je policzyc jako 1.
Radon liczzy takze asserta jako ifa, przez co moze dodac dodatkowy punkt do CC

3. lizard dostarcza zdecyowanie wiecej metry, np nloc- liczbe linijek bez komentarzy, token, liczbe parametrow przekazywanych do funkcji, radon dostarcza nam za to ocene A-F

4. Mamy zagniezdzone fory, list comprehension, duzo orow, oraz wiele odwolan do innych funkcji, ale jest to konieczne, aby pokryc edge-cases ktore moga wystapic podczas tej funkcji, dodatkowo musi ona pokrywac wiele typow plikow.
Kod sam w sobie nie jest az tak dlugi, na pewno moglby byc uproszczony.
