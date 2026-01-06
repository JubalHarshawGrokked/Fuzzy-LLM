from pyswip import Prolog

prolog = Prolog()

# Fuzzy facts (truth values as numbers)
prolog.assertz("tall(john, 0.8)")
prolog.assertz("fast(john, 0.7)")

# Fuzzy AND using min t-norm
prolog.assertz("""
    fuzzy_and(T1, T2, T) :-
        T is min(T1, T2)
""")

# Fuzzy rule
prolog.assertz("""
    good_player(X, T) :-
        tall(X, T1),
        fast(X, T2),
        fuzzy_and(T1, T2, T)
""")

# Query
results = list(prolog.query("good_player(john, T)"))

print("Fuzzy Prolog result:")
print(results)
