from typing import Set, FrozenSet
from masurare_performanta import timp_si_memorie  # decorator ca sa ne spuna cat timp si cata memorie a folosit
from functools import lru_cache                # ca sa tinem minte rezultatele la sub-formule deja rezolvate

@timp_si_memorie
def dpll(clauze: Set[FrozenSet[int]]) -> bool:
    """
    Algoritmul DPLL:
    - face propagare unitati (când o clauză are un singur literal)
    - gaseste literali puri (cele care apar doar cu semn fix)
    - apoi, daca mai e nevoie, incearca un literal pe rand si face backtracking
    """

    @lru_cache(maxsize=None)
    def rec(clz_fs: FrozenSet[FrozenSet[int]]) -> bool:
        # Transformam frozenset in set ca sa putem modifica usor
        clz = set(clz_fs)

        # Daca nu mai avem nicio clauza, totul e satisfacut - returnam True
        if not clz:
            return True

        # Daca exista vreo clauza goala, am ajuns intr-o contradictie - returnam False
        if any(len(c) == 0 for c in clz):
            return False

        # Cautam clauze unitare (exact un literal)
        for c in clz:
            if len(c) == 1:
                l = next(iter(c))  # literalul din clauza unitară
                # eliminam clauzele care contin l (sunt rezolvate)
                # si scoatem -l din rest
                new_clz = frozenset(
                    c2 - {-l}
                    for c2 in clz
                    if l not in c2
                )
                return rec(new_clz)  # reluam cu formula redusa

        # Cautam literali puri (apare l, dar nu apare -l)
        lit = {l for c in clz for l in c}
        for l in lit:
            if -l not in lit:
                # eliminam toate clauzele in care apare l
                new_clz = frozenset(c for c in clz if l not in c)
                return rec(new_clz)  # reluam dupa eliminare

        # Daca niciun pas simplu nu a rezolvat tot,
        # alegem un literal oricare
        lit = next(iter(next(iter(clz))))

        # Incercam mai intai sa-l punem adevarat
        true_clz = frozenset(
            c2 - {-lit}
            for c2 in clz
            if lit not in c2
        )
        if rec(true_clz):
            return True  # daca reuseste, ne oprim

        # Altfel, incercam varianta opusa (literalul = False)
        false_clz = frozenset(
            c2 - {lit}
            for c2 in clz
            if -lit not in c2
        )
        return rec(false_clz)

    # Apelul initial, convertim lista de clauze pentru cache
    return rec(frozenset(clauze))
