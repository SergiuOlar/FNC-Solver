from typing import Set, FrozenSet
from masurare_performanta import timp_si_memorie
from itertools import combinations

@timp_si_memorie
def rezolutie(clauze: Set[FrozenSet[int]]) -> bool:
    """
    Algoritmul complet de rezolutie pentru SAT pe formule CNF:
    - Returneaza False imediat ce deriva clauza vida (indica UNSAT).
    - Daca nu mai pot fi generate rezolventi noi, inseamna ca formula e SAT.
    """

    # Pornim cu setul initial de clauze
    clauze_set: Set[FrozenSet[int]] = set(clauze)
    new_clauze: Set[FrozenSet[int]] = set()  # aici vom pune clauzele pe care le derivam

    # Repetam pana cand nu mai apar clauze noi
    while True:
        # Pentru fiecare pereche de clauze distincte
        for c1, c2 in combinations(clauze_set, 2):
            # Cautam un literal care sa fie complementar
            for lit in c1:
                if -lit in c2:
                    # Construim rezolventul: eliminam lit din c1 si -lit din c2
                    rezolvent = (set(c1) - {lit}) | (set(c2) - {-lit})

                    # Verificam daca a iesit o tautologie (lit si -lit in aceeasi clauza)
                    if any(l in rezolvent and -l in rezolvent for l in rezolvent):
                        continue  # aruncam tautologia

                    rezolvent_fs = frozenset(rezolvent)

                    # Daca am obtinut clauza vida - UNSAT
                    if not rezolvent_fs:
                        return False

                    # Daca deja exista, nu o adaugam iar
                    if rezolvent_fs in clauze_set or rezolvent_fs in new_clauze:
                        continue

                    # Daca in setul curent exista deja o clauza care contine toate literalele din rezolvent,
                    # atunci rezolventul nu adauga nicio informatie noua si poate fi ignorat.
                    if any(exist <= rezolvent_fs for exist in clauze_set):
                        continue

                    # Altfel, adaugam rezolventul in colectia de clauze noi
                    new_clauze.add(rezolvent_fs)

        # Daca nu s-au generat rezolventi noi, formula este SAT
        if not new_clauze:
            return True

        # Altfel, adaugam toate clauzele noi in set si reluam bucla
        clauze_set |= new_clauze
        new_clauze.clear()
