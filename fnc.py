from typing import Dict, Set, FrozenSet, Optional
import re
import os

def dimacs(path: str) -> Dict[str, Set[FrozenSet[int]]]:
    """
    Citeste un fisier DIMACS FNC care poate contine una sau mai multe formule.
    - Liniile care incep cu 'c formula:' definesc inceputul unei noi formule, cu numele dupa ':'.
    - Daca nu exista astfel de comentarii, tot fisierul e considerat o singura formula,
      denumita dupa numele fisierului.
    - Liniile de profil 'p cnf num_vars num_clauses' se ignora, ele doar marcheaza
      inceputul unei sectiuni de clauze.
    - Fiecare linie de clauza este o lista de literali (intregi), terminata cu 0.
    Returneaza un dict:
       { nume_formula: set(frozenset(literali)) }
    """
    formula: Dict[str, Set[FrozenSet[int]]] = {}
    curent: Optional[str] = None

    with open(path, 'r') as f:
        for raw in f:
            linie = raw.strip()
            if not linie:
                # linie goala - separator de blocuri
                continue

            # Comentariu special de forma "c formula: nume"
            if linie.startswith('c formula:'):
                curent = linie.split(':', 1)[1].strip()
                formula[curent] = set()
                continue

            # Linia de profil DIMACS
            if linie.startswith('p cnf'):
                # daca nu avem un nume curent, il setam dupa numele fisierului
                if curent is None:
                    nume = os.path.basename(path)
                    formula[nume] = set()
                    curent = nume
                continue

            # Daca nu avem inca o formula curenta, o initializam cu numele fisierului
            if curent is None:
                nume = os.path.basename(path)
                formula[nume] = set()
                curent = nume

            # Procesam linia de clauza: literali separati prin spatiu, terminata cu 0
            parts = re.split(r"\s+", linie)
            nums = [int(x) for x in parts if x]
            if nums[-1] != 0:
                raise ValueError(f"Linie invalida in {path}: '{linie}'. Trebuie sa se termine cu 0.")
            literali = frozenset(nums[:-1])
            formula[curent].add(literali)

    return formula
