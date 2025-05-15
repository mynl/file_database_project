GRAMMAR
=======

clause_list         	::= clause_list clause
                    	 | clause

clause              	::= TOP NUMBER
                    	 | flags
                    	 | regexes
                    	 | SELECT select_list
                    	 | WHERE where_clause_expression
                    	 | ORDER_BY column_sort_list

flags               	::= FLAG flags
                    	 | FLAG

regexes             	::= regexes AND regex
                    	 | regex

regex               	::= COLUMN TILDE REGEX_SLASHED
                    	 | COLUMN TILDE REGEX_UNQUOTED
                    	 | COLUMN TILDE COLUMN
                    	 | BANG REGEX_UNQUOTED
                    	 | BANG COLUMN

select_list         	::= select_list "," select_item
                    	 | select_item

select_item         	::= COLUMN
                    	 | NOT COLUMN
                    	 | STAR

where_clause_expression	::= where_clause_expression AND where_clause
                    	 | where_clause

where_clause        	::= COLUMN EQ_TEST QUOTED_STRING
                    	 | COLUMN EQ_TEST COLUMN
                    	 | COLUMN EQ_TEST DATETIME

column_sort_list    	::= column_sort_list "," column_sort
                    	 | column_sort

column_sort         	::= COLUMN
                    	 | NOT COLUMN



TOKENS
======
        COLUMN, NUMBER, QUOTED_STRING, REGEX_SLASHED, REGEX_UNQUOTED,
        DATETIME, SELECT, ORDER_BY, WHERE, TOP, EQ_TEST, AND,
        FLAG, STAR, NOT, DATETIME, TILDE, BANG

DEFINITIONS
===========
    SELECT = 'select|SELECT'
    ORDER_BY = 'order|ORDER|sort|SORT'
    WHERE = 'where|WHERE'
    TOP = 'top|TOP'
    AND = 'and|AND'    # just AND, otherwise into parens, order of ops etc.
    FLAG = 'recent|RECENT|verbose|VERBOSE|duplicates|DUPLICATES|hardlinks|HARDLINKS'

    STAR = r'\*'
    TILDE = r'~'
    BANG = r'!'
    # to reverse sort order
    NOT = r'\-'
    EQ_TEST = r'==|<=|<|>|>='
    DATETIME complex regex
    NUMBER = r'-?(\d+(\.\d*)?|\.\d+)(%|[eE][+-]?\d+)?|inf|-inf'
    QUOTED_STRING = r'''"([^"\]|\.)*"|'([^'\]|\.)*''''
    COLUMN = r'[a-z_][a-z0-9_]*'
    REGEX_SLASHED = r'/([^/\]|\.)*/'
    REGEX_UNQUOTED = r'[^\s,~/!][^\s,]*'
