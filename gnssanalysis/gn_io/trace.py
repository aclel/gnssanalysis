"""TRACE file parser. Note the separate functions for values and residuals"""

import logging as _logging
import os as _os
import re as _re
from io import BytesIO as _BytesIO
from pathlib import Path as _Path
from typing import Iterable as _Iterable, Optional as _Optional
import warnings as _warnings

import pandas as _pd
import numpy as _np

from .. import gn_aux as _gn_aux
from .. import gn_const as _gn_const
from .. import gn_datetime as _gn_datetime
from .. import gn_io as _gn_io


# Regex patterns for parsing TRACE files
FLOAT = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
SPECIAL_FLOAT = r"(?:nan|-nan|inf|-inf)"
FLOAT_TOKEN = rf"(?:{FLOAT}|{SPECIAL_FLOAT})"

# Residual line regex (supports negative iter for smoothed files, and optional ratio fields)
LINE_RE = _re.compile(
    rf"""
    ^%\s+
    (?P<iter>-?\d+)\s+
    (?P<date>\d{{4}}-\d{{2}}-\d{{2}})\s+                 # e.g. 2025-10-05
    (?P<time>\d{{2}}:\d{{2}}:\d{{2}}(?:\.\d+)?)\s+       # e.g. 00:01:00.00
    (?P<meas>(?:CODE_MEAS|PHAS_MEAS))\s+
    (?P<sat>\S+)\s+
    (?P<recv>\S+)\s+
    (?P<sig>\S+)\s+
    (?P<prefit>{FLOAT})\s+
    (?P<postfit>{FLOAT})\s+
    (?P<sigma>{FLOAT})
    (?:\s+(?P<prefit_ratio>{FLOAT})\s+(?P<postfit_ratio>{FLOAT}))?  # optional at higher trace level
    \s+(?P<label>\S+)\s*$
    """,
    _re.VERBOSE,
)

# Large error regex (handles both STATE and MEAS errors)
LARGE_RE = _re.compile(
    r"""^(?P<date>\d{4}-\d{2}-\d{2})\s+
        (?P<time>\d{2}:\d{2}:\d{2}\.\d+)\s+
        LARGE\s+(?P<kind>STATE|MEAS)\s+ERROR\s+OF\s*:\s*
        (?P<value>[0-9.]+)\s+AT\s+\d+\s*:\s*
        (?:(?P<meas_type>\S+)\s+(?P<sat>\S+)\s+(?P<recv>\S+)\s+(?P<sig>\S+)
        |
        (?P<param>\S+)\s+(?P<recv2>\S+)\s+(?P<comp>\S+))""",
    _re.VERBOSE,
)

# Ambiguity reset regex (handles both PREPROC and REJECT)
AMB_RE = _re.compile(
    r"""^(?P<date>\d{4}-\d{2}-\d{2})\s+
        (?P<time>\d{2}:\d{2}:\d{2}\.\d+)\s+
        Ambiguity\ Removed\s+
        -\s+(?P<action>PREPROC|REJECT)\s+
        AMBIGUITY\s+
        (?P<sat>\S+)\s+
        (?P<recv>\S+)\s+
        (?P<sig>\S+)
        (?P<rest>.*)$
    """,
    _re.VERBOSE
)


def _to_float_or_nan(x: str) -> float:
    """Convert string to float, return NaN on failure."""
    try:
        return float(x)
    except Exception:
        return float("nan")


def parse_residual_lines(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse residual lines (starting with '%') from Network TRACE files.

    Supports both classic 12-field format and higher-trace 14-field format with ratios.
    Also supports negative iteration numbers from smoothed TRACE files.

    When files contain multiple iterations (forward + smoothed), use keep_last_iteration()
    to filter to the final iteration per observation.

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        Columns:
            - iter     : int   — filter iteration number (can be negative for smoothed)
            - date     : str   — date string (YYYY-MM-DD)
            - time     : str   — time string (HH:MM:SS.fff)
            - meas     : str   — measurement type ("PHAS_MEAS" or "CODE_MEAS")
            - sat      : str   — satellite identifier (e.g. "G20")
            - recv     : str   — receiver/station code
            - sig      : str   — signal code (e.g. "L1C")
            - prefit   : float — prefit residual value
            - postfit  : float — postfit residual value
            - sigma    : float — measurement sigma
            - label    : str   — signal label
            - prefit_ratio  : float — prefit ratio (NaN if not present)
            - postfit_ratio : float — postfit ratio (NaN if not present)
            - datetime : pd.Timestamp — parsed timestamp

    Examples
    --------
    >>> with open("trace.SUM") as f:
    ...     df = parse_residual_lines(f)
    >>> df = keep_last_iteration(df)  # Keep only final iteration
    """
    records = []
    for ln in lines:
        if not ln.startswith('%'):
            continue
        m = LINE_RE.match(ln)
        if not m:
            continue
        gd = m.groupdict()

        rec = {
            "iter": int(gd["iter"]),
            "date": gd["date"],
            "time": gd["time"],
            "meas": gd["meas"],
            "sat": gd["sat"],
            "recv": gd["recv"],
            "sig": gd["sig"],
            "prefit": _to_float_or_nan(gd["prefit"]),
            "postfit": _to_float_or_nan(gd["postfit"]),
            "sigma": _to_float_or_nan(gd["sigma"]),
            "label": gd["label"],
        }

        # Optional higher-trace columns
        pr = gd.get("prefit_ratio")
        por = gd.get("postfit_ratio")
        rec["prefit_ratio"]  = _to_float_or_nan(pr)  if pr  is not None else float("nan")
        rec["postfit_ratio"] = _to_float_or_nan(por) if por is not None else float("nan")

        records.append(rec)

    if not records:
        return _pd.DataFrame(columns=[
            "iter","date","time","meas","sat","recv","sig",
            "prefit","postfit","sigma","label","prefit_ratio","postfit_ratio","datetime"
        ])

    df = _pd.DataFrame.from_records(records)
    df["datetime"] = _pd.to_datetime(
        df["date"] + " " + df["time"],
        format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
    )
    return df


def parse_large_errors(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse 'LARGE STATE ERROR' and 'LARGE MEAS ERROR' lines from Network TRACE files.

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        For MEAS errors, columns: datetime, kind, value, meas_type, sat, recv, sig
        For STATE errors, columns: datetime, kind, value, recv, param, comp
    """
    recs = []
    for ln in lines:
        if "LARGE" not in ln:
            continue
        m = LARGE_RE.match(ln)
        if not m:
            continue
        gd = m.groupdict()
        dt = _pd.to_datetime(gd["date"] + " " + gd["time"])
        kind = gd["kind"]
        val = float(gd["value"])
        if kind == "STATE":
            recs.append({
                "datetime": dt,
                "kind": kind,
                "value": val,
                "recv": gd["recv2"],
                "param": gd["param"],
                "comp": gd["comp"],
            })
        else:
            recs.append({
                "datetime": dt,
                "kind": kind,
                "value": val,
                "meas_type": gd["meas_type"],
                "sat": gd["sat"],
                "recv": gd["recv"],
                "sig": gd["sig"],
            })
    return _pd.DataFrame.from_records(recs)


def parse_ambiguity_resets(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse 'Ambiguity Removed' lines (both PREPROC and REJECT actions) from Network TRACE files.

    PREPROC: Ambiguities removed during preprocessing (GF, MW, LLI, SCDIA, retrack cycle slip detection)
    REJECT: Ambiguities removed by Kalman filter

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        Columns:
            - datetime : pd.Timestamp — timestamp of reset
            - action   : str — "PREPROC" or "REJECT"
            - sat      : str — satellite identifier
            - recv     : str — receiver/station code
            - sig      : str — signal code
            - reasons  : str — comma-separated reset reasons
    """
    recs = []
    for ln in lines:
        if "Ambiguity Removed" not in ln:
            continue
        m = AMB_RE.match(ln.rstrip("\n"))
        if not m:
            continue
        gd = m.groupdict()
        dt = _pd.to_datetime(f"{gd['date']} {gd['time']}", errors="coerce")

        # Parse reasons from tail
        tail = gd.get("rest", "")
        reasons = []
        for chunk in tail.split("-"):
            t = chunk.strip()
            if not t:
                continue
            if t.upper() in {"PREPROC", "REJECT", "AMBIGUITY"}:
                continue
            reasons.append(t)

        # Clean, dedupe while preserving order
        clean = []
        seen = set()
        for r in reasons:
            rr = _re.sub(r"\s+", " ", r)
            if rr not in seen:
                seen.add(rr)
                clean.append(rr)

        # Add 'KF' reason for REJECT (Kalman filter), if not already present
        action_str = gd["action"].strip().upper()
        if action_str == "REJECT":
            # check case-insensitively if KF already present
            present_upper = {x.upper() for x in clean}
            if "KF" not in present_upper:
                clean.insert(0, "KF")  # put first so it's prominent

        recs.append(
            {
                "datetime": dt,
                "action": action_str,  # PREPROC / REJECT
                "sat": gd["sat"].strip(),
                "recv": gd["recv"].strip(),
                "sig": gd["sig"].strip(),
                "reasons": ", ".join(clean),
            }
        )

    return _pd.DataFrame.from_records(recs)


def parse_lc(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse LC (linear combination) lines from station TRACE files.

    LC combos include: zd, mp, gf, mw, wl, if (zero-difference, multipath,
    geometry-free, Melbourne-Wübbena, wide-lane, ionosphere-free)

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines from LC combo blocks (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        Columns:
            - datetime    : pd.Timestamp — timestamp
            - sat         : str — satellite identifier
            - combo_type  : str — combination type (zd, mp, gf, mw, wl, if)
            - code_type   : str — code type (L for phase, P for code)
            - combo_label : str — specific combination label (L1, L2, L5, gf12, etc.)
            - value       : float — measurement value
    """
    line_list = []
    for ln in lines:
        if not isinstance(ln, str):
            continue
        stripped = ln.strip()
        if not stripped or stripped.startswith('*'):
            continue
        line_list.append(stripped)
    if not line_list:
        return _pd.DataFrame(
            columns=['datetime', 'sat', 'combo_type', 'code_type', 'combo_label', 'value']
        )

    series = _pd.Series(line_list)

    extracted = series.str.extract(
        r"""
        ^\s*
        (?P<datetime>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)
        \s+sat=\s+(?P<sat>\S+)
        \s+(?P<combo_type>\S+)
        \s+(?P<code_type>\S+)
        \s+--\s+(?P<measurements>.+)$
        """,
        flags=_re.VERBOSE,
    ).dropna(subset=["datetime", "sat", "combo_type", "code_type", "measurements"])

    if extracted.empty:
        return _pd.DataFrame(
            columns=['datetime', 'sat', 'combo_type', 'code_type', 'combo_label', 'value']
        )

    pairs = extracted["measurements"].str.extractall(
        rf"(?P<combo_label>\w+)\s*=\s*(?P<value>{FLOAT_TOKEN})"
    )
    if pairs.empty:
        return _pd.DataFrame(
            columns=['datetime', 'sat', 'combo_type', 'code_type', 'combo_label', 'value']
        )

    pairs = pairs.reset_index(level=-1, drop=True)
    df = pairs.join(extracted.drop(columns="measurements"))
    df["datetime"] = _pd.to_datetime(df["datetime"], errors="coerce")
    df["value"] = _pd.to_numeric(df["value"], errors="coerce")
    df["value"] = df["value"].replace([_np.inf, -_np.inf], _np.nan)
    df = df.dropna(subset=["datetime"])

    df = df.reset_index(drop=True)[
        ['datetime', 'sat', 'combo_type', 'code_type', 'combo_label', 'value']
    ]
    for col in ['sat', 'combo_type', 'code_type', 'combo_label']:
        df[col] = df[col].astype(object)
    df['value'] = df['value'].astype(float)
    return df


def parse_pde_cs(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse PDE cycle slip detection & repair metrics from TRACE files.

    PDE-CS lines contain metrics for cycle slip detection including geometry-free,
    Melbourne-Wübbena combinations, and validation statistics.

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        Columns:
            - datetime : pd.Timestamp — timestamp
            - sat      : str — satellite identifier
            - mode     : str — frequency mode (TRIP/DUAL/None)
            - el       : float — elevation angle (degrees)
            - lamw     : float — lambda wide-lane (meters)
            - gf12     : float — geometry-free L1-L2 (meters)
            - mw12     : float — Melbourne-Wübbena L1-L2 (meters)
            - siggf    : float — sigma geometry-free (meters)
            - sigmw    : float — sigma Melbourne-Wübbena (meters)
            - lamew    : float — lambda extra-wide-lane (meters)
            - gf25     : float — geometry-free L2-L5 (meters)
            - mw25     : float — Melbourne-Wübbena L2-L5 (meters)
            - vtpv     : float — V-transpose P V statistic
            - val      : float — validation statistic
            - thres    : float — threshold value
            - N1       : float — ambiguity L1 (cycles)
            - N2       : float — ambiguity L2 (cycles)
            - N5       : float — ambiguity L5 (cycles)
    """
    line_list = []
    for ln in lines:
        if not isinstance(ln, str):
            continue
        stripped = ln.strip()
        if stripped.startswith("PDE-CS"):
            line_list.append(stripped)
    if not line_list:
        return _pd.DataFrame(columns=[
            'datetime', 'sat', 'mode', 'el', 'lamw', 'gf12', 'mw12', 'siggf',
            'sigmw', 'lamew', 'gf25', 'mw25', 'vtpv', 'val', 'thres', 'N1', 'N2', 'N5'
        ])

    series = _pd.Series(line_list)
    series = series[~series.str.contains(r"epoch\s+prn", regex=True, na=False)]
    if series.empty:
        return _pd.DataFrame(columns=[
            'datetime', 'sat', 'mode', 'el', 'lamw', 'gf12', 'mw12', 'siggf',
            'sigmw', 'lamew', 'gf25', 'mw25', 'vtpv', 'val', 'thres', 'N1', 'N2', 'N5'
        ])

    base = series.str.extract(
        r"""
        ^\s*PDE-CS\s+GPST\s+
        (?:(?P<mode>TRIP|DUAL)\s+)?
        (?P<datetime>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+
        (?P<sat>\S+)\s+
        (?P<el>-?\d+(?:\.\d+)?)\s+
        (?P<rest>.*)$
        """,
        flags=_re.VERBOSE,
    )

    base = base.dropna(subset=["datetime", "sat", "el"])

    if base.empty:
        return _pd.DataFrame(columns=[
            'datetime', 'sat', 'mode', 'el', 'lamw', 'gf12', 'mw12', 'siggf',
            'sigmw', 'lamew', 'gf25', 'mw25', 'vtpv', 'val', 'thres', 'N1', 'N2', 'N5'
        ])

    metrics = base.pop("rest").fillna("")
    base["datetime"] = _pd.to_datetime(base["datetime"], errors="coerce")
    base["el"] = _pd.to_numeric(base["el"], errors="coerce")
    base = base.dropna(subset=["datetime"])

    flag_series = metrics.str.extract(
        r"--\s*(?P<flag>low_elevation|single\s+frequency)\s*--",
        flags=_re.IGNORECASE,
    )
    base["flag"] = (
        flag_series["flag"]
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )
    base["flag"] = base["flag"].where(base["flag"].notna(), None)

    split_metrics = metrics.str.split("vtpv=", n=1, expand=True)
    metric_values = split_metrics[0].fillna("")
    tail_values = split_metrics[1].fillna("")

    token_lists = metric_values.str.findall(rf"{FLOAT_TOKEN}")
    values = _pd.DataFrame(token_lists.tolist(), index=metric_values.index)
    col_map = ['lamw', 'gf12', 'mw12', 'siggf', 'sigmw', 'lamew', 'gf25', 'mw25']
    for idx, col in enumerate(col_map):
        if values is not None and idx in values.columns:
            src = values[idx]
        else:
            src = _pd.Series(_np.nan, index=values.index)
        base[col] = _pd.to_numeric(src, errors="coerce")

    base['vtpv'] = _pd.to_numeric(
        tail_values.str.extract(rf"^\s*(?P<vtpv>{FLOAT_TOKEN})")['vtpv'],
        errors="coerce",
    )
    base['val'] = _pd.to_numeric(
        tail_values.str.extract(rf"val=\s*(?P<val>{FLOAT_TOKEN})")['val'],
        errors="coerce",
    )
    base['thres'] = _pd.to_numeric(
        tail_values.str.extract(rf"thres=\s*(?P<thres>{FLOAT_TOKEN})")['thres'],
        errors="coerce",
    )

    post_thres = tail_values.str.extract(rf"thres=\s*{FLOAT_TOKEN}(?P<tail>.*)$")['tail'].fillna("")
    n_values = post_thres.str.extractall(rf"(?P<num>{FLOAT_TOKEN})")['num'].unstack()
    for idx, col in enumerate(['N1', 'N2', 'N5']):
        if idx in n_values.columns:
            src = n_values[idx]
        else:
            src = _pd.Series(_np.nan, index=n_values.index)
        base[col] = _pd.to_numeric(src, errors="coerce")

    numeric_cols = [
        'el', 'lamw', 'gf12', 'mw12', 'siggf', 'sigmw',
        'lamew', 'gf25', 'mw25', 'vtpv', 'val', 'thres', 'N1', 'N2', 'N5'
    ]
    base[numeric_cols] = base[numeric_cols].apply(_pd.to_numeric, errors="coerce")
    base[numeric_cols] = base[numeric_cols].replace([_np.inf, -_np.inf], _np.nan)
    base[numeric_cols] = base[numeric_cols].astype(float)
    base['mode'] = base['mode'].where(base['mode'].notna(), None).astype(object)
    base['sat'] = base['sat'].astype(object)
    base['flag'] = base['flag'].astype(object)

    result = base[['datetime', 'sat', 'mode', 'flag'] + numeric_cols].dropna(subset=["datetime", "sat"])
    return result.reset_index(drop=True)


def parse_elevation(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse satellite elevation angles from TRACE files.

    This is a convenience function that calls parse_pde_cs() and returns
    only the elevation-related columns for simpler analysis.

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        Columns:
            - datetime : pd.Timestamp — timestamp
            - sat      : str — satellite identifier
            - el       : float — elevation angle (degrees)
            - mode     : str — frequency mode (TRIP/DUAL/None)
    """
    df = parse_pde_cs(lines)

    if df.empty:
        return _pd.DataFrame(columns=['datetime', 'sat', 'el', 'mode'])

    # Return only elevation-relevant columns
    return df[['datetime', 'sat', 'el', 'mode']].copy()


def keep_last_iteration(df: _pd.DataFrame) -> _pd.DataFrame:
    """
    Filter residual DataFrame to keep only the last iteration for each observation.

    When TRACE files contain multiple iterations (e.g., forward + smoothed),
    this keeps only the final iteration for each unique combination of
    (datetime, meas, sat, recv, sig, label).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame from parse_residual_lines() with 'iter' column

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with only last iterations, sorted by (datetime, sat, sig)

    Examples
    --------
    >>> df = parse_residual_lines(open("trace.SUM"))
    >>> df = keep_last_iteration(df)  # Keep only final iteration
    """
    if df.empty:
        return df
    keys = ["datetime", "meas", "sat", "recv", "sig", "label"]
    return (
        df.sort_values(["datetime", "iter"])
          .drop_duplicates(subset=keys, keep="last")
          .sort_values(["datetime", "sat", "sig"])
          .reset_index(drop=True)
    )


def parse_residuals(
    paths: _Iterable[_Path],
    strategy: str = "auto",
    forward_keep_last: bool = True,
    smoothed_iteration: _Optional[int] = -1,
    include_source: bool = False,
) -> _pd.DataFrame:
    """
    Parse residual observations from a collection of network TRACE files.

    Parameters
    ----------
    paths : Iterable[pathlib.Path | str]
        Collection of TRACE files (forward and/or smoothed). Files are grouped by
        their base name (with the ``_smoothed`` suffix removed) so that forward and
        smoothed pairs can be resolved automatically.
    strategy : {"auto", "smoothed", "forward", "both"}, default "auto"
        Selection strategy for choosing between smoothed and forward residuals.
        - "auto": prefer smoothed residuals, fall back to forward when smoothed missing.
        - "smoothed": use smoothed residuals, fall back to forward with a warning.
        - "forward": use forward residuals, fall back to smoothed with a warning.
        - "both": include both smoothed and forward residuals.
    forward_keep_last : bool, default True
        When consuming forward traces, keep only the last iteration per observation
        (via :func:`keep_last_iteration`). Set to False to retain all iterations.
    smoothed_iteration : int | None, default -1
        Iteration to keep from smoothed traces. Use None to keep every iteration.
    include_source : bool, default False
        When True, append a ``source_path`` column with the file each record came from.

    Returns
    -------
    pandas.DataFrame
        Residual observations including a ``trace_type`` column that records whether
        the data came from a smoothed or forward TRACE file. Additional columns match
        :func:`parse_residual_lines`.
    """

    strategy = strategy.lower()
    valid_strategies = {"auto", "smoothed", "forward", "both"}
    if strategy not in valid_strategies:
        raise ValueError(
            f"Invalid strategy '{strategy}'. Expected one of {sorted(valid_strategies)}."
        )

    paths = list(paths or [])
    key_columns = ["datetime", "meas", "sat", "recv", "sig", "label"]
    base_columns = [
        "iter",
        "date",
        "time",
        "meas",
        "sat",
        "recv",
        "sig",
        "prefit",
        "postfit",
        "sigma",
        "label",
        "prefit_ratio",
        "postfit_ratio",
        "datetime",
        "trace_type",
    ]
    if include_source:
            base_columns.append("source_path")

    if not paths:
        return _pd.DataFrame(columns=base_columns)

    grouped = {}
    for raw in paths:
        path = _Path(raw)
        if not path.exists():
            _warnings.warn(f"TRACE residual file not found: {path}", RuntimeWarning, stacklevel=2)
            continue

        stem_lower = path.stem.lower()
        is_smoothed = "_smoothed" in stem_lower
        base_stem = path.stem.replace("_smoothed", "")
        key = (base_stem, path.parent)
        entry = grouped.setdefault(key, {"smoothed": [], "forward": []})
        entry["smoothed" if is_smoothed else "forward"].append(path)

    def _parse_residual_file(path: _Path) -> _pd.DataFrame:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            return parse_residual_lines(fh)

    forward_file_cache = {}
    forward_group_merge = {}
    for key, entry in grouped.items():
        frames_for_merge = []
        for forward_path in entry["forward"]:
            try:
                df_raw = _parse_residual_file(forward_path)
            except Exception as exc:
                _warnings.warn(
                    f"Failed to parse residuals from {forward_path}: {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                continue

            if df_raw.empty:
                continue

            df_forward = df_raw.copy()
            if forward_keep_last:
                df_forward = keep_last_iteration(df_forward)
            forward_file_cache[forward_path] = df_forward

            frames_for_merge.append(keep_last_iteration(df_raw.copy()))

        if frames_for_merge:
            combined = _pd.concat(frames_for_merge, ignore_index=True)
            combined = keep_last_iteration(combined)
            if not combined.empty:
                forward_group_merge[key] = combined.set_index(key_columns)

    selected = []
    for (base_stem, parent), entry in grouped.items():
        smoothed_files = entry["smoothed"]
        forward_files = entry["forward"]

        def _warn_fallback(missing: str) -> None:
            available = "forward" if missing == "smoothed" else "smoothed"
            if entry[available]:
                msg = (
                    f"No {missing} residuals found for '{base_stem}' in {parent}; "
                    f"using {available} residuals instead."
                )
                _warnings.warn(msg, RuntimeWarning, stacklevel=2)

        if strategy == "auto":
            if smoothed_files:
                selected.extend((path, "smoothed") for path in smoothed_files)
            elif forward_files:
                selected.extend((path, "forward") for path in forward_files)
        elif strategy == "smoothed":
            if smoothed_files:
                selected.extend((path, "smoothed") for path in smoothed_files)
            elif forward_files:
                _warn_fallback("smoothed")
                selected.extend((path, "forward") for path in forward_files)
        elif strategy == "forward":
            if forward_files:
                selected.extend((path, "forward") for path in forward_files)
            elif smoothed_files:
                _warn_fallback("forward")
                selected.extend((path, "smoothed") for path in smoothed_files)
        elif strategy == "both":
            selected.extend((path, "smoothed") for path in smoothed_files)
            selected.extend((path, "forward") for path in forward_files)

    frames = []
    smoothed_file_cache = {}
    for idx, (path, trace_type) in enumerate(selected):
        base_stem = path.stem.replace("_smoothed", "")
        group_key = (base_stem, path.parent)

        try:
            if trace_type == "forward":
                df = forward_file_cache.get(path)
                if df is None:
                    df_raw = _parse_residual_file(path)
                    if df_raw.empty:
                        continue
                    df = df_raw.copy()
                    if forward_keep_last:
                        df = keep_last_iteration(df)
                    forward_file_cache[path] = df
                df = df.copy()
            else:  # smoothed
                df = smoothed_file_cache.get(path)
                if df is None:
                    df_raw = _parse_residual_file(path)
                    if df_raw.empty:
                        smoothed_file_cache[path] = df_raw
                        continue
                    df = df_raw.copy()
                    sm_index = df.set_index(key_columns)
                    forward_combined = forward_group_merge.get(group_key)
                    if forward_combined is not None and not forward_combined.empty:
                        aligned = forward_combined.reindex(sm_index.index)
                        if aligned is not None:
                            zero_fill_cols = {"sigma"}
                            align_cols = [
                                col
                                for col in sm_index.columns
                                if col not in {"prefit", "postfit", "iter"}
                                and col in aligned.columns
                            ]
                            for col in align_cols:
                                mask = sm_index[col].isna()
                                if col in zero_fill_cols:
                                    mask |= sm_index[col] == 0
                                if mask.any():
                                    sm_index.loc[mask, col] = aligned.loc[mask, col]
                            df = sm_index.reset_index()
                    if smoothed_iteration is not None:
                        df = df[df["iter"] == smoothed_iteration]
                    smoothed_file_cache[path] = df
                df = df.copy()
        except Exception as exc:
            _warnings.warn(f"Failed to parse residuals from {path}: {exc}", RuntimeWarning, stacklevel=2)
            continue

        if df.empty:
            continue

        if trace_type == "forward":
            if forward_keep_last:
                df = keep_last_iteration(df)
        elif trace_type == "smoothed" and smoothed_iteration is not None:
            df = df[df["iter"] == smoothed_iteration]

        if df.empty:
            continue

        df = df.copy()
        df["trace_type"] = trace_type
        if include_source:
            df["source_path"] = str(path)
        frames.append(df.reset_index(drop=True))

    if not frames:
        return _pd.DataFrame(columns=base_columns)

    result = _pd.concat(frames, ignore_index=True)

    # Ensure expected columns exist even if ratios were absent from the inputs
    for col in base_columns:
        if col not in result.columns:
            result[col] = _pd.NA

    display_columns = [col for col in base_columns if col != "datetime"]
    result = result[display_columns]
    result = result.sort_values(["date", "time", "sat", "recv", "sig", "trace_type"]).reset_index(drop=True)
    return result


# ============================================================================
# Legacy/compatibility functions below this line
# ============================================================================


def _trace_extract(path_or_bytes, blk_name):
    trace_bytes = _gn_io.common.path2bytes(path_or_bytes)  # path2bytes passes through bytes

    begin = end = 0
    buf = []

    blk_begin = (f"+{blk_name}").encode()
    blk_end = (f"-{blk_name}").encode()

    while True:
        begin = trace_bytes.find(blk_begin, end)
        begin_full = trace_bytes.find(b"\n", begin)
        if begin == -1:
            break
        end = trace_bytes.find(blk_end, begin_full)

        blk_content = trace_bytes[begin_full + 1 : end]  # needs +1 not to start with '\n'
        blk_type = b"\t" + trace_bytes[begin + 1 : begin_full] + b"\n"  # needs +2 to remove ' +'
        blk_content_w_type = blk_type.join(blk_content.splitlines()) + blk_type
        buf.append(blk_content_w_type)

    content = b"".join(buf)
    if len(content) == 0:
        _logging.error(f'"{blk_name}" data not found')
        return None
    return content


def _read_trace_states(path_or_bytes, throw_if_nans=False):
    states = _trace_extract(path_or_bytes, blk_name="STATES")

    if states is None:
        return None

    if throw_if_nans:
        _gn_aux.throw_if_nans(states)

    df = _pd.read_csv(
        _BytesIO(states),
        delimiter="\t",
        usecols=[1, 2, 3, 4, 5, 6, 7, 8, 10],
        skipinitialspace=True,
        comment="#",
        header=None,
        names=["TIME", "TYPE", "SITE", "SAT", "NUM", "EST", "VAR", "ADJ", "BLK"],
        dtype={
            "TYPE": object,
            "SITE": object,
            "SAT": object,
            "NUM": int,
            "EST": float,
            "VAR": float,
            "ADJ": float,
            "BLK": object,
        },
        parse_dates=["TIME"],
    )

    if df.size == 0:
        _logging.error("STATES* blocks present but empty")
        return None

    df.TIME = _gn_datetime.datetime2j2000(df.TIME.values)

    empty_mask = df.TYPE.notna()  # dropping ONE type
    if (~empty_mask).sum() > 0:
        df = df[empty_mask]

    return df.set_index(["TIME", "SITE", "TYPE", "SAT", "NUM", "BLK"])


def _read_trace_residuals(path_or_bytes, it_max_only=True, throw_if_nans=False):
    residuals = _trace_extract(path_or_bytes, blk_name="RESIDUALS")

    if residuals is None:
        return None

    if throw_if_nans:
        _gn_aux.throw_if_nans(residuals)

    df = _pd.read_csv(
        _BytesIO(residuals),
        delimiter="\t",
        comment="#",
        header=None,
        usecols=[1, 2, 3, 4, 5, 6, 7, 8, 9, 11],
        skipinitialspace=True,
        na_values="NONE",
        names=["It", "TIME", "TYPE", "SAT", "SITE", "CODE", "PREFIT", "POSTFIT", "STD", "BLK"],
        dtype={
            "It": int,
            "TYPE": object,
            "SAT": object,
            "SITE": object,
            "CODE": object,
            "PREFIT": float,
            "POSTFIT": float,
            "STD": float,
            "BLK": object,
        },
        parse_dates=["TIME"],
    )
    if df.empty:  # blocks are present but empty
        _logging.error("RESIDUALS* blocks present but empty")
        return None

    df.TIME = _gn_datetime.datetime2j2000(df.TIME.values)

    if not it_max_only:
        return df.set_index(["TIME", "SITE", "TYPE", "CODE", "SAT", "BLK"])
    # to get max_ind values pandas >= 1.1 is required
    it_max_ind = df[["TIME", "It"]].groupby(["TIME"]).max().reset_index().values.tolist()
    return (
        df.set_index(["TIME", "It"])
        .loc[it_max_ind]
        .reset_index()
        .set_index(["TIME", "SITE", "TYPE", "SAT", "CODE", "It", "BLK"])
    )

def _find_trace(output_path: str) -> tuple:
    """Scans output path for TRACE files"""
    station_names = set()
    trace_paths = []
    _re_station_name = _re.compile(r"\-(.{4})\d+.TRACE")

    for file in _os.scandir(path=output_path):
        if file.path.endswith("TRACE"):
            station_names.add(_re_station_name.findall(file.path)[0])
            trace_paths.append(file.path)

    station_names = sorted(station_names)
    trace_paths = sorted(trace_paths)
    return station_names, trace_paths


def squeeze_column_names(df, delimiter=None):
    cols_frame = df.columns.to_frame(index=None).astype(str)
    if delimiter is not None:
        cols_frame.iloc[:, :-1] += delimiter
    df.columns = cols_frame.sum(axis=1)


def states2eda(states_df: _pd.DataFrame):
    df = states_df.rename(columns={"EST": "x", "VAR": "P", "ADJ": "dx"})
    states_mask = _gn_aux.df_quick_select(df, "BLK", "STATES", as_mask=True)
    eda_records = []
    if states_mask is not None:
        pos_trop_mask = _gn_aux.df_quick_select(df, "TYPE", ["REC_POS", "TROP"], as_mask=True)
        if pos_trop_mask is not None:
            df_pos_trop = df[states_mask & pos_trop_mask].unstack("NUM")
            squeeze_column_names(df_pos_trop)
            df_pos_trop.reset_index(level=["SITE", "TYPE", "TIME"], inplace=True)
            df_pos_trop.TIME = _gn_datetime.j20002datetime(df_pos_trop.TIME.values, as_datetime=True)
            df_pos_trop.rename(columns={"TYPE": "States", "Site": "Site", "TIME": "Epoch"})
            eda_records += df_pos_trop.to_dict("records")

        rclk_mask = _gn_aux.df_quick_select(df, "TYPE", "REC_CLOCK", as_mask=True)
        if rclk_mask is not None:
            df_rclk = df[states_mask & rclk_mask].unstack("NUM")
            squeeze_column_names(df_rclk)
            df_rclk.reset_index(level=["SITE", "TYPE", "TIME"], inplace=True)
            df_rclk.TIME = _gn_datetime.j20002datetime(df_rclk.TIME.values, as_datetime=True)
            df_rclk.rename(columns={"TYPE": "States", "Site": "Site", "TIME": "Epoch"})
            eda_records += df_rclk.to_dict("records")

    return eda_records


def residuals2eda(residuals_df: _pd.DataFrame):
    """ """
    b = (
        residuals_df.drop(columns="It")
        .rename(columns={"PREFIT": "Prefit", "POSTFIT": "Postfit", "STD": "Variance"})
        .unstack(["TYPE", "NUM"])
    )
    squeeze_column_names(b, delimiter="-")

    b.reset_index(["TIME", "SITE", "SAT"], inplace=True)
    b.TIME = _gn_datetime.j20002datetime(b.TIME.values, as_datetime=True)
    return b.rename(columns={"TIME": "Epoch", "SITE": "Site", "SAT": "Sat"}).to_dict("records")
