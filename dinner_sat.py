"""
Το πρόβλημα του δείπνου λυμένο με πραγματικό SAT solver (CaDiCaL μέσω PySAT).

Εγκατάσταση:  pip install python-sat
Εκτέλεση:     python dinner_sat.py
"""
import random
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver


def solve_dinner(names, conflicts, seats):
    pool = IDPool()
    # Μία μεταβλητή ΝΑΙ/ΟΧΙ για κάθε καλεσμένο: "έρχεται ο/η ...;"
    x = {n: pool.id(n) for n in names}

    cnf = CNF()

    # Κανόνας 1: κάθε ασύμβατο ζευγάρι -> "ΟΧΙ και οι δύο μαζί"
    # (στη γλώσσα του SAT: όχι-Α Ή όχι-Β)
    for a, b in conflicts:
        cnf.append([-x[a], -x[b]])

    # Κανόνας 2: "τουλάχιστον `seats` καλεσμένοι".
    # Το μετατρέπουμε κι αυτό σε απλούς κανόνες ΝΑΙ/ΟΧΙ
    # (με βοηθητικές μεταβλητές που φτιάχνει μόνο του το PySAT).
    card = CardEnc.atleast(lits=list(x.values()), bound=seats,
                           vpool=pool, encoding=EncType.seqcounter)
    cnf.extend(card.clauses)

    with Solver(name="cadical153", bootstrap_with=cnf.clauses) as s:
        start = time.perf_counter()
        ok = s.solve()
        secs = time.perf_counter() - start
        stats = s.accum_stats()
        guests = [n for n in names if s.get_model()[x[n] - 1] > 0] if ok else None

    return guests, secs, pool.top, len(cnf.clauses), stats


def check(guests, conflicts):
    """Ο γρήγορος έλεγχος: κοιτάμε ένα-ένα τα ασύμβατα ζευγάρια."""
    s = set(guests)
    return not any(a in s and b in s for a, b in conflicts)


# --- 1. Το μικρό μας τραπέζι (8 άτομα, 4 θέσεις) ---------------------------
names = ["Άννα", "Βασίλης", "Γιώργος", "Δήμητρα",
         "Ελένη", "Ζωή", "Θοδωρής", "Ιωάννα"]
E = [(4, 7), (0, 7), (0, 5), (3, 4), (2, 6), (1, 5),
     (1, 2), (2, 7), (1, 4), (2, 3), (1, 3)]
conflicts = [(names[a], names[b]) for a, b in E]

guests, secs, nvars, nclauses, st = solve_dinner(names, conflicts, 4)
print("Μικρό τραπέζι:", guests, "| έλεγχος:", check(guests, conflicts))

# --- 2. Το δείπνο του άρθρου: 400 άτομα, 100 θέσεις ------------------------
random.seed(1)
big = [f"Καλεσμένος {i}" for i in range(400)]
# Τυχαία ασύμβατα ζευγάρια, αλλά φροντίζουμε να υπάρχει λύση:
# κρύβουμε μια "σωστή" εκατοντάδα και δεν βάζουμε συγκρούσεις μέσα της.
hidden = set(random.sample(big, 100))
pairs = set()
while len(pairs) < 2000:
    a, b = random.sample(big, 2)
    if not (a in hidden and b in hidden):
        pairs.add((a, b))
pairs = list(pairs)

guests, secs, nvars, nclauses, st = solve_dinner(big, pairs, 100)
print(f"\n400 άτομα, 100 θέσεις, {len(pairs)} ασύμβατα ζευγάρια")
print(f"  Μεταβλητές: {nvars:,} | κανόνες: {nclauses:,}")
print(f"  Βρέθηκε λύση: {guests is not None} σε {secs:.3f} δευτ.")
print(f"  Υποθέσεις: {st.get('decisions', 0):,} | αδιέξοδα: {st.get('conflicts', 0):,}")
print(f"  Έλεγχος λύσης: {check(guests, pairs)}")
print("  Brute force θα έψαχνε σε ~2.2 × 10^96 λίστες.")
