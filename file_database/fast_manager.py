# manager.py
"""Manage config file and index database creation and updating."""

import os
import re
import socket
import subprocess
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, Optional, Sequence, Tuple

import pandas as pd
import yaml

from . import BASE_DIR
from .disk_info import DriveInfo
from .hasher import hash_many

logger = logging.getLogger(__name__)


# ---------- fast path helpers ----------

def _compile_ignores(patterns: Sequence[str]) -> List[re.Pattern]:
    """Compile case-insensitive regex patterns once."""
    return [re.compile(p, flags=re.IGNORECASE) for p in patterns or []]


def _name_matches_any(name: str, regexes: Sequence[re.Pattern]) -> bool:
    """Return True if any compiled regex matches name."""
    for r in regexes:
        if r.search(name):
            return True
    return False


def iter_files_fast(
    roots: Iterable[Path],
    re_excluded_dirs: Sequence[re.Pattern],
    re_excluded_files: Sequence[re.Pattern],
    follow_symlinks: bool,
    on_excluded: Optional[Callable[[str, str], None]] = None,
) -> Iterator[Tuple[Path, str, Path]]:
    """
    Fast, non-recursive directory crawl using os.scandir.

    Yields (file_path, drive_letter, base_root) for files/symlinks that pass filters.
    Uses an explicit stack to avoid recursion overhead.
    """
    stack: List[Tuple[Path, str, Path]] = []
    for r in roots:
        try:
            if r.is_dir():
                stack.append((r, r.resolve().drive.upper(), r))
        except OSError:
            # root unreadable
            continue

    while stack:
        dir_path, drive_letter, base_root = stack.pop()
        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    name = entry.name

                    # directory handling
                    try:
                        if entry.is_dir(follow_symlinks=follow_symlinks):
                            if _name_matches_any(name, re_excluded_dirs):
                                if on_excluded:
                                    on_excluded("dir", name)
                                continue
                            stack.append(
                                (Path(entry.path), drive_letter, base_root))
                            continue
                    except OSError:
                        # permission or broken link
                        continue

                    # file / symlink handling
                    try:
                        is_file_like = (
                            entry.is_file(follow_symlinks=follow_symlinks)
                            or entry.is_symlink()
                        )
                    except OSError:
                        continue
                    if not is_file_like:
                        if on_excluded:
                            on_excluded("non-file", name)
                        continue
                    if _name_matches_any(name, re_excluded_files):
                        if on_excluded:
                            on_excluded("file", name)
                        continue

                    yield Path(entry.path), drive_letter, base_root
        except (OSError, FileNotFoundError):
            # directory disappeared or unreadable; skip
            continue


def _stat_row(
    p: Path,
    drive_letter: str,
    base_root: Path,
    last_indexed_ns: int,
    follow_symlinks: bool,
    vol_tuple: Optional[Tuple[str, str, str]] = None,
) -> Optional[dict]:
    """Stat a single file and build row dict. Returns None if unchanged or on error."""
    try:
        st = p.stat(follow_symlinks=follow_symlinks)
    except OSError:
        return None

    if st.st_mtime_ns < last_indexed_ns:
        return None

    vol_serial, drive_model, drive_serial = ("", "", "")
    if vol_tuple is not None:
        vol_serial, drive_model, drive_serial = vol_tuple

    # Compute relative parent once, omitting the included root (your prior behavior)
    try:
        parent_rel = str(p.parent.relative_to(base_root))
    except Exception:
        parent_rel = str(p.parent)

    suffix = p.suffix[1:] if p.suffix.startswith(".") else p.suffix

    return {
        "name": p.name,
        "dir": parent_rel,          # relative to top-level included root
        "drive": drive_letter,      # e.g., 'C:'
        "path": str(p),
        "mod": st.st_mtime_ns,
        "create": st.st_ctime_ns,
        "access": st.st_atime_ns,
        "node": st.st_ino,
        "links": st.st_nlink,
        "size": st.st_size,
        "suffix": suffix,
        "vol_serial": vol_serial,
        "drive_model": drive_model,
        "drive_serial": drive_serial,
    }


def build_rows_threaded(
    items: Sequence[Tuple[Path, str, Path]],
    last_indexed_ns: int,
    follow_symlinks: bool,
    drive_info_lookup: Optional[dict[str, Tuple[str, str, str]]] = None,
    max_workers: Optional[int] = None,
) -> list[dict]:
    """
    Thread the stat/build step. os.stat releases the GIL on Windows, so this scales.
    drive_info_lookup: optional map { 'C:': (vol_serial, model, serial), ... }
    """
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = []
        for p, drive_letter, base_root in items:
            vol_tuple = None
            if drive_info_lookup is not None:
                vol_tuple = drive_info_lookup.get(drive_letter, None)
            futs.append(
                ex.submit(
                    _stat_row,
                    p,
                    drive_letter,
                    base_root,
                    last_indexed_ns,
                    follow_symlinks,
                    vol_tuple,
                )
            )
        for f in as_completed(futs):
            row = f.result()
            if row is not None:
                rows.append(row)
    return rows


# ---------- your class (unchanged API) ----------

class FastProjectManager:
    """Manage single project config yaml (fdb-config) file."""

    def __init__(self, config_path: Path):
        """
        Load YAML config from file.

        The fdb-config suffix optional and added if missing.
        If not found in current directory, looks in local (eg. for default config).
        """
        self.config_path = Path(config_path)
        if self.config_path.suffix != ".fdb-config":
            self.config_path = self.config_path.with_suffix(".fdb-config")

        if not self.config_path.exists():
            self.config_path = BASE_DIR / self.config_path.name
        logger.info("Opening %s", self.config_path)

        with self.config_path.open() as f:
            self._config = yaml.safe_load(f)
            self.hostname = socket.gethostname()
            if self.hostname.lower() != self._config["hostname"].lower():
                # bugfix: cfg -> self._config
                logger.warning(
                    "WARNING: Host name %s of machine does not match config file %s.",
                    self.hostname,
                    self._config["hostname"],
                )
        self._database = pd.DataFrame([])
        self._config_df = None
        self.last_excluded_list = None
        self._re_excluded_dirs = None
        self._re_excluded_files = None
        logger.info("object %s created.", self)

    def __getattr__(self, name):
        """Provide access to config yaml dictionary."""
        if name in self._config:
            return self._config[name]
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}")

    def __getitem__(self, name):
        """Access to values of config dictionary."""
        return self._config[name]

    def __repr__(self):
        """Create simple string representation."""
        return f"PM({self.config_path.name})"

    @property
    def config(self):
        """Return the config yaml dictionary."""
        return self._config

    @property
    def config_df(self):
        if self._config_df is None:
            self._config_df = pd.Series(self.config).to_frame("value")
            self._config_df.index.name = "key"
        return self._config_df

    def set_attributes(self, **kwargs):
        """Set new attributes of config yaml dictionary."""
        for k, v in kwargs.items():
            self._config[k] = v

    def hardlinks(self, keep=False) -> pd.DataFrame:
        """Return rows that share the same inode (i.e., hard links)."""
        df = self.database
        return df[df.duplicated("node", keep=keep)].sort_values("node")

    def duplicates(self, keep=False) -> pd.DataFrame:
        """
        Return rows that share the same hash (i.e., duplicate content).

        keep = 'first', 'last', False: keep first, last or all duplicates
        """
        df = self.database
        return df[df.duplicated("hash", keep=keep)].sort_values("hash")

    def save(self):
        """Save dictionary to yaml and persist DB."""
        backup = self.config_path.with_suffix(".fdb-config-bak")
        if backup.exists():
            backup.unlink()
        backup.hardlink_to(self.config_path)
        self.config_path.unlink()
        with self.config_path.open("w") as f:
            yaml.safe_dump(
                self._config,
                f,
                sort_keys=False,          # preserve input order
                default_flow_style=False,  # block structure
                width=100,
                indent=2,
            )
        self.database.to_feather(self.database_path)

    @property
    def database_path(self):
        """Get the database path name from config file."""
        return Path(self._config["database"])

    @property
    def database(self):
        """Return the database, loading from feather once."""
        if self._database.empty:
            if self.database_path.exists():
                self._database = pd.read_feather(self.database_path)
        return self._database

    def reset(self):
        """Reset config, as though it has never been created."""
        self._config["last_indexed"] = 0
        self._config["last_included_dirs"] = []
        self._config["last_excluded_dirs"] = []
        self._config["last_excluded_files"] = []
        self._config["last_new_files"] = 0

    def schedule(self, execute=False):
        """Set up the task schedule for the project."""
        schedule_time = self.config.get("schedule_time", "")
        if schedule_time == "":
            print("Scheduling not defined in config file. Exiting.")
        schedule_frequency = self.schedule_frequency
        task_name = f"file-db-task {self.project}"
        cmd = [
            "schtasks",
            "/Create",
            "/TN",
            task_name,
            "/TR",
            f'file-db index -c "{str(self.config_path)}"',
            "/SC",
            schedule_frequency,
            "/ST",
            schedule_time,
            "/F",  # force update if exists
        ]

        if execute:
            print("Executing:\n\n", " ".join(cmd))
            subprocess.run(cmd, check=True)
        else:
            print("Would execute\n\n", " ".join(cmd))

    # ---------- new fast indexer ----------
    def index(self, mode: str | None = "update", verbose: bool = False) -> None:
        """Incrementally scan and index files according to config (fast version)."""
        # light logger
        lprint = print if verbose else (lambda *a, **k: None)

        start = time.time()
        cpu_start = time.process_time()
        start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if mode == "update":
            existing_df = self.database
            print(f"Updating index with {len(existing_df):,} entries")
        else:
            self.reset()
            existing_df = pd.DataFrame([])
            print("Creating all new index")

        # compile filters once
        re_dirs = _compile_ignores(self.excluded_dirs)
        re_files = _compile_ignores(self.excluded_files)

        # collect drive info for included drives only (once)
        drive_info_lookup: dict[str, Tuple[str, str, str]] = {}
        if getattr(self, "include_drive_info", True):
            di = DriveInfo()
            drive_letters = set()
            roots: list[Path] = []
            for root_str in self.included_dirs:
                p = Path(root_str)
                if p.is_dir():
                    roots.append(p)
                    try:
                        drive_letters.add(p.resolve().drive.upper())
                    except OSError:
                        pass
            for dl in drive_letters:
                try:
                    vol_serial, model, serial = di.drive_letter_id(dl)
                    drive_info_lookup[dl] = (
                        str(vol_serial), str(model), str(serial))
                except Exception:
                    drive_info_lookup[dl] = ("", "", "")
        else:
            roots = [Path(r) for r in self.included_dirs if Path(r).is_dir()]

        # keep excluded details (for checking)
        self.last_excluded_list = []

        def _track_excluded(reason: str, name: str) -> None:
            self.last_excluded_list.append([reason, name])

        # enumerate candidates quickly
        roots = [Path(r) for r in self.included_dirs if Path(r).is_dir()]
        items = list(
            iter_files_fast(
                roots=roots,
                re_excluded_dirs=re_dirs,
                re_excluded_files=re_files,
                follow_symlinks=self.follow_symlinks,
                on_excluded=_track_excluded,
            )
        )

        # threaded stat/build
        rows = build_rows_threaded(
            items=items,
            last_indexed_ns=self.last_indexed,
            follow_symlinks=self.follow_symlinks,
            drive_info_lookup=drive_info_lookup or None,
            max_workers=getattr(self, "stat_workers", os.cpu_count() or 8),
        )

        print(f"Collected {len(rows):,} updated/new files from {len(items):,} candidates")

        df_new = pd.DataFrame(rows)

        if df_new.empty:
            df = existing_df
        else:
            # hashing (optional, your hasher already threads)
            if self.hash_files:
                lprint(f"Hashing {len(df_new)} files")
                to_hash = [Path(p) for p in df_new["path"]]
                hashes = hash_many(to_hash, self.hash_workers)
                df_new["hash"] = df_new["path"].map(
                    lambda p: hashes.get(Path(p), None))

            # Convert to datetime in local timezone
            tz = self.timezone
            for col in ("create", "mod", "access"):
                df_new[col] = (
                    pd.to_datetime(df_new[col], unit="ns")
                    .dt.tz_localize("UTC")
                    .dt.tz_convert(tz)
                )

            # Combine with existing data (replace updated paths)
            if not existing_df.empty:
                existing_df = existing_df[~existing_df["path"].isin(
                    df_new["path"])]
                df = pd.concat([existing_df, df_new], ignore_index=True)
                lprint(f"df - new appended to existing, {len(df)} records")
            else:
                df = df_new
                lprint(f"df - created new, {len(df)} records")

        # replace database
        self._database = df

        # Update config files
        max_ns = int(
            df["mod"].max().value) if not df.empty else self.last_indexed

        # timing
        end = time.time()
        end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu_end = time.process_time()
        elapsed = end - start
        cpu_elapsed = cpu_end - cpu_start
        elapsed_wall_str = f"{int(elapsed // 60)}:{elapsed % 60:04.1f}"
        elapsed_cpu_str = f"{cpu_elapsed:.2f}s"
        new_files_per_second = (len(df_new) / elapsed) if elapsed > 0 else 0.0
        total_files_per_second = (len(df) / elapsed) if elapsed > 0 else 0.0

        # update config and add some interesting info
        self.set_attributes(
            last_indexed=max_ns,
            last_new_files=len(df_new),
            total_files=len(df),
            last_included_dirs=self.included_dirs.copy(),
            last_excluded_dirs=self.excluded_dirs.copy(),
            last_excluded_files=self.excluded_files.copy(),
            last_excluded_count=len(self.last_excluded_list or []),
            start_time=start_str,
            end_time=end_str,
            elapsed_wall_time=elapsed_wall_str,
            elapsed_cpu_time=elapsed_cpu_str,
            new_files_per_second=new_files_per_second,
            total_files_per_second=total_files_per_second,
        )

        # persist
        self.save()

    # (kept for inspection tools; no longer used by index, but handy)
    def filtered_files(self, root: Path):
        """(Legacy) Recursive yield of files honoring excluded regexes."""
        if self._re_excluded_dirs is None:
            self._re_excluded_dirs = _compile_ignores(self.excluded_dirs)
        if self._re_excluded_files is None:
            self._re_excluded_files = _compile_ignores(self.excluded_files)

        def recurse(dir_path: Path):
            for entry in dir_path.iterdir():
                if entry.is_dir():
                    if _name_matches_any(entry.name, self._re_excluded_dirs):
                        self.last_excluded_list.append(["dir", entry.name])
                        continue
                    yield from recurse(entry)
                elif entry.is_file() or entry.is_symlink():
                    if _name_matches_any(entry.name, self._re_excluded_files):
                        self.last_excluded_list.append(["file", entry.name])
                        continue
                    yield entry

        return recurse(root)

    def last_excluded_df(self):
        """Return details of excluded files and directories (for checking)."""
        d = pd.DataFrame(self.last_excluded_list or [],
                         columns=["reason", "file"])
        d["count"] = 1
        d = d.groupby(["reason", "file"])[["count"]].sum()
        return d

    @staticmethod
    def list():
        """List projects in the default location."""
        return list(BASE_DIR.glob("*.fdb-config"))

    @staticmethod
    def list_deets():
        """Dataframe of all projects in default location."""
        df = pd.concat(
            [ProjectManager(p).config_df for p in ProjectManager.list()], axis=1
        ).T.fillna("")
        df = df.set_index("project").T
        return df
