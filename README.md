# File Database

Fast index and query of local files using `pandas` and `pyarrow`.

Post SPA-epiphany...now built SPA front-end! 

## Features

- Recursively index files in specified directories
- Regex-based exclusion of file and folder patterns
- Optional BLAKE2b hashing for deduplication
- Feather-format output for fast query
- Simple CLI powered by `click`

## Usage

```bash
# Index files
file-db index --config config.yaml

# Query files
file-db query --expr "size > 1e7 and suffix == '.csv'"
```

## Query Language

## Query Examples

recent files, top 10, drop dir column but add create column, files with names
matching regex "q?md$", which means suffix qmd or md.

```sql
verbose recent top 10 select !dir,create ! q?md$
```



## Min config file

included/excluded files must not be empty.

```yaml
project: Samsung 64GB compact flash
hostname: KOLMOGOROV
database: G:/sams64gb.fdb-feather
included_dirs:
- G:/
excluded_dirs: []
excluded_files: []
excluded_files:
hash_files: true
hash_workers: 6
last_indexed: 0
timezone: Europe/London
tablefmt: mixed_grid
```

## To Do

* Util to create a blank config file (maybe with prompts)
* Incremental updates check for deletes and if the file is logged (changed spec), use set and set diff and `df = df[~df["col"].isin(seen)]`
* Create job and python path
* query > file work
* add duplicates and hardlinks key works
* parse queries in order independent manner
* GT should have a repr_text version!
* directory sizes?!
* recent directories (recent changes to dirs)



## Regex look aheads/look backs
