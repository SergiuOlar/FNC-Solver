import time                                   # Pentru cronometrare globala
import os                                     # Pentru verificarea existentei fisierelor
import re                                     # Pentru parsarea liniilor de clauze
import logging                                # Pentru nivelul de logare
import multiprocessing                        # Pentru rularea cu timeout in proces separat
from multiprocessing import TimeoutError # Exceptie in cazul timeout-ului
from typing import Set, FrozenSet, Callable, Dict

from fnc import dimacs                        # Functie de procesare DIMACS din fisier
from rezolutie import rezolutie               # Implementarea rezolutie
from dp import dp                             # Implementarea DP
from dpll import dpll                         # Implementarea DPLL
from masurare_performanta import logger       # Logger-ul folosit in tot proiectul

# Timeout implicit pentru fiecare solver (in secunde)
DEFAULT_TIMEOUT = 1000

# Mapare nume solver - functia corespunzatoare
SOLVERS: Dict[str, Callable[[Set[FrozenSet[int]]], bool]] = {
    'Rezolutie': rezolutie,
    'DP': dp,
    'DPLL': dpll
}


def run_solver(
    nume: str,
    fn: Callable[[Set[FrozenSet[int]]], bool],
    clauze: Set[FrozenSet[int]],
    rezultate_file=None,
    timeout: float = DEFAULT_TIMEOUT
) -> (float, float):
    """
    Ruleaza un solver intr-un Pool cu un singur worker si cu timeout:
     - afiseaza live rezultatul pe ecran
     - daca exista rezultate_file, scrie aceeasi linie si in fisier
     - returneaza tuple(durata, memorie_peak) sau (None, None) la timeout
    """
    with multiprocessing.Pool(1) as pool:
        async_res = pool.apply_async(fn, (clauze,))
        try:
            # Asteapta pana la `timeout` secunde
            sat, dur, peak, curr = async_res.get(timeout=timeout)
            # Formateaza linia de output
            linie = f"{nume:<10} | {'YES' if sat else 'NO ':<3} | {dur:<7.4f}s | {peak:<8.1f}KiB"
            rezultate = (dur, peak)
        except TimeoutError:
            # In caz de expirare timeout
            linie = f"{nume:<10} | TIMED OUT after {timeout}s"
            rezultate = (None, None)

    # Afiseaza pe consola
    print(linie)
    # Scrie si in fisier, daca este deschis
    if rezultate_file:
        rezultate_file.write(linie + "\n")

    return rezultate


def process_file(
    input_path: str,
    output_path: str,
    solvers_to_run: Set[str]
):
    """
    Proceseaza un fisier DIMACS in modul batch:
     1. Proceseaza toate formulele (pot fi mai multe) cu functia dimacs()
     2. Pentru fiecare formula si pentru fiecare solver selectat:
        - ruleaza solver-ul,
        - aduna timpi si memoria pentru statistici
        - scrie rezultatele in fisier si le afiseaza
     3. La final, calculeaza si afiseaza/scrie:
        - timpi mediu pentru fiecare solver,
        - timpul total combinat,
        - memoria totala combinata,
        - durata totala a executiei batch-ului.
    """
    # Obtinem dictionarul {nume_formula: set de clauze}
    formula = dimacs(input_path)

    # Initializam acumulatoarele pentru timp si memorie
    time_tot   = {n: 0.0 for n in solvers_to_run}
    mem_tot    = {n: 0.0 for n in solvers_to_run}
    count_runs = {n: 0   for n in solvers_to_run}

    # Incepem cronometrarea totala
    start_all = time.time()

    # Deschidem fisierul de output
    with open(output_path, 'w', encoding='utf-8') as out:
        # Iteram fiecare formula din fisierul DIMACS
        for idx, (nume, clauze) in enumerate(formula.items(), start=1):
            # Antet pentru fiecare exercitiu/formula
            header = f"\n=== Exercitiul {idx}/{len(formula)}: {nume} ==="
            print(header)
            out.write(header + "\n")

            # Titlul tabelului de rezultate
            title = "Solver     | SAT | Time(s)  | Peak KiB"
            print(title)
            out.write(title + "\n")
            out.write("-" * len(title) + "\n")

            # Pentru fiecare solver ales
            for solver_name in solvers_to_run:
                fn = SOLVERS[solver_name]
                dur, peak = run_solver(solver_name, fn, clauze, rezultate_file=out)
                if dur is not None:
                    time_tot[solver_name] += dur
                    mem_tot[solver_name]  += peak
                    count_runs[solver_name] += 1

            print()
            out.write("\n")

        # Dupa toate formulele, generam statisticile generale
        summary = "=== Statistici generale ==="
        print(summary)
        out.write(summary + "\n")

        # Timp mediu de rezolvare per solver
        for solver_name in solvers_to_run:
            if count_runs[solver_name]:
                avg = time_tot[solver_name] / count_runs[solver_name]
                line = f"  {solver_name:<8}: {avg:.4f}s pe {count_runs[solver_name]} formule"
            else:
                line = f"  {solver_name:<8}: nicio executie valida"
            print(line)
            out.write(line + "\n")

        # Timp total si memorie totala combinate
        total_time = sum(time_tot.values())
        total_mem  = sum(mem_tot.values())
        end_all    = time.time()
        elapsed_all = end_all - start_all
        elapsed_min = elapsed_all / 60.0

        footer = (
            f"\nTimp total combinat solvers: {total_time:.4f}s\n"
            f"Memorie totala combinata:     {total_mem:.1f}KiB\n"
            f"Timp de executie TOTAL:       {elapsed_all:.4f}s "
            f"({elapsed_min:.4f} min)\n"
        )
        print(footer)
        out.write(footer)


def read_from_keyboard() -> Set[FrozenSet[int]]:
    """
    Citeste clauze FNC de la tastatura, linie cu linie:
     - fiecare linie contine literali separati prin spatiu, terminati cu 0.
     - o linie goala incheie citirea.
    """
    print("\nIntroduceti clauzele (literali separati prin spatiu, terminati cu 0). Linie goala finalizeaza:")
    clauze = set()
    while True:
        linie = input().strip()
        if not linie:
            break
        nums = [int(x) for x in re.split(r"\s+", linie) if x]
        if nums[-1] != 0:
            print("Linia trebuie sa se termine cu 0.")
            continue
        clauze.add(frozenset(nums[:-1]))
    return clauze


def choose_input() -> str:
    """
    Afiseaza meniul principal:
     1) Fisier DIMACS  2) Tastatura  3) Iesire
    Returneaza optiunea selectata.
    """
    while True:
        print("\n1) Fișier DIMACS (citirea din fisier,scrierea in fisier) \n2) Tastatură(citirea de la tastatura,scrierea pe ecran)  \n3) Iesire")
        c = input("Optiune (1-3): ").strip()
        if c in ('1', '2', '3'):
            return c


def choose_solvers() -> Set[str]:
    """
    Afiseaza meniul solver-elor disponibile:
     1) Rezolutie  2) DP  3) DPLL  4) Toate
    Intoarce multimea solver-elor alese.
    """
    print("\n1) Rezolutie  2) DP  3) DPLL  4) Toate")
    c = input("Optiune (1-4): ").strip()
    mapping = {
        '1': {'Rezolutie'},
        '2': {'DP'},
        '3': {'DPLL'},
        '4': set(SOLVERS.keys())
    }
    return mapping.get(c, set())


def interactive_menu():
    """Bucla principala a meniului interactiv."""
    logger.setLevel(logging.WARNING)
    while True:
        mode = choose_input()
        if mode == '3':  # Iesire
            print("La revedere!")
            break

        if mode == '1':
            # Modul batch: citire din fisier si scriere in alt fisier
            inp = input("Cale fisier intrare: ").strip()
            out = input("Cale fisier iesire: ").strip()
            if not os.path.isfile(inp):
                print(f"Eroare: '{inp}' nu exista.")
                continue
            solvers = choose_solvers()
            process_file(inp, out, solvers)

        else:
            # Modul interactiv: solver-e pe o singura formula de la tastatura
            solvers = choose_solvers()
            clauze = read_from_keyboard()

            title = "Solver     | SAT | Time(s)  | Peak KiB"
            print("\n" + title)
            print("-" * len(title))
            for solver_name in solvers:
                fn = SOLVERS[solver_name]
                run_solver(solver_name, fn, clauze)

        print()


if __name__ == '__main__':
    # Pornim meniul la executarea script-ului
    interactive_menu()
