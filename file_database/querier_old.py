"""Query file database."""

import re

import pandas as pd


def _quote_bare_dates(expr: str) -> str:
    """
    Add quotes around bare date strings.

    Allows expressions like: mod < 2024-11

    Works for fields: mod, create.
    """
    def replacer(m):
        field, op, val = m.groups()
        return f"{field} {op} \"{val}\""

    pattern = r'\b(mod|create)\s*([<>]=?)\s*(\d{4}-\d{2}(?:-\d{2})?)\b'
    return re.sub(pattern, replacer, expr)


def query_ex(df: pd.DataFrame, expr: str) -> pd.DataFrame:
    """
    Run extended query parser.

    Supports optional 'top N' prefix, regex with '~', and pandas query().
    Also supports 'sort by col1, col2' at the end.

    Query parser: supports

        optional 'top N' prefix,
        regex with '~', and
        pandas query().

    Examples:
    "top 50 name ~ 'report' and suffix == 'csv'"
    "path ~ 'archive/2023' and mod > '2024-01'"
    "top 10 mod > '2024-03-01'"
    ""  # returns all rows

    Do not need quotes around dates?

    Ordering
        verbose: turns on verbose mode to debug how query is parsed
        recent : automatically sort by mod date
        top n  : top n resutls only
        select comma sep list of fields : in addition to the default ones
        regex clauses: separated by and, regex does not need to be quoted
        sql clause: sent directly to df.query, string literals must be quoted
        order|sort by

    OR in place of regex and sql clauses just ! *.py
    (for a regex applied to the name just name ~ regex)

    dates and sql: stunningly, mod.dt.day == 13 works: modified on the 13th!

    an empty string returns all rows.

    Piping output handled by the cli.

    Look aheads: ^(?!.*[ae]+).*' matches names with no a or e...

    Always case insenstive...TODO: !!

    """
    df = df.copy()
    expr = expr.strip()
    # default values
    recent = False
    top_n = None
    regex_filters = []
    non_regex_parts = []
    sort_cols = []
    sort_order = []
    select_cols = []
    drop_cols = []
    base_cols = ['name', 'dir', 'mod', 'size', 'suffix']
    verbose = False
    duplicates_links = False

    # strip verbose prefix, second clause matches JUST verbose
    verbose_match = re.search(
        r'^verbose\s+(.+)|^verbose$', expr, flags=re.IGNORECASE)
    if verbose_match:
        verbose = True
        # verbose = 7 characters at the start
        expr = expr[7:].strip()
    if verbose:
        def lprint(*argv):
            print(*argv)
    else:
        def lprint(*argv):
            pass
    lprint(f'verbose mode\n{expr = }')

    # Check for recent prefix
    recent_match = re.match(r'^recent\b',  # r'^recent\s+(.+)|^recent$',
                            expr, flags=re.IGNORECASE)
    if recent_match:
        recent = True
        # recent = 6 characters at the start
        expr = expr[6:].strip()
    lprint(f'{recent = }')
    lprint(f'{expr = }')

    # Check for 'top N' prefix
    top_match = re.match(r'^top\s+(\d+)\s*', expr, flags=re.IGNORECASE)
    if top_match:
        top_n = int(top_match.group(1))
        expr = expr[top_match.end():].strip()

    lprint(f'{top_n = }')
    lprint(f'{expr = }')

    # check for dups or hardlinks
    hd_match = re.match(r'^(hardlinks|duplicates)\b',
                        expr, flags=re.IGNORECASE)
    if hd_match:
        duplicates_links = hd_match.group(1)
        # recent = 6 characters at the start
        expr = expr[len(duplicates_links):].strip()
    lprint(f'{duplicates_links = }')
    lprint(f'{expr = }')

    # select col list
    select_match = re.match(
        r"^select\s+((!|\-)?[a-zA-Z]+(?:\s*,\s*(!|\-)?[a-zA-Z]+)*)", expr, flags=re.IGNORECASE)
    if select_match:
        fields_str = select_match.group(1)
        select_cols = [f.strip() for f in fields_str.split(',')]
        drop_cols = [i[1:] for i in select_cols if i[0] in ('!', '-')]
        select_cols = [i for i in select_cols if i[0] not in ('!', '-')]
        expr = expr[select_match.end():].lstrip()
    lprint(f'{select_cols = }')
    lprint(f'{drop_cols = }')
    lprint(f'{expr = }')

    # Strip and extract 'sort by ...' suffix
    sort_match = re.search(
        r'\b(?:sort|order)\s+by\s+(.+)$', expr, flags=re.IGNORECASE)
    if sort_match:
        sort_clause = sort_match.group(1)
        sort_cols, sort_order = _parse_sort_fields(sort_clause)
        expr = expr[:sort_match.start()].strip()
    lprint(f'{sort_cols = }\n{sort_order = }')
    lprint(f'{expr = }')
    if sort_cols and recent:
        print('WARNING: sort clause ignored with recent prefix.')

    # see if what's left is ! regex, which is then applied to name
    if expr.startswith("!"):
        expr = expr[1:].strip()
        lprint('glob mode')
        # a glob *.py
        expr = expr.replace('.', '\\.')
        expr = expr.replace('*', '.*')
        regex_filters.append(('name', expr))
    else:
        # Extract regex filters (e.g., name ~ pattern)
        tokens = re.split(r'(?<!~)\band\b', expr)
        for tok in tokens:
            tok = tok.strip()
            if "~" in tok:
                field, pattern = map(str.strip, tok.split("~", 1))
                field = field.strip()
                pattern = pattern.strip().strip("'\"")
                regex_filters.append((field, pattern))
            elif tok:
                non_regex_parts.append(tok)

        # Run query() on remaining logic
        if non_regex_parts:
            query_expr = " and ".join(non_regex_parts)
            query_expr = _quote_bare_dates(query_expr)
            lprint(f'{query_expr = }')
            df = df.query(query_expr)
        else:
            lprint('NO non-regex parts.')

    # Apply regex filters
    lprint(f'{regex_filters = }')
    for field, pattern in regex_filters:
        if field in df.columns:
            df = df[df[field].astype(str).str.contains(
                pattern, regex=True, case=False, na=False)]
        else:
            raise ValueError(f"Unknown field for regex filtering: '{field}'")

    # Sort
    if recent:
        now = pd.Timestamp.now()
        df = df.copy()
        # df.loc[:, 'age'] = (now - df.loc[:, 'mod']).dt.days
        df['age'] = (now - df['mod']).dt.days
        df = df.sort_values(by='mod', ascending=False)
    elif sort_cols:
        df = df.sort_values(by=sort_cols, ascending=sort_order)

    if duplicates_links == 'duplicates':
        lprint('filtering for duplicates')
        df = df[df.duplicated("hash", keep=False)]
    elif duplicates_links == 'hardlinks':
        lprint('filtering for hardlinks')
        df = df[df.duplicated("node", keep=False)]

    # Top N
    unrestricted_len = len(df)
    if top_n is not None:
        df = df.head(top_n)

    # prune fields
    # base cols plus select
    fields = [i for i in df.columns if i in base_cols or i in select_cols]
    # drop out the drop cols
    if drop_cols:
        fields = [i for i in fields if i not in drop_cols]
    if recent:
        fields.insert(0, 'age')
    df = df[fields]

    return df, unrestricted_len


def _parse_sort_fields(spec: str):
    """Parse comma sep list of field names with optional -|! prefix into list and list of ascending."""
    fields = []
    orders = []
    for field in spec.split(','):
        field = field.strip()
        if field.startswith('-'):
            fields.append(field[1:])
            orders.append(False)
        else:
            fields.append(field)
            orders.append(True)
    return fields, orders


def query_help():
    return """
Help on query function
======================

Query syntax
------------
All rows optional. Must be in order shown.
An empty query returns all rows.

verbose
recent
top n
hardlinks | duplicates
select (!|-)field1[, fields]
regex [and regex]
sql
order|sort by [-]field[, fields]

* if recent an age column is added
* hardlinks | duplicates -> find duplicates or linked files (within the project)
* select field, prefix by ! or - to drop a base column, eg select !dir drops (long) directory
* regex not quoted
* sql clause quoted for passing to df.query
* -field is descending order, else ascending.

Query return fields
-------------------
name
dir
mod
size
suffix
...plus selected columns

Database fields
---------------
name
dir
drive
path
mod
create
node
size,
suffix
vol_serial
drive_model
drive_serial
hash

"""
