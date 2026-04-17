Analizuje repo z flaska:

1. Zgadzaja sie co do najgorszej funkcji -> jest to Blueprint.register w blueprints.py o zlozonosci 23

2. Wiekszosc taka sama,ale nie zgadzaja sie w paru miejscach. Np w pliku debughelpers.py, dla "explain_templates_loading_attempts", radon daje mu 13 a lizard 12.
Przy recznym sprawdzeniu wyszla mi zlozonosc dla tej funkcji rowna 12, wiec najwidoczniej radon cos zlapal, bylo np w stringu i zawieralo "trying" bo np "try"
moglo by byc policzone jako +1?

3. Oba sa z grubsza podobne, ale wyglada ze Radon troche konkretniej daje bo jest pod Pythona. Zawiera to Maintability Indeks, Haldstead Metrics, mozna nie skupiac
sie na samej CC ale szukac czegos co jest podejrzane np w 2 z 3 parametrow.

4. Przejrzalem wlasnie ta funckje o zlozonosci 23 z pliku blueprints.py -> jest umiarkowanie trudna, powiedzialbym takie 6.5/10. Nie ma mocno zagniezdzonych ifow, wiec 
logike w miare da sie przesledzic, zeby glebiej zrozumiec trzeba by zrobic insight. Jest sciana "ifow" ktorej nie dokonca jest obtymalna, np:
            if bp_url_prefix is None:
                bp_url_prefix = blueprint.url_prefix

            if state.url_prefix is not None and bp_url_prefix is not None:
                bp_options["url_prefix"] = (
                    state.url_prefix.rstrip("/") + "/" + bp_url_prefix.lstrip("/")

tutaj bez sensu sprawdzane czy bp_url_prefix jest ustawione, w paru miejscach pewnie mozna by to usprawnic. Bywalo gorzej 
