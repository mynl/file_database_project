"""Manage config file and index database creation and updating."""

from datetime import datetime
from pathlib import Path
import re
import socket
import subprocess
import time
import yaml

import pandas as pd

from . import BASE_DIR
from . querier import query_ex, query_help as query_help_work
from . disk_info import DriveInfo
from . hasher import hash_many


class ProjectManager():
    """Manage single project config yaml (fdb-config) file."""

    def __init__(self, config_path: Path):
        """
        Load YAML config from file.

        The fdb-config suffix optional and added if missing.
        If not found in current directory, looks in local (eg. for default config).
        """
        self.config_path = Path(config_path)
        if self.config_path.suffix != '.fdb-config':
            self.config_path = self.config_path.with_suffix('.fdb-config')
        # print(self.config_path)
        if not self.config_path.exists():
            self.config_path = BASE_DIR / self.config_path.name
        # print(self.config_path)
        with self.config_path.open() as f:
            self._config = yaml.safe_load(f)
            self.hostname = socket.gethostname()
            if self.hostname.lower() != self._config['hostname'].lower():
                print(
                    f"WARNING: Host name {self.hostname} of machine does not match config file {cfg['hostname']}."
                )
        self._database = pd.DataFrame([])
        self._config_df = None

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
        return f'PM({self.config_path.name})'

    @property
    def config(self):
        """Return the config yaml dictionary."""
        return self._config

    @property
    def config_df(self):
        if self._config_df is None:
            self._config_df = pd.Series(self.config).to_frame('value')
            self._config_df.index.name = 'key'
        return self._config_df

    def set_attributes(self, **kwargs):
        """Set new attributes of config yaml dictionary."""
        for k, v in kwargs.items():
            self._config[k] = v

    def query(self, expr):
        """Run expr through the querier."""
        return query_ex(self.database, expr)

    @staticmethod
    def query_help():
        """Print help for query syntax."""
        return query_help_work()

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
        """Save dictionary to yaml."""
        backup = self.config_path.with_suffix('.fdb-config-bak')
        if backup.exists():
            backup.unlink()
        backup.hardlink_to(self.config_path)
        self.config_path.unlink()
        with self.config_path.open("w") as f:
            yaml.safe_dump(self._config, f,
                           sort_keys=False,                # preserve input order
                           default_flow_style=False,       # block structure
                           width=100,
                           indent=2
                           )
        self.database.to_feather(self.database_path)

    @property
    def database_path(self):
        """Get the database path name from config file."""
        return Path(self._config['database'])

    @property
    def database(self):
        """Return the database."""
        if self._database.empty:
            if self.database_path.exists():
                self._database = pd.read_feather(self.database_path)
        return self._database

    def reset(self):
        """Reset config, as though it has never been created."""
        self._config['last_indexed'] = 0
        self._config['last_included_dirs'] = []
        self._config['last_excluded_dirs'] = []
        self._config['last_excluded_files'] = []
        self._config['last_new_files'] = 0

    def schedule(self, execute=False):
        """Set up the task schedule for the project."""
        schedule_time = self.config.get('schedule_time', '')
        if schedule_time == "":
            print('Scheduling not defined in config file. Exiting.')
        schedule_frequency = self.schedule_frequency
        task_name = f'file-db-task {self.project}'
        cmd = [
            "schtasks",
            "/Create",
            "/TN", task_name,
            "/TR", f'file-db index -c "{str(self.config_path)}"',
            "/SC", schedule_frequency,
            "/ST", schedule_time,
            "/F"  # force update if exists
        ]

        if execute:
            print('Executing:\n\n', ' '.join(cmd))
            subprocess.run(cmd, check=True)
        else:
            print('Would execute\n\n', ' '.join(cmd))

    def index(self, mode: str | None = "update", verbose=False):
        """Incrementally scan and index files according to config."""
        # timer logging
        if verbose:
            def lprint(*argv):
                print(*argv)
        else:
            def lprint(*argv):
                pass

        start = time.time()
        cpu_start = time.process_time()
        start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        drive_info = DriveInfo()
        if mode == 'update':
            existing_df = self.database
            print(f'Updating index with {len(existing_df):,} entries')
        else:
            self.reset()
            existing_df = pd.DataFrame([])
            print('Creating all new index')

        last_indexed = self.last_indexed

        rows = []
        for root_str in self.included_dirs:
            root = Path(root_str)
            if not root.is_dir():
                print(
                    f'Odd {root=} is not a directory... in self.included_dirs')
                continue
            drive_letter = root.anchor[:-1].upper()
            vol_serial, drive_model, drive_serial = drive_info.drive_letter_id(
                drive_letter)
            for p in root.rglob("*"):
                if not p.is_file():
                    lprint(f'Not file {p}')
                    continue
                if self.is_excluded(p):
                    continue
                try:
                    stat = p.stat(follow_symlinks=self.follow_symlinks)
                    if stat.st_mtime_ns < last_indexed:
                        continue  # skip unchanged
                    entry = {
                        "name": p.name,
                        # omit the drive letter
                        "dir": str(p.parent.relative_to(p.anchor)),
                        "drive": drive_letter,                           # just letter
                        # whole path
                        "path": str(p),
                        "mod": stat.st_mtime_ns,
                        "create": stat.st_ctime,
                        "node": stat.st_ino,
                        "size": stat.st_size,
                        "suffix": p.suffix[1:],
                        "vol_serial": vol_serial,
                        "drive_model": drive_model,
                        "drive_serial": drive_serial,
                    }
                    rows.append(entry)
                except Exception as e:
                    print(f'FILE INFO EXCEPTION: {p}, {e}')
                    continue
            print(f'{root = } and {len(rows) = }')
        df_new = pd.DataFrame(rows)

        if df_new.empty:
            # ensures it is an empty df rather than None
            df = existing_df
        else:
            # new files to add
            if self.hash_files:
                lprint(f'Hashing {len(df_new)} files')
                to_hash = [Path(p) for p in df_new["path"]]
                hashes = hash_many(to_hash, self.hash_workers)
                df_new["hash"] = df_new["path"].map(
                    lambda p: hashes.get(Path(p), None))

            # Convert to date time in local timezone
            tz = self.timezone
            # low res second version
            # df["mod"] = pd.to_datetime(df["mod"], unit="s").dt.tz_localize("UTC").dt.tz_convert(tz)
            df_new["create"] = pd.to_datetime(
                df_new["create"], unit="s").dt.tz_localize("UTC").dt.tz_convert(tz)
            # more technically correct but makes querying harder
            # df["mod"] = pd.to_datetime(df["mod"], unit="ns", utc=True).dt.tz_convert(config["timezone"])
            # so go with
            df_new["mod"] = pd.to_datetime(df_new["mod"], unit="ns")

            # Combine with existing data (replace updated paths)
            if not existing_df.empty:
                existing_df = existing_df[~existing_df["path"].isin(
                    df_new["path"])]
                df = pd.concat([existing_df, df_new], ignore_index=True)
                lprint(f'df - new appended to existing, {len(df)} records')
            else:
                df = df_new
                lprint(f'df - created new, {len(df)} records')

        #

        # replace database
        self._database = df

        # Update config files
        # print(df.head())
        max_ns = int(df["mod"].max().value)  # convert to nanoseconds

        # index process timing
        end = time.time()
        end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu_end = time.process_time()
        elapsed = end - start
        cpu_elapsed = cpu_end - cpu_start
        elapsed_wall_str = f"{int(elapsed // 60)}:{elapsed % 60:04.1f}"
        elapsed_cpu_str = f"{cpu_elapsed:.2f}s"
        new_files_per_second = len(df_new) / elapsed
        total_files_per_second = len(df) / elapsed

        # update config and add some interesting info
        self.set_attributes(
            last_indexed=max_ns,
            last_new_files=len(df_new),
            total_files=len(df),
            last_included_dirs=self.included_dirs.copy(),
            last_excluded_dirs=self.excluded_dirs.copy(),
            last_excluded_files=self.excluded_files.copy(),
            start_time=start_str,
            end_time=end_str,
            elapsed_wall_time=elapsed_wall_str,
            elapsed_cpu_time=elapsed_cpu_str,
            new_files_per_second=new_files_per_second,
            total_files_per_second=total_files_per_second,
        )

        # save updated config and database to feather
        self.save()

    def is_excluded(self, path: Path) -> bool:
        """Return True if any part of path matches an exclusion pattern."""
        for part in path.parts:
            if any(re.search(pat, part) for pat in self.excluded_dirs):
                return True
        return any(re.search(pat, path.name) for pat in self.excluded_files)
