# FNC-Solver

Un mic proiect in Python pentru rezolvarea problemelor SAT în formă CNF, cu trei metode de bază:

- **Rezoluţie completă**  
- **DP (Davis–Putnam)**  
- **DPLL**  

Oferă:
- **Mod interactiv** (citire de la tastatură + live pe ecran)  
- **Mod batch** (citire din fișier .`dimacs` / `.cnf` / `.txt` + scriere rezultate în fișier)  
- **Suport arhive** (`.tar.gz` cu mai multe `.cnf`/`.dimacs`)  
- Monitorizare **timp** și **memorie** pentru fiecare apel

---

## 📁 Structura proiect
FNC-Solver/  
├── main.py # CLI + meniu interactiv & batch  
├── fnc.py # parsare format DIMACS (batch sau text)  
├── rezolutie.py # solver Rezoluţie completă  
├── dp.py # solver Davis–Putnam  
├── dpll.py # solver DPLL  
├── masurare_performanta.py # decorator de măsurare timp și memorie  
├── requirements.txt # (opțional) niciun pachet extern  
└── README.md # (acest fișier)  

---

## 🚀 Cum se rulează

1. Clonează proiectul:  
   -**git clone** https://github.com/SergiuOlar/FNC-Solver.git  
   -**cd FNC-Solver**  
2. Asigura-te ca ai Python 3.+:  
   -**python --version**  
3.Pornește interfața:  
   -**python main.py**  

---

## 🎛️ Meniul principal

La pornire vei vedea:  
  1) Fișier DIMACS      _# input din .cnf/.dimacs/.txt → afișaj + scriere fișier_  
     -**Alege un fișier .cnf, .dimacs sau .txt în format DIMACS FNC.**  
     -**Rezultatele vor fi afișate live și salvate într-un fișier .txt la calea specificată.**  
  3) Tastatură          _# input manual → afișaj doar pe ecran_    
     -**Introdu clauzele linie cu linie: lista de literali (ex: 1 -3 4 0), termină cu 0.**  
     -**O linie goală finalizează input-ul.**  
     -**Se afișează doar pe ecran.**  
  5) Arhivă .tar.gz     _# batch din arhivă → afișaj + scriere fișier_  
     -**Procesează toate fișierele .cnf/.dimacs din arhivă.**  
     -**Afișează live și salvează rezultatele într-un fișier .txt.**  
     -**Vei primi un mesaj de avertisment dacă alegi Rezoluție (ineficient pe loturi mari).**  
  7) Iesire             _# închide programul_  

---

## 🔢 Selectarea solver-elor  

După alegerea modului de input, vei selecta solver-ul:  
  **1) Rezoluție   2) DP   3) DPLL   4) Toate**  

---

## 📄 Format DIMACS FNC  

  -c formula: NumeInstanta      # (opțional) etichetează o formulă  
  -p cnf <numVar> <numClauze>   # header (ignorăm cifrele)  
  -<lit1> <lit2> … <litk> 0     # fiecare clauză, încheiată cu 0  
  -…                            # mai multe clauze  

  Comentariile c … sunt ignorate (doar c formula: desemnează nume)  
  Orice altă linie care începe cu c este sărită.  
  Linia p cnf <nr_var> <nr_cla> doar marchează secțiunea de clauze.  
  Fiecare clauză listează literali (pozitiv/negativ) și se termină cu 0.  

  **Exemplu**  
  
  c formula: ex1  
  p cnf 4 3  
  1 -3 4 0  
  -1 2 3 0  
  2 -4 0  
  

---

## 📚 Referințe & lectură suplimentară

1. **Davis, M. & Putnam, H.** (1960). *A Computing Procedure for Quantification Theory*. Journal of the ACM, 7(3), 201–215.  
2. **Davis, M., Logemann, G. & Loveland, D.** (1962). *A Machine Program for Theorem‐Proving*. Communications of the ACM, 5(7), 394–397.  
3. **Cook, S. A.** (1971). *The Complexity of Theorem‐Proving Procedures*. Proceedings of the 3rd Annual ACM Symposium on Theory of Computing (STOC ’71), 151–158.  
4. **Biere, A., Heule, M., van Maaren, H. & Walsh, T.** (eds.) (2009). *Handbook of Satisfiability*. IOS Press.  
5. **DIMACS CNF Challenge** – instrucțiuni și formate:  
   https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/  
6. **SAT Competition** – competiții anuale de SAT solvers:  
   http://satcompetition.org/  




   
