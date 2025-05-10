import time                                    # Pentru cronometrare globala
import os                                      # Pentru verificarea existentei fisierelor
import re                                      # Pentru procesarea liniilor de clauze
import logging                                 # Pentru nivelul de logare
import multiprocessing                         # Pentru rularea cu timeout in proces separat
from multiprocessing import TimeoutError       # Exceptie in cazul timeout-ului
import tarfile                                 # Pentru arhive tar.gz
from typing import Set, FrozenSet, Callable, Dict

from fnc import dimacs_text, dimacs_file       # Functi pentru citirea formulelor FNC
from rezolutie import rezolutie                # Implementarea rezolutiei
from dp import dp                              # Implementarea algoritmului DP
from dpll import dpll                          # Implementarea algoritmului DPLL
from masurare_performanta import logger

# Timeout implicit pentru fiecare solver (in secunde)
DEFAULT_TIMEOUT = 1000

# Mapare nume solver -> functia corespondenta
SOLVERS: Dict[str, Callable[[Set[FrozenSet[int]]], bool]] = {
    'Rezolutie': rezolutie,
    'DP':         dp,
    'DPLL':       dpll
}


def run_solver(
    nume: str,
    fn: Callable[[Set[FrozenSet[int]]], bool],
    clauze: Set[FrozenSet[int]],
    rezultate_file=None,
    timeout: float = DEFAULT_TIMEOUT
) -> (float, float):
    """
    Ruleaza un solver cu timeout:
     - afiseaza o linie cu rezultatul pe ecran
     - daca `rezultate_file` este dat, scrie aceeasi linie si in fisier
     - returneaza tuple(durata, memorie_peak) sau (None, None) daca s-a atins timeout
    """
    # Creaza un pool cu un singur worker
    with multiprocessing.Pool(1) as pool:
        async_res = pool.apply_async(fn, (clauze,))
        try:
            sat, dur, peak, curr = async_res.get(timeout=timeout)
            linie = f"{nume:<10} | {'YES' if sat else 'NO ':<3} | {dur:<7.4f}s | {peak:<8.1f}KiB"
            result = (dur, peak)
        except TimeoutError:
            linie = f"{nume:<10} | TIMED OUT after {timeout}s"
            result = (None, None)

    # Afiseaza pe consola
    print(linie)
    # Daca avem fisier de iesire, scrie si acolo
    if rezultate_file:
        rezultate_file.write(linie + "\n")
    return result


def _run_batch(
    formulas: Dict[str, Set[FrozenSet[int]]],
    solvers_to_run: Set[str],
    out
) -> (Dict[str,float], Dict[str,float], Dict[str,int], float):
    """
    Ruleaza solvers_to_run pe fiecare formula din `formulas`,
    afiseaza live si scrie in fisierul `out`.
    Returneaza:
      - time_tot  : dict cu timpul total pe fiecare solver
      - mem_tot   : dict cu memoria totala pe fiecare solver
      - counts    : dict cu numarul de rulări pe fiecare solver
      - elapsed_all : durata totala a operatiunii batch
    """
    start_all = time.time()
    # Initializam acumulatoarele
    time_tot   = {n: 0.0 for n in solvers_to_run}
    mem_tot    = {n: 0.0 for n in solvers_to_run}
    counts     = {n: 0   for n in solvers_to_run}

    # Pentru fiecare formula in batch
    for idx, (fname, clauses) in enumerate(formulas.items(), start=1):
        header = f"\n=== Exercitiul {idx}/{len(formulas)}: {fname} ==="
        print(header);    out.write(header + "\n")

        title = "Solver     | SAT | Time(s)  | Peak KiB"
        print(title);     out.write(title + "\n"); out.write("-"*len(title)+"\n")

        # Ruleaza fiecare solver selectat
        for solver_name in solvers_to_run:
            fn = SOLVERS[solver_name]
            dur, peak = run_solver(solver_name, fn, clauses, rezultate_file=out)
            if dur is not None:
                time_tot[solver_name] += dur
                mem_tot[solver_name]  += peak
                counts[solver_name]   += 1

        print(); out.write("\n")

    elapsed_all = time.time() - start_all
    return time_tot, mem_tot, counts, elapsed_all


def process_file(
    input_path: str,
    output_path: str,
    solvers_to_run: Set[str]
):
    """
    Proceseaza un fisier DIMACS in modul batch:
     1. Citeste formulele cu dimacs_file
     2. Ruleaza _run_batch pentru toate formulele
     3. Scrie rezultatele si statisticile generale in `output_path`
    """
    formulas = dimacs_file(input_path)
    with open(output_path, 'w', encoding='utf-8') as out:
        time_tot, mem_tot, counts, elapsed_all = _run_batch(formulas, solvers_to_run, out)

        # Scrie statistici generale
        out.write("=== Statistici generale ===\n")
        print("=== Statistici generale ===")
        for solver_name in solvers_to_run:
            if counts[solver_name]:
                avg = time_tot[solver_name] / counts[solver_name]
                line = f"  {solver_name:<8}: {avg:.4f}s pe {counts[solver_name]} formule"
            else:
                line = f"  {solver_name:<8}: nicio executie valida"
            print(line); out.write(line + "\n")

        total_time = sum(time_tot.values())
        total_mem  = sum(mem_tot.values())
        elapsed_min = elapsed_all / 60.0
        footer = (
            f"\nTimp total combinat solvers: {total_time:.4f}s\n"
            f"Memorie totala combinata:     {total_mem:.1f}KiB\n"
            f"Timp de executie TOTAL:       {elapsed_all:.4f}s ({elapsed_min:.4f} min)\n"
        )
        print(footer); out.write(footer)

    print(f"\n>> Rezultatele au fost scrise in '{output_path}' <<")


def process_tar_archive(
    archive_path: str,
    solvers_to_run: Set[str],
    output_path: str
):
    """
    Proceseaza o arhiva .tar.gz:
     - extrage toate fisierele .cnf/.dimacs
     - pentru fiecare fisier si fiecare formula, apeleaza _run_batch
     - la final, scrie si afiseaza statisticile pe intreaga arhiva
    """
    if not os.path.isfile(archive_path):
        print(f"Eroare: '{archive_path}' nu exista.")
        return

    try:
        tar = tarfile.open(archive_path, 'r:gz')
    except Exception as e:
        print(f"Nu am putut deschide arhiva: {e}")
        return

    members = [m for m in tar.getmembers()
               if m.isfile() and m.name.endswith(('.cnf', '.dimacs'))]
    if not members:
        print("Nu am gasit fisiere .cnf/.dimacs in arhiva.")
        tar.close()
        return

    # Deschidem fisierul de iesire
    with open(output_path, 'w', encoding='utf-8') as out:
        # Avertisment daca s-a ales Rezolutie (poate fi ineficient)
        if 'Rezolutie' in solvers_to_run:
            warn = "(!) Ai ales Rezolutie pe arhiva – poate fi ineficient."
            print(warn); out.write(warn + "\n\n")

        # Acumulatoare globale pentru intreaga arhiva
        global_time  = {n: 0.0 for n in solvers_to_run}
        global_mem   = {n: 0.0 for n in solvers_to_run}
        global_count = {n: 0   for n in solvers_to_run}
        archive_start = time.time()

        # Pentru fiecare fisier din arhiva
        for member in members:
            header = f"\n=== Fisier in arhiva: {member.name} ==="
            print(header); out.write(header + "\n")

            f = tar.extractfile(member)
            if not f:
                continue
            text = f.read().decode('utf-8')
            formulas = dimacs_text(text)

            # Ruleaza batch intern si primeste statistici locale
            time_tot, mem_tot, counts, _ = _run_batch(formulas, solvers_to_run, out)

            # Aduna in statistica globala
            for solver in solvers_to_run:
                global_time[solver]  += time_tot.get(solver, 0.0)
                global_mem [solver]  += mem_tot.get(solver, 0.0)
                global_count[solver] += counts.get(solver, 0)

        # Dupa procesarea tuturor fisierelor, afiseaza statisticile globale
        archive_elapsed = time.time() - archive_start
        archive_min     = archive_elapsed / 60.0

        footer_header = "=== Statistici pe intreaga arhiva ==="
        print(footer_header); out.write(footer_header + "\n")

        # Timp mediu pe solver
        for solver in solvers_to_run:
            cnt = global_count[solver]
            if cnt:
                avg = global_time[solver] / cnt
                line = f"  {solver:<10}: timp mediu {avg:.4f}s pe {cnt} formule"
            else:
                line = f"  {solver:<10}: nicio executie valida"
            print(line); out.write(line + "\n")

        # Total combinate
        total_time = sum(global_time.values())
        total_mem  = sum(global_mem.values())
        footer = (
            f"\nTimp total combinat:       {total_time:.4f}s\n"
            f"Memorie totala combinata:   {total_mem:.1f}KiB\n"
            f"Timp executie arhiva:       {archive_elapsed:.4f}s ({archive_min:.4f} min)\n"
        )
        print(footer); out.write(footer)

    tar.close()
    print(f"\n>> Rezultatele au fost scrise in '{output_path}' <<")


def read_from_keyboard() -> Set[FrozenSet[int]]:
    """
    Citeste clauze FNC de la tastatura, linie cu linie:
     - linie: literali separati prin spatiu, terminati cu 0
     - linie goala opreste citirea
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
     1) Fisier DIMACS
     2) Tastatura
     3) Arhiva .tar.gz
     4) Iesire
    """
    while True:
        print()
        print("1) Fișier DIMACS  – input din (.cnf/.dimacs/.txt), afisare in timp real pe ecran + scriere în fișier")
        print("2) Tastatură      – input manual, afișaj doar pe ecran")
        print("3) Arhivă .tar.gz – input batch din arhivă, afisare in timp real pe ecran + scriere în fișier")
        print("4) Ieșire         – termină programul")
        c = input("Opțiune (1-4): ").strip()
        if c in ('1','2','3','4'):
            return c


def choose_solvers() -> Set[str]:
    """
    Afiseaza meniul solver-elor disponibile:
     1) Rezolutie
     2) DP
     3) DPLL
     4) Toate
    """
    print("\n1) Rezolutie   2) DP   3) DPLL   4) Toate")
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
        if mode == '4':
            print("La revedere!")
            break
        if mode == '3':
            print("\n(!) Pentru procesarea arhivelor mari, se recomanda sa folositi DPLL, pentru eficienta mai buna.")

        solvers = choose_solvers()
        if not solvers:
            print("Niciun solver ales, reincearca.")
            continue

        if mode == '1':
            inp = input("Cale fisier intrare (.cnf/.dimacs/.txt): ").strip()
            out = input("Cale fisier iesire (.txt):               ").strip()
            if not os.path.isfile(inp):
                print(f"Eroare: '{inp}' nu exista.")
                continue
            process_file(inp, out, solvers)

        elif mode == '3':
            arch = input("Cale arhiva (.tar.gz):        ").strip()
            out  = input("Cale fisier iesire (.txt)):   ").strip()
            process_tar_archive(arch, solvers, out)

        else:  # mode == '2'
            clauze = read_from_keyboard()
            title = "Solver     | SAT | Time(s)  | Peak KiB"
            print("\n" + title)
            print("-"*len(title))
            for solver_name in solvers:
                run_solver(solver_name, SOLVERS[solver_name], clauze)

        print()


if __name__ == '__main__':
    interactive_menu()
