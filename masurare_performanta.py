import time
import tracemalloc
from functools import wraps
import logging

# creeaza un logger dedicat pentru acest modul, folosind numele modulului curent
logger = logging.getLogger(__name__)

def timp_si_memorie(fn):
    """
    Decorator care:
    1. Porneste monitorizarea memoriei inainte de apelul functiei
    2. Masoara timpul de executie
    3. La final, opreste monitorizarea si returneaza
       - rezultatul functiei (sat/unsat)
       - durata in secunde
       - varful de memorie folosit (in KiB)
       - memoria curenta alocata (in bytes)
    """
    @wraps(fn)
    def wrapper(clause):
        # Incepem sa urmarim alocarile de memorie
        tracemalloc.start()

        # Retinem momentul de start
        t0 = time.perf_counter()

        # Apelam functia originala (de ex. dpll, dp sau resolution)
        sat = fn(clause)

        # Calculam cat a durat efectiv
        dur = time.perf_counter() - t0

        # Luam statistici de memorie:
        #    curr = memoria curenta alocata acum,
        #    peak = varful de memorie atins in timpul executiei
        curr, peak = tracemalloc.get_traced_memory()

        # Oprim monitorizarea memoriei
        tracemalloc.stop()

        # Returnam toate informatiile utile:
        #    - sat: boolean (True/False)
        #    - dur: timp in secunde
        #    - peak/1024: varf de memorie in KiB
        #    - curr: memoria curenta in bytes
        return sat, dur, peak / 1024, curr

    return wrapper