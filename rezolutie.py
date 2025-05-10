from typing import Set, FrozenSet, Dict
from masurare_performanta import timp_si_memorie # decorator care masoara timpul si memoria

@timp_si_memorie
def rezolutie(clauze: Set[FrozenSet[int]]) -> bool:
    """
    Rezolutie optimizata prin set-of-support + index pe literali + grupare pe lungime.
    “suport” (Set-Of-Support) e o multime de clauze proaspat adaugate,
    pe care le combinam cu clauzele deja stabilite (baza) pentru a genera
    doar rezolventi noi. La fiecare pas:
    1. luam fiecare clauza din “suport” si o rezolvam cu clauzele din “baza”
    2. colectam noii rezolventi intr-un set temporar
    3. actualizam “suport” cu acest nou set, iar clauzele vechi din “suport” raman in “baza”
    False la prima clauza vida (UNSAT), altfel True cand nu mai pot aparea clauze noi (SAT).
    """
    # multimea initiala de clauze
    baza: Set[FrozenSet[int]] = set(clauze)

    # grupam clauzele dupa lungime, pentru verificare rapida de redundant
    dupa_lungime: Dict[int, Set[FrozenSet[int]]] = {}
    for cl in baza:
        dupa_lungime.setdefault(len(cl), set()).add(cl)

    # index literal - clauze care contin literalul
    index_lit: Dict[int, Set[FrozenSet[int]]] = {}
    for cl in baza:
        for lit in cl:
            index_lit.setdefault(lit, set()).add(cl)
    obt_lit = index_lit.get  # shortcut pentru acces

    # SOS (set-of-support) porneste cu toate clauzele initiale
    suport: Set[FrozenSet[int]] = set(baza)

    while suport:
        urmator_suport: Set[FrozenSet[int]] = set()

        # pentru fiecare clauza din suport
        for cl1 in suport:
            for lit in cl1:
                # luam doar clauzele din baza care contin literalul opus
                for cl2 in obt_lit(-lit, ()):
                    # construim rezolventul
                    rez = (set(cl1) - {lit}) | (set(cl2) - {-lit})

                    # sarim tautologiile (lit si -lit in aceeasi clauza)
                    valid = True
                    for l in rez:
                        if -l in rez:
                            valid = False
                            break
                    if not valid:
                        continue

                    rez_fs = frozenset(rez)

                    # UNSAT imediat daca clauza vida
                    if not rez_fs:
                        return False

                    # daca deja exista in baza sau in lista urmatoarelor, sarim
                    if rez_fs in baza or rez_fs in urmator_suport:
                        continue

                    # verificare rapida de acoperire:
                    # exista deja o clauza de lungime <= len(rez_fs) care e subset?
                    len_rez = len(rez_fs)
                    redundant = False
                    for lung in range(1, len_rez + 1):
                        for cl_exist in dupa_lungime.get(lung, ()):
                            if cl_exist <= rez_fs:
                                redundant = True
                                break
                        if redundant:
                            break
                    if redundant:
                        continue

                    # clauza noua utila
                    urmator_suport.add(rez_fs)

        # daca nu s-au generat rezolventi noi, formula e SAT
        if not urmator_suport:
            return True

        # adaugam rezolventi noi in baza, index si grupari
        for r in urmator_suport:
            baza.add(r)
            dupa_lungime.setdefault(len(r), set()).add(r)
            for lit in r:
                index_lit.setdefault(lit, set()).add(r)

        # pregatim urmatoarea generatie de procesat
        suport = urmator_suport

    # daca s-a golit suport fara clauza vida, SAT
    return True
