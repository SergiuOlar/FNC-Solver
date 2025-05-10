from typing import Set, FrozenSet
from masurare_performanta import timp_si_memorie  # decorator care masoara timpul si memoria

@timp_si_memorie
def dp(clauze: Set[FrozenSet[int]]) -> bool:
    # Transformam intrarea intr-un set mutabil de clauze
    clz: Set[FrozenSet[int]] = set(clauze)

    # Repetam pana cand formula e complet simplificata sau gasim o clauza goala
    while True:
        # Daca nu mai avem clauze, inseamna ca toti literalii pot fi satisfacuti
        if not clz:
            return True

        # Daca exista vreo clauza goala (0 literali), inseamna ca e contradictie
        if any(len(c) == 0 for c in clz):
            return False

        # Propagare unitati: gasim clauza cu un singur literal
        unit = next(
            (next(iter(c)) for c in clz if len(c) == 1),
            None
        )
        if unit is not None:
            # Eliminam toate clauzele in care apare literalul adevarat
            # si din rest scoatem literalul opus
            clz = {
                frozenset(c2 - {-unit})
                for c2 in clz
                if unit not in c2
            }
            continue  # reluam cu formula redusa

        # Eliminarea literalilor puri: literali care apar doar cu semnul lor
        lit = {l for c in clz for l in c}
        pur = next((l for l in lit if -l not in lit), None)
        if pur is not None:
            # Scoatem toate clauzele in care apare acest literal pur
            clz = {c for c in clz if pur not in c}
            continue  # reluam cu formula redusa

        # Nu mai putem simplifica direct, aplicam pasul de rezolutie
        #    alegem un literal oricare din prima clauza
        lit = next(iter(next(iter(clz))))
        var = abs(lit)

        # Impartim clauzele in cele care contin lit si cele care contin -lit
        poz = [c for c in clz if lit in c]
        neg = [c for c in clz if -lit in c]

        # Generam toti rezolventi dintre cele doua grupe
        temp_rez = {
            frozenset((c1 - {lit}) | (c2 - {-lit}))
            for c1 in poz for c2 in neg
        }
        # Filtram rezolventi care sunt contradictori intern (lit si -lit)
        rezolventi = {r for r in temp_rez if not any(-l in r for l in r)}

        # Clauzele care nu implica variabila curenta raman
        rest = {
            c for c in clz
            if var not in {abs(x) for x in c}
        }

        # Noua formula e unirea dintre clauzele ramase si rezolventi calcultati
        clz = rest | rezolventi
        # reluam din nou procesul pe formula redusa
