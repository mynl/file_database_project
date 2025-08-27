# app.py
"""
Flask backend for a small SPA that browses a prebuilt File Database.

Refactor highlights
-------------------
- "Pick File Database Project": a dropdown populated from BASE_DIR with *.fdb-config.
- "Load" button posts the chosen config to /api/load (you will fill in the loader).
- No exclude UI; filtering is handled by the external file DB.
- Search: fuzzy over full path; optional time filter (today/week/month/year with -N).
- Open: uses os.startfile on Windows; only allows paths present in the loaded DB.

You fill in:
- BASE_DIR (Path to directory containing *.fdb-config).
- load_project_db(config_path: Path) -> pd.DataFrame  (loader for your DB).

Expected DB columns (at minimum): name, path, mod, size, suffix
We normalize to:
- modified_ns (int UTC ns), modified_iso (str UTC), ext (no dot), parent (dirname), size_bytes (int).

Usage
-----

    set FLASK_DEBUG=1
    set FLASK_APP=app.py
    python app.py


"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
from threading import Lock
from typing import List, Optional, Tuple
import sys
import yaml

import pandas as pd
from flask import Flask, jsonify, make_response, request, send_from_directory

from rustfuzz import FuzzyMatcherMulti

sys.path.append('\\s\\telos\\python\\file_database_project')
from file_database import ProjectManager, BASE_DIR


if __name__ != '__main__':
    # defer set up with main
    logger = logging.getLogger(__name__)

# ---------------------------
# App + globals
# ---------------------------
app = Flask(__name__, static_folder="static", template_folder="static")

_ACTIVE = {
    "df": None,           # pd.DataFrame | None
    "config": None,       # Path | None
    "matcher": None,      # for Rust Fuzzy Matcher object
}
_ACTIVE_LOCK = Lock()


# ---------------------------
# Utilities
# ---------------------------
def _to_iso(ts: float) -> str:
    """POSIX seconds -> ISO 8601 UTC string YYYY-MM-DDTHH:MM:SSZ."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_time_spec(spec: str, tz_name: str = "Europe/London") -> Optional[Tuple[int, int]]:
    """Parse 'today[-N]', 'week[-N]', 'month[-N]', 'year[-N]'.
    Returns (start_ns, end_ns) in UTC nanoseconds, inclusive of current period and N-1 previous.
    """
    if not spec:
        return None
    s = spec.strip().casefold()
    # m = re.fullmatch(r"(today|week|month|year)(?:-(\d+))?", s)
    m = re.fullmatch(r"(h|d|w|m|y)(?:-(\d+))?", s)
    if not m:
        return None
    unit, n_str = m.groups()
    n = int(n_str) if n_str else 1
    if n <= 0:
        return None

    try:
        from zoneinfo import ZoneInfo  # py3.9+
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = datetime.now().astimezone().tzinfo

    now_local = datetime.now(tz)

    def sod(dt: datetime) -> datetime:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def sow(dt: datetime) -> datetime:
        d0 = sod(dt)
        return d0 - timedelta(days=d0.weekday())  # Monday=0

    def som(dt: datetime) -> datetime:
        return sod(dt).replace(day=1)

    def soy(dt: datetime) -> datetime:
        return sod(dt).replace(month=1, day=1)

    def minus_months(dt: datetime, k: int) -> datetime:
        total = dt.year * 12 + (dt.month - 1) - k
        y, m = divmod(total, 12)
        return dt.replace(year=y, month=m + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

    if unit == 'h':
        # hours
        base = sod(now_local)
        start_local = base - timedelta(hours=n - 1)
    elif unit == 'd':
        # day
        base = sod(now_local)
        start_local = base - timedelta(days=n - 1)
    elif unit == "w":
        # week
        base = sow(now_local)
        start_local = base - timedelta(weeks=n - 1)
    elif unit == "m":
        # month
        base = som(now_local)
        start_local = minus_months(base, n - 1)
    else:
        # year
        base = soy(now_local)
        start_local = base.replace(year=base.year - (n - 1))

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = now_local.astimezone(timezone.utc)
    return int(start_utc.timestamp() * 1e9), int(end_utc.timestamp() * 1e9)


def _normalize_loaded_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy normalized for the SPA."""
    out = df.copy()

    # path
    if "path" not in out.columns:
        raise ValueError("Loaded DB must include a 'path' column (absolute path).")

    # name
    if "name" not in out.columns:
        out["name"] = out["path"].map(lambda s: Path(s).name)

    # parent (directory path as string)
    out["parent"] = out["path"].map(lambda s: str(Path(s).parent))

    # ext (no dot): prefer 'suffix' if present
    if "suffix" in out.columns:
        out["ext"] = out["suffix"].astype(str).str.lstrip(".")
    else:
        out["ext"] = out["name"].map(lambda s: Path(s).suffix.lstrip("."))

    # size -> size_bytes
    if "size_bytes" not in out.columns:
        if "size" in out.columns:
            out["size_bytes"] = pd.to_numeric(out["size"], errors="coerce").fillna(0).astype("int64")
        else:
            out["size_bytes"] = 0

    # for fuzzy matching
    out["fuzzy"] = out.dir + ' ' + out['name'].str.replace('_', ' ')

    # modified time -> modified_ns + modified_iso (UTC)
    # accept 'mod' or 'modified' column
    ts_col = "mod" if "mod" in out.columns else ("modified" if "modified" in out.columns else None)
    if ts_col is None:
        raise ValueError("Loaded DB must include a 'mod' (or 'modified') timestamp column.")

    # parse timestamps (mixed tz-aware / naive supported)
    mod = pd.to_datetime(out[ts_col], errors="coerce", utc=False)
    # If Series has no tz, localize to local zone; else keep tz-aware
    if getattr(mod.dt, "tz", None) is None:
        local_tz = datetime.now().astimezone().tzinfo
        mod = mod.dt.tz_localize(local_tz, nonexistent="shift_forward", ambiguous="NaT")
    mod_utc = mod.dt.tz_convert("UTC")
    out["modified_ns"] = mod_utc.view("int64")  # epoch ns
    out["modified_iso"] = mod_utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Select + order a compact set used by the UI
    cols = ["name", "parent", "ext", "size_bytes", "modified_iso", "modified_ns",
            "path", "fuzzy"]
    return out[cols]


def load_project_db(config_path: Path) -> pd.DataFrame:
    """Given a *.fdb-config path, load and return the project's DataFrame.

    Expected columns (minimum): name, path, mod, size, suffix
    Return a DataFrame; _normalize_loaded_df will convert to the SPA schema.

    Replace this body with your real loader.
    """
    pm = ProjectManager(config_path)
    return pm.database


# ---------------------------
# Routes
# ---------------------------
@app.get("/api/projects")
def projects():
    """List available *.fdb-config files in BASE_DIR (non-recursive)."""
    base = BASE_DIR.resolve()
    if not base.exists() or not base.is_dir():
        return make_response(jsonify({"error": "BASE_DIR not found"}), 500)
    items = []
    for p in sorted(base.glob("*.fdb-config")):
        items.append({"path": str(p), "title": p.stem})
    return jsonify({"projects": items})


@app.post("/api/load")
def load():
    """Load selected project DB and prime matcher."""
    data = request.get_json(force=True, silent=True) or {}
    cfg = data.get("config")
    if not cfg:
        return make_response(jsonify({"error": "Missing 'config'"}), 400)

    cfg_path = Path(cfg).resolve()
    try:
        cfg_path.relative_to(BASE_DIR.resolve())
    except Exception:
        return make_response(jsonify({"error": "Config must be under BASE_DIR"}), 400)
    if not cfg_path.exists() or not cfg_path.is_file():
        return make_response(jsonify({"error": "Config path not found"}), 400)

    df_raw = load_project_db(cfg_path)  # <-- you implement
    df = _normalize_loaded_df(df_raw)

    with _ACTIVE_LOCK:
        _ACTIVE["df"] = df
        _ACTIVE["config"] = cfg_path
        _ACTIVE["matcher"] = FuzzyMatcherMulti(df['fuzzy'].to_list())

    return jsonify({
        "ok": True,
        "rows": int(len(df)),
        "config": str(cfg_path),
        "columns": list(df.columns),
    })


@app.get("/api/search")
def search():
    """Search current DB with optional time filter."""
    qt = request.args.get("q", default="", type=str)
    n = request.args.get("n", default=20, type=int)
    logger.info('query received %s', qt)
    qts = qt.split('@')
    q = t = ''
    if len(qts) == 1:
        q = qts[0].strip()
    elif len(qts) == 2:
        q, t = qts
        q = q.strip()
        t = t.strip()
    logger.info('parsed filtering q=%s, time=%s, n=%s', q, t, n)

    with _ACTIVE_LOCK:
        df: Optional[pd.DataFrame] = _ACTIVE["df"]
        if df is None or df.empty:
            return jsonify({"rows": [], "count": 0})

        original_records = len(df)

        # time filter
        filt_df = df
        bounds = _parse_time_spec(t)
        if bounds:
            start_ns, end_ns = bounds
            mask = (df["modified_ns"] >= start_ns) & (df["modified_ns"] < end_ns)
            filt_df = df.loc[mask]
            if filt_df.empty:
                return jsonify({"rows": [], "count": 0})
            logger.info('time bounds reduces df from %s to %s records',
                original_records, len(filt_df))

        # no query -> recency in window
        if not q.strip():
            rows = (
                filt_df.sort_values("modified_ns", ascending=False)
                .head(n)[["name", "parent", "ext", "size_bytes", "modified_iso", "path"]]
                .to_dict(orient="records")
            )
            return jsonify({"rows": rows, "count": len(rows)})

        # fuzzy + time: intersect by path
        limit = max(n * 5, n)
        matcher = _ACTIVE['matcher']
        idx_scores, scores = matcher.query(q, limit)
        if not idx_scores:
            return jsonify({"rows": [], "count": 0})

        if not idx_scores:
            return jsonify({"rows": [], "count": 0})
        if bounds:
            # only pick records in filt_df
            idx_scores = [i for i in idx_scores if i in filt_df.index]
        rows_df = filt_df.loc[idx_scores]
        logger.info('fuzzy query reduces from %s to %s records', len(filt_df), len(rows_df))
        if bounds:
            # prefer recency within matched set
            rows_df = rows_df.sort_values("modified_ns", ascending=False)
            logger.info('time and fuzzy - sorting on time')
        out = rows_df[["name", "parent", "ext", "size_bytes", "modified_iso", "path"]].to_dict(orient="records")
        return jsonify({"rows": out, "count": len(out)})


@app.get("/api/open")
def open_file():
    """Open a file via Windows default app. Only allows paths present in the loaded DB."""
    path_s = request.args.get("path")
    if not path_s:
        return make_response(jsonify({"error": "Missing 'path'"}), 400)

    with _ACTIVE_LOCK:
        if not _ACTIVE["allowed"]:
            return make_response(jsonify({"error": "No project loaded"}), 400)
        if path_s not in _ACTIVE["allowed"]:
            return make_response(jsonify({"error": "Path not in current DB"}), 400)

    p = Path(path_s).resolve()
    if not p.exists() or not p.is_file():
        return make_response(jsonify({"error": "Not a file"}), 400)
    os.startfile(str(p))
    return jsonify({"ok": True})


@app.get("/")
def index():
    """Serve the SPA."""
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    # when run like this we are responsible for setting up logging
    import logging.config

    config_path = Path('\\s\\telos\\python\\gs_project\\gstarter\\logconfig.yaml')
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)

    logger = logging.getLogger(__name__)
    logger.info('main logging setup...')

    app.run(host="127.0.0.1", port=5008, debug=True)
