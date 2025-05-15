"""Implement command line interface."""

from functools import partial
import os
from pathlib import Path
import socket
import yaml

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.formatted_text import HTML

from greater_tables import GT

from . import DEFAULT_CONFIG_FILE, BASE_DIR
from . manager import ProjectManager


# custom greater-tables formatter
fGT = partial(GT,
              show_index=False,
              large_ok=True,
              formatters={'node': lambda x: str(x)},
              aligners={'suffix': 'center'})


# @click.option('--show-completion', is_flag=True, is_eager=True,
# expose_value=False, callback=lambda ctx, param, value: click.echo(click.shell_
# completion.get_completion_script('fdb')) or ctx.exit() if value else None)
@click.group()
def main():
    """File database CLI."""
    pass


@main.command()
@click.option('-c', '--config', type=click.Path(exists=False, dir_okay=False, path_type=Path), default=DEFAULT_CONFIG_FILE, help='YAML config path')
def index(config: Path):
    """Run the indexer and write Feather file."""
    pm = ProjectManager(config)
    pm.index_files(config)
    click.echo(f"Index update completed.")


@main.command()
@click.argument('config_path', type=click.Path(exists=False, dir_okay=False, writable=True, path_type=Path))
@click.option('-b', '--base', type=click.Path(exists=False, dir_okay=False, path_type=Path), default=DEFAULT_CONFIG_FILE, help='YAML config path')
def create_config(config_path, base):
    """Interactively create a YAML config file for the file database project."""

    # sort the file out
    if config_path.suffix != '.fdb-config':
        config_path = config_path.with_suffix('.fdb-config')
    if base:
        config_path = BASE_DIR / config_path
    click.secho(str(config_path))

    click.secho("=== File Database Config Creator ===", fg='cyan')
    p = Path().home()
    home = str(p)
    config_dir = config_path.parent
    project = click.prompt("Project name", default="File Database Small Test")
    db_default = config_dir / (project.replace(' ', '-') + '.fdb-feather')

    config={
        "project": project,
        "hostname": click.prompt("Hostname", default=socket.gethostname()),
        "database": click.prompt("Database path", default=db_default),
        "included_dirs": [click.prompt("Include dir", default=home)],
        "excluded_dirs": [
            r"\.git$",
            r"^__pycache__$",
            r"\.ipynb_checkpoints$",
            r"\.jupyter_cache$",
        ],
        "excluded_files": [
            r"\.tmp$",
            r"~$",
        ],
        "follow_symlinks": click.confirm("Follow symlinks?", default=False),
        "hash_files": click.confirm("Hash files?", default=True),
        "hash_workers": click.prompt("Number of hash workers", default=6, type=int),
        "last_indexed": 0,
        "timezone": click.prompt("Timezone", default="Europe/London"),
        "tablefmt": click.prompt("Table format", default="mixed_grid"),
    }

    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(config, f, sort_keys=False)

    click.secho(f"\nConfig written to {config_path}", fg="green")


@ main.command()
@ click.option('-c', '--config', type=click.Path(exists=False, dir_okay=False, path_type=Path), default=DEFAULT_CONFIG_FILE, help='YAML config path')
@ click.option('-t', '--tablefmt', default='', show_default=True, help='Markdown table format (see tabulate docs); default uses config file value.')
def query_repl(config: Path, tablefmt: str):
    """Interactive REPL to run multiple queries on the file index with fuzzy completion."""
    pm=ProjectManager(config)
    print(pm)
    if tablefmt == '':
        tablefmt=pm.tablefmt
    click.echo(f"Loaded {len(pm.database):,} rows from {pm.project}")
    click.echo(
        "Enter pandas query expressions (type 'exit', 'x', 'quit' or 'q' to stop and ? for help).\n")

    keywords=['cls', 'and', 'or'] + list(pm.database.columns)
    word_completer=FuzzyCompleter(WordCompleter(keywords, sentence=True))
    session=PromptSession(completer=word_completer)
    result=None

    while True:
        try:
            expr=session.prompt(HTML('<ansiyellow>>> </ansiyellow>')).strip()
            pipe=False
            if expr.lower() in {"exit", "x", "quit", "q"}:
                break
            elif expr == "?":
                click.echo(pm.query_help())
                click.echo(repl_help())
                continue
            elif expr == 'cls':
                # clear screen
                os.system('cls')
                continue
            elif expr.find(">") >= 0:
                # contains a pipe
                expr, pipe=expr.split('>')
                pipe=pipe.strip()
            elif expr.startswith('o'):
                # open files
                if result is None:
                    print('No existing query! Run query first')
                    continue
                # open file mode, start with o n
                try:
                    expr=int(expr[1:].strip())
                except ValueError:
                    print('Wrong syntax for open, expect o index number')
                try:
                    fname=result.loc[expr, 'path']
                    os.startfile(fname)
                except KeyError:
                    print(f'Key {expr} not found.')
                except FileNotFoundError:
                    print("File does not exist.")
                except OSError as e:
                    print(f"No association or error launching: {e}")
                continue

            # if here, run query work
            result, unrestricted_len=pm.query(expr)
            click.echo(_df_to_str(result, tablefmt=tablefmt))
            click.echo(
                f'{unrestricted_len:,d} unrestricted results, {len(result)} shown.')
            if pipe:
                click.echo(
                    f'Found pipe clause {pipe = } TODO: deal with this!')
        except Exception as e:
            click.echo(f"[Error] {e}")




def _df_to_str(df, tablefmt):
    """Nice prepped df as string for printing."""
    f=fGT(df)
    df=f.df
    dfa=[i[4:] for i in f.df_aligners]
    colw={c: 15 for c in df.columns}
    for c in ['dir', 'path', 'hash']:
        if c in df:
            colw[c]=min(40, df[c].str.len().max())
    for c in ['name']:
        if c in df:
            colw[c]=min(60, df[c].str.len().max())
        return df.to_markdown(
            index=False,
            colalign=dfa,
            tablefmt=tablefmt,
            maxcolwidths=[colw.get(i) for i in df.columns])


def repl_help():
    """Help string for repl loop."""
    return """
Repl Help
=========

[select top regex order etc] > output file

* > pipe output NYI.

cls     clear screen
?       show help
x       exit

"""
