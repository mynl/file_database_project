# app.py
"""
Flask backend for a small SPA that:
- Pops a native Windows folder picker to choose the root directory.
- Scans files recursively, excluding path parts that match user-provided regexes (case-insensitive).
- Builds a pandas DataFrame with file metadata (ISO timestamps, sizes in bytes, types by extension).
- Provides a simple fuzzy-search endpoint over full paths (placeholder; plug in Rust later).
- Opens files via the Windows default application using os.startfile.

Endpoints
---------
POST  /api/pick                -> Launches a native folder picker (Windows) and returns the selected path
POST  /api/scan                -> Body: {"root": str, "excludes": [regex,...]} ; scans + caches a DataFrame
GET   /api/search?q=...&n=...  -> Fuzzy search over cached corpus; returns JSON rows
GET   /api/open?path=...       -> Opens a file with its associated default app (Windows)
GET   /                        -> Serves the single-page app (index.html)

Notes
-----
- Uses pathlib.Path for all file work.
- Regex excludes are matched case-insensitively against EACH path component and the file extension.
- "created" uses st_ctime on Windows.
- Placeholder fuzzy matcher is intentionally simple; swap out with your Rust module.

Usage
-----

    set FLASK_DEBUG=1
    set FLASK_APP=app.py
    python app.py

"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock
from typing import Iterable, List, Optional, Tuple
try:
    from zoneinfo import ZoneInfo  # Py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

import pandas as pd
from flask import Flask, jsonify, make_response, request, send_from_directory

# --- App setup ---
app = Flask(__name__, static_folder="static", template_folder="static")
app.config.update(TEMPLATES_AUTO_RELOAD=True, SEND_FILE_MAX_AGE_DEFAULT=0)


# Global cache guarded by a lock to keep things simple.
_CACHE_LOCK = Lock()
_CACHE = {
    "root": None,            # Path | None
    "excludes": [],          # list[str]
    "df": None,              # pd.DataFrame | None
    "corpus": [],            # list[str] full paths for matcher
}


# --- Helpers ---
def _compile_excludes(patterns: Iterable[str]) -> List[re.Pattern]:
    """Compile exclude regexes as case-insensitive; invalid patterns are ignored.

    Each pattern is applied to each path component and to the extension (without leading dot).
    """
    out: List[re.Pattern] = []
    for pat in patterns:
        try:
            out.append(re.compile(pat, re.IGNORECASE))
        except re.error:
            # Silently skip invalid regexes; could be logged if desired.
            continue
    return out


def _should_exclude(p: Path, excludes: List[re.Pattern]) -> bool:
    """Return True if any exclude regex matches any path part or the file extension.

    - Matches are case-insensitive by construction.
    - Only files are considered at the call site; directories are pruned by parts check.
    """
    parts = list(p.parts)
    if p.suffix:
        parts.append(p.suffix.lstrip("."))
    for rx in excludes:
        if any(rx.search(part) for part in parts):
            return True
    return False


def _to_iso(ts: float) -> str:
    """Convert POSIX timestamp (s) to an ISO 8601 string in UTC (YYYY-MM-DDTHH:MM:SSZ)."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _scan(root: Path, excludes: List[re.Pattern]) -> Tuple[pd.DataFrame, List[str]]:
    """Walk *root* recursively with directory pruning and return (DataFrame, corpus)."""
    recs: List[dict] = []
    corpus: List[str] = []

    root = root.resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)

        # prune subdirectories in-place
        dirnames[:] = [
            d for d in dirnames
            if not _should_exclude(dpath / d, excludes)
        ]

        for name in filenames:
            p = dpath / name
            if _should_exclude(p, excludes):
                continue
            try:
                st = p.stat()
            except OSError:
                continue

            p = p.resolve()
            abs_path = str(p)
            try:
                rel_path = p.relative_to(root).parent
                # now relative, e.g. "subdir/file.txt"
                subdir = str(rel_path)
            except ValueError:
                print(f'ValueError for {p.resolve()}')
                subdir = str(p.parent)
            recs.append({
                "path": abs_path,
                "name": p.name,
                "subdir": subdir,
                "ext": p.suffix.lstrip("."),
                "size_bytes": int(st.st_size),
                "created_iso": _to_iso(getattr(st, "st_ctime", st.st_mtime)),
                "modified_iso": _to_iso(st.st_mtime),
                "created_ns": int(getattr(st, "st_ctime_ns", int(st.st_mtime * 1e9))),
                "modified_ns": int(st.st_mtime_ns),
            })
            corpus.append(abs_path)

    df = pd.DataFrame.from_records(recs)
    return df, corpus


def _scan_old(root: Path, excludes: List[re.Pattern]) -> Tuple[pd.DataFrame, List[str]]:
    """Walk the directory tree under *root* and return (DataFrame, corpus).

    DataFrame columns:
      - path (str, absolute)
      - name (str)
      - parent (str)
      - ext (str, no dot)
      - size_bytes (int)
      - created_iso (str, UTC)
      - modified_iso (str, UTC)
      - created_ns (int)
      - modified_ns (int)
    """
    recs = []
    corpus = []
    for p in root.rglob("*"):
        # Skip directories early if a part is excluded
        if p.is_dir():
            if _should_exclude(p, excludes):
                continue
            else:
                continue  # directories are not records
        if not p.is_file():
            continue
        if _should_exclude(p, excludes):
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        abs_path = str(p.resolve())
        parent = str(p.parent)
        ext = p.suffix.lstrip(".")
        recs.append(
            {
                "path": abs_path,
                "name": p.name,
                "parent": parent,
                "ext": ext,
                "size_bytes": int(st.st_size),
                "created_iso": _to_iso(getattr(st, "st_ctime", st.st_mtime)),
                "modified_iso": _to_iso(st.st_mtime),
                "created_ns": int(getattr(st, "st_ctime_ns", int(st.st_mtime * 1e9))),
                "modified_ns": int(st.st_mtime_ns),
            }
        )
        corpus.append(abs_path)
    df = pd.DataFrame.from_records(recs)
    return df, corpus


def _parse_time_spec(spec: str, tz_name: str = "Europe/London") -> Optional[Tuple[int, int]]:
    """Parse time filter like 'today', 'today-3', 'week', 'week-3', 'month-3', 'year-2'.
    Returns (start_ns, end_ns) in UTC nanoseconds, or None if no/invalid spec.

    Semantics:
      - today         -> from start of local day to now
      - today-N       -> last N days including today (day-boundaries)
      - week          -> from Monday 00:00 local this week to now
      - week-N        -> last N weeks including this week (Mon-boundaries)
      - month         -> from first of this month 00:00 local to now
      - month-N       -> last N calendar months including this month
      - year          -> from Jan 1 this year 00:00 local to now
      - year-N        -> last N calendar years including this year
    """
    if not spec:
        return None

    s = spec.strip().casefold()
    m = re.fullmatch(r"(today|week|month|year)(?:-(\d+))?", s)
    if not m:
        return None

    unit, n_str = m.groups()
    n = int(n_str) if n_str else 1
    if n <= 0:
        return None

    # local time
    tz = ZoneInfo(tz_name) if ZoneInfo else datetime.now().astimezone().tzinfo
    now_local = datetime.now(tz)

    # helpers
    def start_of_day(dt: datetime) -> datetime:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def start_of_week(dt: datetime) -> datetime:
        sod = start_of_day(dt)
        return sod - timedelta(days=sod.weekday())  # Monday=0

    def start_of_month(dt: datetime) -> datetime:
        sod = start_of_day(dt)
        return sod.replace(day=1)

    def start_of_year(dt: datetime) -> datetime:
        sod = start_of_day(dt)
        return sod.replace(month=1, day=1)

    def minus_months(dt: datetime, k: int) -> datetime:
        # move to day 1 to avoid end-of-month pitfalls
        y, m = dt.year, dt.month
        m0 = m - k
        y -= ( (k - 1 + m - 1) // 12 )
        m0 = ((m - 1 - k) % 12) + 1
        # recompute y correctly
        years_delta = (m - 1 - k) // 12
        y = dt.year + years_delta
        # safer: compute total months and convert back
        total = (dt.year * 12 + (dt.month - 1)) - k
        y, m0 = divmod(total, 12)
        return dt.replace(year=y, month=m0 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # choose start
    if unit == "today":
        base = start_of_day(now_local)
        start_local = base - timedelta(days=(n - 1))
    elif unit == "week":
        base = start_of_week(now_local)
        start_local = base - timedelta(weeks=(n - 1))
    elif unit == "month":
        base = start_of_month(now_local)
        start_local = minus_months(base, n - 1)
    else:  # "year"
        base = start_of_year(now_local)
        start_local = base.replace(year=base.year - (n - 1))

    # convert to UTC ns
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = now_local.astimezone(timezone.utc)
    start_ns = int(start_utc.timestamp() * 1e9)
    end_ns = int(end_utc.timestamp() * 1e9)
    return start_ns, end_ns


# --- Placeholder fuzzy matcher ---
class SimpleFuzzy:
    """Very small, fast-enough placeholder to be replaced by your Rust matcher.

    Strategy: casefolded substring hit -> score = |match| / |path|; otherwise 0.
    """

    def __init__(self) -> None:
        self._items: List[str] = []
        self._folded: List[str] = []

    def load(self, items: List[str]) -> None:
        self._items = items
        self._folded = [s.casefold() for s in items]

    def search(self, query: str, limit: int = 200) -> List[Tuple[int, float]]:
        q = query.strip().casefold()
        if not q:
            # Return first N by recency (as-is ordering); caller can sort by modified_ns from df.
            return [(i, 0.0) for i in range(min(limit, len(self._items)))]
        hits: List[Tuple[int, float]] = []
        for i, s in enumerate(self._folded):
            pos = s.find(q)
            if pos != -1:
                score = len(q) / max(1, len(s))
                hits.append((i, score))
        hits.sort(key=lambda t: t[1], reverse=True)
        return hits[:limit]


_MATCHER = SimpleFuzzy()


# --- Routes ---
@app.post("/api/pick")
def pick_folder():
    """Open a native folder picker (Windows) and return the chosen path.

    Returns {"root": str} or {"root": null} if canceled.
    """
    # Local import to avoid Tk on non-pick routes.
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    selected = filedialog.askdirectory(title="Select root directory")
    root.destroy()
    return jsonify({"root": selected or None})


@app.post("/api/scan")
def scan():
    """Scan the directory; body must include JSON with keys: root, excludes (list[str])."""
    data = request.get_json(force=True, silent=True) or {}
    root_s = data.get("root")
    excludes_list = data.get("excludes", [])

    if not root_s:
        return make_response(jsonify({"error": "Missing 'root'"}), 400)

    root = Path(root_s).resolve()
    if not root.exists() or not root.is_dir():
        return make_response(jsonify({"error": "Root is not a directory"}), 400)

    rx = _compile_excludes(excludes_list)
    df, corpus = _scan(root, rx)

    with _CACHE_LOCK:
        _CACHE["root"] = root
        _CACHE["excludes"] = list(excludes_list)
        _CACHE["df"] = df
        _CACHE["corpus"] = corpus
        _MATCHER.load(corpus)

    return jsonify({
        "count": int(len(df)),
        "root": str(root),
        "columns": list(df.columns),
    })


@app.get("/api/search")
def search():
    """Search cached corpus with query q and return top rows as JSON.

    Query params:
      q: query string
      n: optional int limit (default 200)
      t: time filter
    """
    q = request.args.get("q", default="", type=str)
    n = request.args.get("n", default=200, type=int)
    t = request.args.get("t", default="", type=str)

    with _CACHE_LOCK:
        df: Optional[pd.DataFrame] = _CACHE.get("df")
        if df is None or df.empty:
            return jsonify({"rows": [], "count": 0})

        # apply time filter if provided
        filt_df = df
        bounds = _parse_time_spec(t)
        if bounds:
            start_ns, end_ns = bounds
            mask = (df["modified_ns"] >= start_ns) & (df["modified_ns"] < end_ns)
            filt_df = df.loc[mask]

        if filt_df.empty:
            return jsonify({"rows": [], "count": 0})

        if not q.strip():
            # default: most recent first within the time window
            rows = (
                filt_df.sort_values("modified_ns", ascending=False)
                .head(n)[["name", "subdir", "ext", "size_bytes", "modified_iso", "path"]]
                .to_dict(orient="records")
            )
            return jsonify({"rows": rows, "count": len(rows)})

        # fuzzy + time: intersect by path
        limit = max(n * 5, n)  # widen pool so time filter doesn't starve results
        idx_scores = _MATCHER.search(q, limit=limit)
        if not idx_scores:
            return jsonify({"rows": [], "count": 0})

        allowed = set(filt_df["path"])
        corpus: List[str] = _CACHE.get("corpus", [])
        chosen_paths: List[str] = []
        for i, _score in idx_scores:
            if i < 0 or i >= len(corpus):
                continue
            pth = corpus[i]
            if pth in allowed:
                chosen_paths.append(pth)
                if len(chosen_paths) >= n:
                    break

        if not chosen_paths:
            return jsonify({"rows": [], "count": 0})

        idxed = filt_df.set_index("path", drop=False)
        rows_df = idxed.loc[chosen_paths]
        # rows_df = idxed.loc[chosen_paths]  # keep matcher order
        rows_df = idxed.loc[chosen_paths].sort_values("modified_ns", ascending=False)  # recency-first

        out = rows_df[["name", "subdir", "ext", "size_bytes", "modified_iso", "path"]].to_dict(orient="records")
        return jsonify({"rows": out, "count": len(out)})

@app.get("/api/open")
def open_file():
    """Open a file via Windows default application.

    Security: only allow paths under the cached root.
    """
    path_s = request.args.get("path")
    if not path_s:
        return make_response(jsonify({"error": "Missing 'path'"}), 400)
    with _CACHE_LOCK:
        root: Optional[Path] = _CACHE.get("root")
        if root is None:
            return make_response(jsonify({"error": "No root set"}), 400)
        p = Path(path_s).resolve()
        try:
            p.relative_to(root)
        except Exception:
            return make_response(jsonify({"error": "Path not under root"}), 400)
    if not p.exists() or not p.is_file():
        return make_response(jsonify({"error": "Not a file"}), 400)
    os.startfile(str(p))
    return jsonify({"ok": True})


@app.get("/")
def index():
    """Serve the SPA index.html."""
    return send_from_directory(app.static_folder, "index.html")


@app.after_request
def _no_cache(resp):
    """Disable client caching in dev so static edits show on refresh."""
    resp.headers["Cache-Control"] = "no-store"
    return resp


if __name__ == "__main__":
    # Windows-only dev run.
    app.run(host="127.0.0.1", port=5008, debug=True)


