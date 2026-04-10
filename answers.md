Porównaj wyniki radon vs lizard:

1. Czy oba narzędzia zgadzają się co do "najgorszej" funkcji?
    Tak, obydwa narzędzia jako "najgorszą" funkcję wskazały _encode_files z wynikiem CC 21 z oceną D

2. Czy wartości CC są identyczne? Jeśli nie - dlaczego?
    Jedna funkcja otrzymała różne wyniki, 16 w lizardzie, 18 w radonie.
    Po przyjrzeniu się funkcji nie widzę co wprost miałoby być liczone w inny sposób w tych dwóch narzędziach. Pierwszym podejrzeniem jest to, że Radon skupia się na języku Python, a Lizard to narzędzie do wielu języków. Może mają przez to inne podejście lub bardziej wyspecjalizowane. Może Radon wyłapał coś specyficznego dla Pythona.

3. Które narzędzie daje więcej informacji?
    Lizard zdecydowanie daje więcej informacji: Radon ocenia CC, a Lizard podaje dodatkowe dane jak NLOC czy ilość parametrów.

Znajdź "najgorszą" funkcję w projekcie - otwórz ją i oceń: czy naprawdę jest aż tak złożona, jak mówi metryka?

1. Funkcja encode_files z pliku models.py nie wygląda na przesadnie złożoną. Co prawda musimy (jak to często z plikami) być ostrożni i co chwila sprawdzać poprawność plików, wyłapywać errory i wyjątki, ale jak na ostrożną funkcję obsługującą pliki nie jest źle.


