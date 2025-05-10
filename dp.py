from typing import Set, FrozenSet
from masurare_performanta import timp_si_memorie  # decorator care masoara timpul si memoria

def alege_variabila(clauze: Set[FrozenSet[int]]) -> int:
    """
    Pentru fiecare variabila v, calculam de cate ori apare v si -v.
    Returneaza variabila cu frecventa totala maxima.
    """
    frecvente = {}
    for cl in clauze:
        for lit in cl:
            frecvente[lit] = frecvente.get(lit, 0) + 1
    # agregam pe variabila (abs)
    scor = {}
    for lit, cnt in frecvente.items():
        var = abs(lit)
        scor[var] = scor.get(var, 0) + cnt
    # alegem variabila cu scor maxim
    return max(scor, key=lambda v: scor[v])


@timp_si_memorie
def dp(clauze_initiale: Set[FrozenSet[int]]) -> bool:
    # pornim cu o copie mutabila a clauzelor
    clauze_mod = set(clauze_initiale)

    # cazuri triviale
    if not clauze_mod:
        return True
    if any(len(c) == 0 for c in clauze_mod):
        return False

    # continuam pana nu mai raman clauze de procesat
    while clauze_mod:
        # verificam din nou pentru clauza goala
        if any(len(c) == 0 for c in clauze_mod):
            return False

        # propagarea unitati: gasim clauza cu un singur literal
        unit = next((next(iter(c)) for c in clauze_mod if len(c) == 1), None)
        if unit is not None:
            # eliminam clauzele care contin literalul adevarat
            # si scoatem literalul opus din restul
            clauze_mod = {
                frozenset(c2 - {-unit})
                for c2 in clauze_mod
                if unit not in c2
            }
            continue

        # eliminarea literalului pur: literali care apar doar cu un semn
        literali = {l for c in clauze_mod for l in c}
        pur = next((l for l in literali if -l not in literali), None)
        if pur is not None:
            # scoatem toate clauzele in care apare literalul pur
            clauze_mod = {c for c in clauze_mod if pur not in c}
            continue

        # alegem o variabila in functie de frecventa
        variabila = alege_variabila(clauze_mod)

        # impartim clauzele dupa prezenta variabilei
        pozitive  = [c for c in clauze_mod if  variabila in c]
        negative  = [c for c in clauze_mod if -variabila in c]

        # generam rezolventii pentru variabila
        rezolventi = set()
        for c1 in pozitive:
            for c2 in negative:
                r = (set(c1) - { variabila }) | (set(c2) - {-variabila})
                # sarim rezolventii tautologici
                if any(l in r and -l in r for l in r):
                    continue
                rezolventi.add(frozenset(r))

        # pastram clauzele care nu mentioneaza variabila deloc
        rest = {c for c in clauze_mod if variabila not in {abs(l) for l in c}}

        # construim noul set de clauze
        clauze_nou = rest | rezolventi

        # eliminare clauze inutile:
        # scoatem clauzele care contin toti literali altei clauze
        clauze_reduse = set(clauze_nou)
        for c1 in clauze_nou:
            for c2 in clauze_nou:
                if c1 is not c2 and c1.issubset(c2):
                    clauze_reduse.discard(c2)

        clauze_mod = clauze_reduse

        # daca nu mai avem clauze, e satisfiabila
        if not clauze_mod:
            return True

    # daca iesim din bucla, nu avem contraditie - SAT
    return True
