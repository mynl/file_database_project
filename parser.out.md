Grammar:

Rule 0     S' -> query
Rule 1     query -> clause_list
Rule 2     clause_list -> clause
Rule 3     clause_list -> clause_list clause
Rule 4     clause -> ORDER_BY column_sort_list
Rule 5     clause -> WHERE where_clause_expression
Rule 6     clause -> SELECT select_list
Rule 7     clause -> regexes
Rule 8     clause -> flags
Rule 9     clause -> TOP NUMBER
Rule 10    flags -> FLAG
Rule 11    flags -> FLAG flags
Rule 12    regexes -> regex
Rule 13    regexes -> regexes AND regex
Rule 14    regex -> COLUMN TILDE COLUMN
Rule 15    regex -> COLUMN TILDE REGEX_UNQUOTED
Rule 16    regex -> COLUMN TILDE REGEX_SLASHED
Rule 17    select_list -> select_item
Rule 18    select_list -> select_list , select_item
Rule 19    select_item -> STAR
Rule 20    select_item -> NOT COLUMN
Rule 21    select_item -> COLUMN
Rule 22    where_clause_expression -> where_clause
Rule 23    where_clause_expression -> where_clause_expression AND where_clause
Rule 24    where_clause -> COLUMN EQ_TEST DATETIME
Rule 25    where_clause -> COLUMN EQ_TEST COLUMN
Rule 26    where_clause -> COLUMN EQ_TEST QUOTED_STRING
Rule 27    column_sort_list -> column_sort
Rule 28    column_sort_list -> column_sort_list , column_sort
Rule 29    column_sort -> NOT COLUMN
Rule 30    column_sort -> COLUMN

Terminals, with rules where they appear:

,                    : 18 28
AND                  : 13 23
COLUMN               : 14 14 15 16 20 21 24 25 25 26 29 30
DATETIME             : 24
EQ_TEST              : 24 25 26
FLAG                 : 10 11
NOT                  : 20 29
NUMBER               : 9
ORDER_BY             : 4
QUOTED_STRING        : 26
REGEX_SLASHED        : 16
REGEX_UNQUOTED       : 15
SELECT               : 6
STAR                 : 19
TILDE                : 14 15 16
TOP                  : 9
WHERE                : 5
error                : 

Nonterminals, with rules where they appear:

clause               : 2 3
clause_list          : 1 3
column_sort          : 27 28
column_sort_list     : 4 28
flags                : 8 11
query                : 0
regex                : 12 13
regexes              : 7 13
select_item          : 17 18
select_list          : 6 18
where_clause         : 22 23
where_clause_expression : 5 23


state 0

    (0) S' -> . query
    (1) query -> . clause_list
    (2) clause_list -> . clause
    (3) clause_list -> . clause_list clause
    (4) clause -> . ORDER_BY column_sort_list
    (5) clause -> . WHERE where_clause_expression
    (6) clause -> . SELECT select_list
    (7) clause -> . regexes
    (8) clause -> . flags
    (9) clause -> . TOP NUMBER
    (12) regexes -> . regex
    (13) regexes -> . regexes AND regex
    (10) flags -> . FLAG
    (11) flags -> . FLAG flags
    (14) regex -> . COLUMN TILDE COLUMN
    (15) regex -> . COLUMN TILDE REGEX_UNQUOTED
    (16) regex -> . COLUMN TILDE REGEX_SLASHED
    ORDER_BY        shift and go to state 4
    WHERE           shift and go to state 5
    SELECT          shift and go to state 6
    TOP             shift and go to state 9
    FLAG            shift and go to state 11
    COLUMN          shift and go to state 12

    query                          shift and go to state 1
    clause_list                    shift and go to state 2
    clause                         shift and go to state 3
    regexes                        shift and go to state 7
    flags                          shift and go to state 8
    regex                          shift and go to state 10

state 1

    (0) S' -> query .


state 2

    (1) query -> clause_list .
    (3) clause_list -> clause_list . clause
    (4) clause -> . ORDER_BY column_sort_list
    (5) clause -> . WHERE where_clause_expression
    (6) clause -> . SELECT select_list
    (7) clause -> . regexes
    (8) clause -> . flags
    (9) clause -> . TOP NUMBER
    (12) regexes -> . regex
    (13) regexes -> . regexes AND regex
    (10) flags -> . FLAG
    (11) flags -> . FLAG flags
    (14) regex -> . COLUMN TILDE COLUMN
    (15) regex -> . COLUMN TILDE REGEX_UNQUOTED
    (16) regex -> . COLUMN TILDE REGEX_SLASHED
    $end            reduce using rule 1 (query -> clause_list .)
    ORDER_BY        shift and go to state 4
    WHERE           shift and go to state 5
    SELECT          shift and go to state 6
    TOP             shift and go to state 9
    FLAG            shift and go to state 11
    COLUMN          shift and go to state 12

    clause                         shift and go to state 13
    regexes                        shift and go to state 7
    flags                          shift and go to state 8
    regex                          shift and go to state 10

state 3

    (2) clause_list -> clause .
    ORDER_BY        reduce using rule 2 (clause_list -> clause .)
    WHERE           reduce using rule 2 (clause_list -> clause .)
    SELECT          reduce using rule 2 (clause_list -> clause .)
    TOP             reduce using rule 2 (clause_list -> clause .)
    FLAG            reduce using rule 2 (clause_list -> clause .)
    COLUMN          reduce using rule 2 (clause_list -> clause .)
    $end            reduce using rule 2 (clause_list -> clause .)


state 4

    (4) clause -> ORDER_BY . column_sort_list
    (27) column_sort_list -> . column_sort
    (28) column_sort_list -> . column_sort_list , column_sort
    (29) column_sort -> . NOT COLUMN
    (30) column_sort -> . COLUMN
    NOT             shift and go to state 16
    COLUMN          shift and go to state 17

    column_sort_list               shift and go to state 14
    column_sort                    shift and go to state 15

state 5

    (5) clause -> WHERE . where_clause_expression
    (22) where_clause_expression -> . where_clause
    (23) where_clause_expression -> . where_clause_expression AND where_clause
    (24) where_clause -> . COLUMN EQ_TEST DATETIME
    (25) where_clause -> . COLUMN EQ_TEST COLUMN
    (26) where_clause -> . COLUMN EQ_TEST QUOTED_STRING
    COLUMN          shift and go to state 20

    where_clause_expression        shift and go to state 18
    where_clause                   shift and go to state 19

state 6

    (6) clause -> SELECT . select_list
    (17) select_list -> . select_item
    (18) select_list -> . select_list , select_item
    (19) select_item -> . STAR
    (20) select_item -> . NOT COLUMN
    (21) select_item -> . COLUMN
    STAR            shift and go to state 23
    NOT             shift and go to state 24
    COLUMN          shift and go to state 25

    select_list                    shift and go to state 21
    select_item                    shift and go to state 22

state 7

    (7) clause -> regexes .
    (13) regexes -> regexes . AND regex
    ORDER_BY        reduce using rule 7 (clause -> regexes .)
    WHERE           reduce using rule 7 (clause -> regexes .)
    SELECT          reduce using rule 7 (clause -> regexes .)
    TOP             reduce using rule 7 (clause -> regexes .)
    FLAG            reduce using rule 7 (clause -> regexes .)
    COLUMN          reduce using rule 7 (clause -> regexes .)
    $end            reduce using rule 7 (clause -> regexes .)
    AND             shift and go to state 26


state 8

    (8) clause -> flags .
    ORDER_BY        reduce using rule 8 (clause -> flags .)
    WHERE           reduce using rule 8 (clause -> flags .)
    SELECT          reduce using rule 8 (clause -> flags .)
    TOP             reduce using rule 8 (clause -> flags .)
    FLAG            reduce using rule 8 (clause -> flags .)
    COLUMN          reduce using rule 8 (clause -> flags .)
    $end            reduce using rule 8 (clause -> flags .)


state 9

    (9) clause -> TOP . NUMBER
    NUMBER          shift and go to state 27


state 10

    (12) regexes -> regex .
    AND             reduce using rule 12 (regexes -> regex .)
    ORDER_BY        reduce using rule 12 (regexes -> regex .)
    WHERE           reduce using rule 12 (regexes -> regex .)
    SELECT          reduce using rule 12 (regexes -> regex .)
    TOP             reduce using rule 12 (regexes -> regex .)
    FLAG            reduce using rule 12 (regexes -> regex .)
    COLUMN          reduce using rule 12 (regexes -> regex .)
    $end            reduce using rule 12 (regexes -> regex .)


state 11

    (10) flags -> FLAG .
    (11) flags -> FLAG . flags
    (10) flags -> . FLAG
    (11) flags -> . FLAG flags
  ! shift/reduce conflict for FLAG resolved as shift
    ORDER_BY        reduce using rule 10 (flags -> FLAG .)
    WHERE           reduce using rule 10 (flags -> FLAG .)
    SELECT          reduce using rule 10 (flags -> FLAG .)
    TOP             reduce using rule 10 (flags -> FLAG .)
    COLUMN          reduce using rule 10 (flags -> FLAG .)
    $end            reduce using rule 10 (flags -> FLAG .)
    FLAG            shift and go to state 11

    flags                          shift and go to state 28

state 12

    (14) regex -> COLUMN . TILDE COLUMN
    (15) regex -> COLUMN . TILDE REGEX_UNQUOTED
    (16) regex -> COLUMN . TILDE REGEX_SLASHED
    TILDE           shift and go to state 29


state 13

    (3) clause_list -> clause_list clause .
    ORDER_BY        reduce using rule 3 (clause_list -> clause_list clause .)
    WHERE           reduce using rule 3 (clause_list -> clause_list clause .)
    SELECT          reduce using rule 3 (clause_list -> clause_list clause .)
    TOP             reduce using rule 3 (clause_list -> clause_list clause .)
    FLAG            reduce using rule 3 (clause_list -> clause_list clause .)
    COLUMN          reduce using rule 3 (clause_list -> clause_list clause .)
    $end            reduce using rule 3 (clause_list -> clause_list clause .)


state 14

    (4) clause -> ORDER_BY column_sort_list .
    (28) column_sort_list -> column_sort_list . , column_sort
    ORDER_BY        reduce using rule 4 (clause -> ORDER_BY column_sort_list .)
    WHERE           reduce using rule 4 (clause -> ORDER_BY column_sort_list .)
    SELECT          reduce using rule 4 (clause -> ORDER_BY column_sort_list .)
    TOP             reduce using rule 4 (clause -> ORDER_BY column_sort_list .)
    FLAG            reduce using rule 4 (clause -> ORDER_BY column_sort_list .)
    COLUMN          reduce using rule 4 (clause -> ORDER_BY column_sort_list .)
    $end            reduce using rule 4 (clause -> ORDER_BY column_sort_list .)
    ,               shift and go to state 30


state 15

    (27) column_sort_list -> column_sort .
    ,               reduce using rule 27 (column_sort_list -> column_sort .)
    ORDER_BY        reduce using rule 27 (column_sort_list -> column_sort .)
    WHERE           reduce using rule 27 (column_sort_list -> column_sort .)
    SELECT          reduce using rule 27 (column_sort_list -> column_sort .)
    TOP             reduce using rule 27 (column_sort_list -> column_sort .)
    FLAG            reduce using rule 27 (column_sort_list -> column_sort .)
    COLUMN          reduce using rule 27 (column_sort_list -> column_sort .)
    $end            reduce using rule 27 (column_sort_list -> column_sort .)


state 16

    (29) column_sort -> NOT . COLUMN
    COLUMN          shift and go to state 31


state 17

    (30) column_sort -> COLUMN .
    ,               reduce using rule 30 (column_sort -> COLUMN .)
    ORDER_BY        reduce using rule 30 (column_sort -> COLUMN .)
    WHERE           reduce using rule 30 (column_sort -> COLUMN .)
    SELECT          reduce using rule 30 (column_sort -> COLUMN .)
    TOP             reduce using rule 30 (column_sort -> COLUMN .)
    FLAG            reduce using rule 30 (column_sort -> COLUMN .)
    COLUMN          reduce using rule 30 (column_sort -> COLUMN .)
    $end            reduce using rule 30 (column_sort -> COLUMN .)


state 18

    (5) clause -> WHERE where_clause_expression .
    (23) where_clause_expression -> where_clause_expression . AND where_clause
    ORDER_BY        reduce using rule 5 (clause -> WHERE where_clause_expression .)
    WHERE           reduce using rule 5 (clause -> WHERE where_clause_expression .)
    SELECT          reduce using rule 5 (clause -> WHERE where_clause_expression .)
    TOP             reduce using rule 5 (clause -> WHERE where_clause_expression .)
    FLAG            reduce using rule 5 (clause -> WHERE where_clause_expression .)
    COLUMN          reduce using rule 5 (clause -> WHERE where_clause_expression .)
    $end            reduce using rule 5 (clause -> WHERE where_clause_expression .)
    AND             shift and go to state 32


state 19

    (22) where_clause_expression -> where_clause .
    AND             reduce using rule 22 (where_clause_expression -> where_clause .)
    ORDER_BY        reduce using rule 22 (where_clause_expression -> where_clause .)
    WHERE           reduce using rule 22 (where_clause_expression -> where_clause .)
    SELECT          reduce using rule 22 (where_clause_expression -> where_clause .)
    TOP             reduce using rule 22 (where_clause_expression -> where_clause .)
    FLAG            reduce using rule 22 (where_clause_expression -> where_clause .)
    COLUMN          reduce using rule 22 (where_clause_expression -> where_clause .)
    $end            reduce using rule 22 (where_clause_expression -> where_clause .)


state 20

    (24) where_clause -> COLUMN . EQ_TEST DATETIME
    (25) where_clause -> COLUMN . EQ_TEST COLUMN
    (26) where_clause -> COLUMN . EQ_TEST QUOTED_STRING
    EQ_TEST         shift and go to state 33


state 21

    (6) clause -> SELECT select_list .
    (18) select_list -> select_list . , select_item
    ORDER_BY        reduce using rule 6 (clause -> SELECT select_list .)
    WHERE           reduce using rule 6 (clause -> SELECT select_list .)
    SELECT          reduce using rule 6 (clause -> SELECT select_list .)
    TOP             reduce using rule 6 (clause -> SELECT select_list .)
    FLAG            reduce using rule 6 (clause -> SELECT select_list .)
    COLUMN          reduce using rule 6 (clause -> SELECT select_list .)
    $end            reduce using rule 6 (clause -> SELECT select_list .)
    ,               shift and go to state 34


state 22

    (17) select_list -> select_item .
    ,               reduce using rule 17 (select_list -> select_item .)
    ORDER_BY        reduce using rule 17 (select_list -> select_item .)
    WHERE           reduce using rule 17 (select_list -> select_item .)
    SELECT          reduce using rule 17 (select_list -> select_item .)
    TOP             reduce using rule 17 (select_list -> select_item .)
    FLAG            reduce using rule 17 (select_list -> select_item .)
    COLUMN          reduce using rule 17 (select_list -> select_item .)
    $end            reduce using rule 17 (select_list -> select_item .)


state 23

    (19) select_item -> STAR .
    ,               reduce using rule 19 (select_item -> STAR .)
    ORDER_BY        reduce using rule 19 (select_item -> STAR .)
    WHERE           reduce using rule 19 (select_item -> STAR .)
    SELECT          reduce using rule 19 (select_item -> STAR .)
    TOP             reduce using rule 19 (select_item -> STAR .)
    FLAG            reduce using rule 19 (select_item -> STAR .)
    COLUMN          reduce using rule 19 (select_item -> STAR .)
    $end            reduce using rule 19 (select_item -> STAR .)


state 24

    (20) select_item -> NOT . COLUMN
    COLUMN          shift and go to state 35


state 25

    (21) select_item -> COLUMN .
    ,               reduce using rule 21 (select_item -> COLUMN .)
    ORDER_BY        reduce using rule 21 (select_item -> COLUMN .)
    WHERE           reduce using rule 21 (select_item -> COLUMN .)
    SELECT          reduce using rule 21 (select_item -> COLUMN .)
    TOP             reduce using rule 21 (select_item -> COLUMN .)
    FLAG            reduce using rule 21 (select_item -> COLUMN .)
    COLUMN          reduce using rule 21 (select_item -> COLUMN .)
    $end            reduce using rule 21 (select_item -> COLUMN .)


state 26

    (13) regexes -> regexes AND . regex
    (14) regex -> . COLUMN TILDE COLUMN
    (15) regex -> . COLUMN TILDE REGEX_UNQUOTED
    (16) regex -> . COLUMN TILDE REGEX_SLASHED
    COLUMN          shift and go to state 12

    regex                          shift and go to state 36

state 27

    (9) clause -> TOP NUMBER .
    ORDER_BY        reduce using rule 9 (clause -> TOP NUMBER .)
    WHERE           reduce using rule 9 (clause -> TOP NUMBER .)
    SELECT          reduce using rule 9 (clause -> TOP NUMBER .)
    TOP             reduce using rule 9 (clause -> TOP NUMBER .)
    FLAG            reduce using rule 9 (clause -> TOP NUMBER .)
    COLUMN          reduce using rule 9 (clause -> TOP NUMBER .)
    $end            reduce using rule 9 (clause -> TOP NUMBER .)


state 28

    (11) flags -> FLAG flags .
    ORDER_BY        reduce using rule 11 (flags -> FLAG flags .)
    WHERE           reduce using rule 11 (flags -> FLAG flags .)
    SELECT          reduce using rule 11 (flags -> FLAG flags .)
    TOP             reduce using rule 11 (flags -> FLAG flags .)
    FLAG            reduce using rule 11 (flags -> FLAG flags .)
    COLUMN          reduce using rule 11 (flags -> FLAG flags .)
    $end            reduce using rule 11 (flags -> FLAG flags .)


state 29

    (14) regex -> COLUMN TILDE . COLUMN
    (15) regex -> COLUMN TILDE . REGEX_UNQUOTED
    (16) regex -> COLUMN TILDE . REGEX_SLASHED
    COLUMN          shift and go to state 37
    REGEX_UNQUOTED  shift and go to state 38
    REGEX_SLASHED   shift and go to state 39


state 30

    (28) column_sort_list -> column_sort_list , . column_sort
    (29) column_sort -> . NOT COLUMN
    (30) column_sort -> . COLUMN
    NOT             shift and go to state 16
    COLUMN          shift and go to state 17

    column_sort                    shift and go to state 40

state 31

    (29) column_sort -> NOT COLUMN .
    ,               reduce using rule 29 (column_sort -> NOT COLUMN .)
    ORDER_BY        reduce using rule 29 (column_sort -> NOT COLUMN .)
    WHERE           reduce using rule 29 (column_sort -> NOT COLUMN .)
    SELECT          reduce using rule 29 (column_sort -> NOT COLUMN .)
    TOP             reduce using rule 29 (column_sort -> NOT COLUMN .)
    FLAG            reduce using rule 29 (column_sort -> NOT COLUMN .)
    COLUMN          reduce using rule 29 (column_sort -> NOT COLUMN .)
    $end            reduce using rule 29 (column_sort -> NOT COLUMN .)


state 32

    (23) where_clause_expression -> where_clause_expression AND . where_clause
    (24) where_clause -> . COLUMN EQ_TEST DATETIME
    (25) where_clause -> . COLUMN EQ_TEST COLUMN
    (26) where_clause -> . COLUMN EQ_TEST QUOTED_STRING
    COLUMN          shift and go to state 20

    where_clause                   shift and go to state 41

state 33

    (24) where_clause -> COLUMN EQ_TEST . DATETIME
    (25) where_clause -> COLUMN EQ_TEST . COLUMN
    (26) where_clause -> COLUMN EQ_TEST . QUOTED_STRING
    DATETIME        shift and go to state 43
    COLUMN          shift and go to state 42
    QUOTED_STRING   shift and go to state 44


state 34

    (18) select_list -> select_list , . select_item
    (19) select_item -> . STAR
    (20) select_item -> . NOT COLUMN
    (21) select_item -> . COLUMN
    STAR            shift and go to state 23
    NOT             shift and go to state 24
    COLUMN          shift and go to state 25

    select_item                    shift and go to state 45

state 35

    (20) select_item -> NOT COLUMN .
    ,               reduce using rule 20 (select_item -> NOT COLUMN .)
    ORDER_BY        reduce using rule 20 (select_item -> NOT COLUMN .)
    WHERE           reduce using rule 20 (select_item -> NOT COLUMN .)
    SELECT          reduce using rule 20 (select_item -> NOT COLUMN .)
    TOP             reduce using rule 20 (select_item -> NOT COLUMN .)
    FLAG            reduce using rule 20 (select_item -> NOT COLUMN .)
    COLUMN          reduce using rule 20 (select_item -> NOT COLUMN .)
    $end            reduce using rule 20 (select_item -> NOT COLUMN .)


state 36

    (13) regexes -> regexes AND regex .
    AND             reduce using rule 13 (regexes -> regexes AND regex .)
    ORDER_BY        reduce using rule 13 (regexes -> regexes AND regex .)
    WHERE           reduce using rule 13 (regexes -> regexes AND regex .)
    SELECT          reduce using rule 13 (regexes -> regexes AND regex .)
    TOP             reduce using rule 13 (regexes -> regexes AND regex .)
    FLAG            reduce using rule 13 (regexes -> regexes AND regex .)
    COLUMN          reduce using rule 13 (regexes -> regexes AND regex .)
    $end            reduce using rule 13 (regexes -> regexes AND regex .)


state 37

    (14) regex -> COLUMN TILDE COLUMN .
    AND             reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)
    ORDER_BY        reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)
    WHERE           reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)
    SELECT          reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)
    TOP             reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)
    FLAG            reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)
    COLUMN          reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)
    $end            reduce using rule 14 (regex -> COLUMN TILDE COLUMN .)


state 38

    (15) regex -> COLUMN TILDE REGEX_UNQUOTED .
    AND             reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)
    ORDER_BY        reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)
    WHERE           reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)
    SELECT          reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)
    TOP             reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)
    FLAG            reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)
    COLUMN          reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)
    $end            reduce using rule 15 (regex -> COLUMN TILDE REGEX_UNQUOTED .)


state 39

    (16) regex -> COLUMN TILDE REGEX_SLASHED .
    AND             reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)
    ORDER_BY        reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)
    WHERE           reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)
    SELECT          reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)
    TOP             reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)
    FLAG            reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)
    COLUMN          reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)
    $end            reduce using rule 16 (regex -> COLUMN TILDE REGEX_SLASHED .)


state 40

    (28) column_sort_list -> column_sort_list , column_sort .
    ,               reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)
    ORDER_BY        reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)
    WHERE           reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)
    SELECT          reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)
    TOP             reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)
    FLAG            reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)
    COLUMN          reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)
    $end            reduce using rule 28 (column_sort_list -> column_sort_list , column_sort .)


state 41

    (23) where_clause_expression -> where_clause_expression AND where_clause .
    AND             reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)
    ORDER_BY        reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)
    WHERE           reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)
    SELECT          reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)
    TOP             reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)
    FLAG            reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)
    COLUMN          reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)
    $end            reduce using rule 23 (where_clause_expression -> where_clause_expression AND where_clause .)


state 42

    (25) where_clause -> COLUMN EQ_TEST COLUMN .
    AND             reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)
    ORDER_BY        reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)
    WHERE           reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)
    SELECT          reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)
    TOP             reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)
    FLAG            reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)
    COLUMN          reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)
    $end            reduce using rule 25 (where_clause -> COLUMN EQ_TEST COLUMN .)


state 43

    (24) where_clause -> COLUMN EQ_TEST DATETIME .
    AND             reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)
    ORDER_BY        reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)
    WHERE           reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)
    SELECT          reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)
    TOP             reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)
    FLAG            reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)
    COLUMN          reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)
    $end            reduce using rule 24 (where_clause -> COLUMN EQ_TEST DATETIME .)


state 44

    (26) where_clause -> COLUMN EQ_TEST QUOTED_STRING .
    AND             reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)
    ORDER_BY        reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)
    WHERE           reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)
    SELECT          reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)
    TOP             reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)
    FLAG            reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)
    COLUMN          reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)
    $end            reduce using rule 26 (where_clause -> COLUMN EQ_TEST QUOTED_STRING .)


state 45

    (18) select_list -> select_list , select_item .
    ,               reduce using rule 18 (select_list -> select_list , select_item .)
    ORDER_BY        reduce using rule 18 (select_list -> select_list , select_item .)
    WHERE           reduce using rule 18 (select_list -> select_list , select_item .)
    SELECT          reduce using rule 18 (select_list -> select_list , select_item .)
    TOP             reduce using rule 18 (select_list -> select_list , select_item .)
    FLAG            reduce using rule 18 (select_list -> select_list , select_item .)
    COLUMN          reduce using rule 18 (select_list -> select_list , select_item .)
    $end            reduce using rule 18 (select_list -> select_list , select_item .)


Conflicts:

shift/reduce conflict for FLAG in state 11 resolved as shift