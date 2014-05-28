% These utilities are used query temporal relations using string integers

str_to_num(String, Number) :-
    ( string(String), var(Number) ->
    string_to_list(String, Codes),
    number_codes(Number, Codes)
    ; var(String), number(Number) ->
    string_to_atom(String, Number)
    ; string(String), number(Number) ->
    string_to_atom(S, Number),
    String = S
    ; abort % report a type error or instantiation fault
    ).

% get_int takes a string integer (ex: 't153') and returns integer (ex: 153)
% Here Y is 't153' and Z is 153.
get_int(Y, Z) :- substring(Y, 2, 5, X), str_to_num(X, Z),!.
get_int(Y, Z) :- substring(Y, 2, 4, X), str_to_num(X, Z),!.
get_int(Y, Z) :- substring(Y, 2, 3, X), str_to_num(X, Z),!.
get_int(Y, Z) :- substring(Y, 2, 2, X), str_to_num(X, Z),!.
get_int(Y, Z) :- substring(Y, 2, 1, X), str_to_num(X, Z).

before(int(_X1,Y1), int(X2,_Y2)) :- 
            get_int(Y1,IY1), 
            get_int(X2,IX2), 
            IY1 < IX2 - 1.

during(int(X1,Y1), int(X2,Y2)) :-
            get_int(X1,IX1),
            get_int(Y1,IY1),
            get_int(X2,IX2),
            get_int(Y2,IY2),
            IX1 > IX2, IY1 < IY2. 

overlaps(int(X1,Y1), int(X2,Y2)) :-
            get_int(X1,IX1),
            get_int(Y1,IY1),
            get_int(X2,IX2),
            get_int(Y2,IY2),
            IX2 > IX1, IX2 < IY1, IY1 < IY2. 

meets(int(_X1,Y1), int(X2,_Y2)) :-
            get_int(Y1,IY1),
            get_int(X2,IX2),
            IX2 =:= IY1 + 1. 

starts(int(X1,_Y1), int(X2,_Y2)) :-
            get_int(X1,IX1),
            get_int(X2,IX2),
            IX1 =:= IX2.

finishes(int(_X1,Y1), int(_X2,Y2)) :-
            get_int(Y1,IY1),
            get_int(Y2,IY2),
            IY1 =:= IY2. 
