"""File database project."""

import os
from pathlib import Path


__appname__ = 'file_database'
__author__ = 'Stephen Mildenhall'
__date__ = '2025-05-14'


def _get_local_folder():
    local_app_data = Path(os.environ["LOCALAPPDATA"])
    my_app_data = local_app_data / __appname__
    my_app_data.mkdir(parents=True, exist_ok=True)
    return my_app_data


BASE_DIR = _get_local_folder()

DEFAULT_CONFIG_FILE = BASE_DIR / "default.fdb-config"


# avoid circular import errors
from . __version__ import __version__
from . manager import ProjectManager  # noqa

