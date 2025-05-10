from typing import Dict, Set, FrozenSet, Optional
import re
import os
import io

def _proceseaza_dimacs_linii(linii) -> Dict[str, Set[FrozenSet[int]]]:
    """
    Proceseaza un iterator de lini în format DIMACS
    - Liniile care incep cu 'c formula:' definesc inceputul unei noi formule
    - Orice alta linie care incepe cu 'c' este comentariu si se sare
    - 'p cnf …' marcheaza doar sectiunea de clauze
    - Clauzele sunt lini de literali intregi, terminate cu 0.
    """
    formule: Dict[Optional[str], Set[FrozenSet[int]]] = {}
    curent: Optional[str] = None

    for linie_bruta in linii:
        linie = linie_bruta.strip()
        if not linie:
            continue  # separam blocurile printr-o linie goala

        # daca intalnim '%' sau linia '0', incheiem analiza
        if linie.startswith('%') or linie == '0':
            break

        # comentariu special pentru inceputul unei formule
        if linie.startswith('c formula:'):
            curent = linie.split(':', 1)[1].strip()
            formule[curent] = set()
            continue

        # orice alta linie care incepe cu 'c' - comentariu, se sare
        if linie.startswith('c'):
            continue

        # linia de profil DIMACS
        if linie.startswith('p cnf'):
            if curent is None:
                nume_generic = os.path.basename("<batch>")
                formule[nume_generic] = set()
                curent = nume_generic
            continue

        # daca nu avem nicio formula deschisa, initializam una
        if curent is None:
            nume_generic = os.path.basename("<batch>")
            formule[nume_generic] = set()
            curent = nume_generic

        # linie de clauza: literali separati prin spatiu, terminata cu 0
        parti = re.split(r"\s+", linie)
        numere = [int(x) for x in parti if x]
        if not numere or numere[-1] != 0:
            raise ValueError(f"Linie invalida: '{linie}'. Trebuie sa se termine cu 0.")
        literali = frozenset(numere[:-1])
        formule[curent].add(literali)

    return formule

def dimacs_file(cale: str) -> Dict[str, Set[FrozenSet[int]]]:
    """
    Proceseaza un fișier DIMACS
    """
    with open(cale, 'r', encoding='utf-8') as f:
        return _proceseaza_dimacs_linii(f)

def dimacs_text(text: str) -> Dict[str, Set[FrozenSet[int]]]:
    """
    Proceseaza un sir care contine un intreg fisier DIMACS
    """
    return _proceseaza_dimacs_linii(io.StringIO(text))
