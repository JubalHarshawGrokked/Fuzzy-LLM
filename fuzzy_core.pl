% --- fuzzy core ---
fuzzy_and(T1, T2, T) :-
    T is min(T1, T2).

fuzzy_or(T1, T2, T) :-
    T is max(T1, T2).

fuzzy_average(List, T) :-
    sum_list(List, Sum),
    length(List, N),
    N > 0,
    T is Sum / N.

product(A, B, P) :- P is A * B.

weighted_average(Values, Weights, T) :-
    maplist(product, Values, Weights, Products),
    sum_list(Products, Sum),
    sum_list(Weights, WSum),
    WSum > 0,
    T is Sum / WSum.
