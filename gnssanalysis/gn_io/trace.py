"""TRACE file parser. Note the separate functions for values and residuals"""

import logging as _logging
import os as _os
import re as _re
from io import BytesIO as _BytesIO, StringIO as _StringIO
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
            - value       : float64 — measurement value in meters (high precision for GNSS measurements)
    """
    datetime_strs = []
    sat_vals = []
    combo_type_vals = []
    code_type_vals = []
    combo_label_vals = []
    value_vals = []

    for ln in lines:
        if not isinstance(ln, str):
            continue
        line = ln.strip()
        if not line or line.startswith('*'):
            continue

        parts = line.split()
        if len(parts) < 7:
            continue

        dt_str = " ".join(parts[:2])
        idx = 2
        if idx >= len(parts) or parts[idx] != "sat=":
            continue
        idx += 1
        if idx >= len(parts):
            continue
        sat = parts[idx]
        idx += 1
        if idx >= len(parts):
            continue
        combo_type = parts[idx]
        idx += 1
        if idx >= len(parts):
            continue
        code_type = parts[idx]
        idx += 1
        if idx >= len(parts) or parts[idx] != "--":
            continue
        idx += 1

        while idx < len(parts):
            token = parts[idx]
            label = value_token = None

            if token.endswith("="):
                label = token[:-1]
                idx += 1
                if idx >= len(parts):
                    break
                value_token = parts[idx]
                idx += 1
            elif idx + 2 < len(parts) and parts[idx + 1] == "=":
                label = token
                value_token = parts[idx + 2]
                idx += 3
            else:
                idx += 1
                continue

            if not label:
                continue
            try:
                value = float(value_token)
            except (TypeError, ValueError):
                continue

            if not _np.isfinite(value):
                value = _np.nan

            datetime_strs.append(dt_str)
            sat_vals.append(sat)
            combo_type_vals.append(combo_type)
            code_type_vals.append(code_type)
            combo_label_vals.append(label)
            value_vals.append(value)

    if not datetime_strs:
        return _pd.DataFrame(
            columns=['datetime', 'sat', 'combo_type', 'code_type', 'combo_label', 'value']
        )

    df = _pd.DataFrame(
        {
            'datetime': _pd.to_datetime(datetime_strs, errors='coerce'),
            'sat': sat_vals,
            'combo_type': combo_type_vals,
            'code_type': code_type_vals,
            'combo_label': combo_label_vals,
            'value': _np.array(value_vals, dtype=_np.float64),
        }
    )
    df = df.dropna(subset=['datetime'])
    if df.empty:
        return _pd.DataFrame(
            columns=['datetime', 'sat', 'combo_type', 'code_type', 'combo_label', 'value']
        )

    df['value'] = df['value'].astype(_np.float64)
    for col in ['sat', 'combo_type', 'code_type', 'combo_label']:
        df[col] = _pd.Categorical(df[col])

    return df.reset_index(drop=True)



def parse_pde_cs(lines: _Iterable[str]) -> _pd.DataFrame:
    """Parse PDE-CS metrics in a streaming fashion to limit peak memory."""

    columns = [
        'datetime', 'sat', 'mode', 'flag',
        'el', 'lamw', 'gf12', 'mw12', 'siggf', 'sigmw',
        'lamew', 'gf25', 'mw25', 'vtpv', 'val', 'thres', 'N1', 'N2', 'N5'
    ]
    frames: list[_pd.DataFrame] = []
    chunk_size = 10000  # Reduced from 50000 to flush more frequently and reduce peak memory

    # Use separate lists for each column instead of tuples to reduce memory overhead
    date_list = []
    time_list = []
    sat_list = []
    mode_list = []
    flag_list = []
    el_list = []
    lamw_list = []
    gf12_list = []
    mw12_list = []
    siggf_list = []
    sigmw_list = []
    lamew_list = []
    gf25_list = []
    mw25_list = []
    vtpv_list = []
    val_list = []
    thres_list = []
    n1_list = []
    n2_list = []
    n5_list = []

    def _token_to_float(tok: _Optional[str]) -> float:
        if tok is None:
            return _np.nan
        tl = tok.lower()
        if tl in {"nan", "-nan", "inf", "-inf"}:
            return _np.nan
        try:
            return float(tok)
        except ValueError:
            return _np.nan

    def flush_chunk() -> None:
        if not date_list:
            return
        # Combine date and time lists into datetime strings
        datetime_strs = [f"{d} {t}" for d, t in zip(date_list, time_list)]
        df = _pd.DataFrame({
            'datetime': _pd.to_datetime(datetime_strs, errors='coerce'),
            'sat': sat_list,
            'mode': mode_list,
            'flag': flag_list,
            'el': _np.array(el_list, dtype=_np.float32),
            'lamw': _np.array(lamw_list, dtype=_np.float32),
            'gf12': _np.array(gf12_list, dtype=_np.float32),
            'mw12': _np.array(mw12_list, dtype=_np.float32),
            'siggf': _np.array(siggf_list, dtype=_np.float32),
            'sigmw': _np.array(sigmw_list, dtype=_np.float32),
            'lamew': _np.array(lamew_list, dtype=_np.float32),
            'gf25': _np.array(gf25_list, dtype=_np.float32),
            'mw25': _np.array(mw25_list, dtype=_np.float32),
            'vtpv': _np.array(vtpv_list, dtype=_np.float32),
            'val': _np.array(val_list, dtype=_np.float32),
            'thres': _np.array(thres_list, dtype=_np.float32),
            'N1': _np.array(n1_list, dtype=_np.float32),
            'N2': _np.array(n2_list, dtype=_np.float32),
            'N5': _np.array(n5_list, dtype=_np.float32),
        })
        date_list.clear()
        time_list.clear()
        sat_list.clear()
        mode_list.clear()
        flag_list.clear()
        el_list.clear()
        lamw_list.clear()
        gf12_list.clear()
        mw12_list.clear()
        siggf_list.clear()
        sigmw_list.clear()
        lamew_list.clear()
        gf25_list.clear()
        mw25_list.clear()
        vtpv_list.clear()
        val_list.clear()
        thres_list.clear()
        n1_list.clear()
        n2_list.clear()
        n5_list.clear()

        df = df.dropna(subset=['datetime'])
        if df.empty:
            return
        frames.append(df)

    for ln in lines:
        if not isinstance(ln, str):
            continue
        stripped = ln.strip()
        if not stripped or not stripped.startswith("PDE-CS"):
            continue
        if "epoch" in stripped and "prn" in stripped:
            continue

        tokens = stripped.split()
        if len(tokens) < 6 or tokens[1] != "GPST":
            continue

        idx = 2
        mode = None
        if tokens[idx] in {"TRIP", "DUAL"}:
            mode = tokens[idx]
            idx += 1

        if idx + 2 >= len(tokens):
            continue
        date_token = tokens[idx]
        time_token = tokens[idx + 1]
        idx += 2

        if idx >= len(tokens):
            continue
        sat = tokens[idx]
        idx += 1

        if idx >= len(tokens):
            continue
        el_val = _token_to_float(tokens[idx])
        idx += 1

        flag = None
        flag_match = _re.search(r"--\s*([^\-]+?)\s*--", stripped)
        if flag_match:
            flag = flag_match.group(1).strip().lower().replace(" ", "_")

        values = []
        while idx < len(tokens):
            tok = tokens[idx]
            if tok.startswith("vtpv=") or tok.startswith("val=") or tok.startswith("thres="):
                break
            if tok.startswith("--"):
                if not flag:
                    flag = tok.strip("-").replace(" ", "_").lower()
                idx += 1
                continue
            if tok.count("=") == 1:
                break
            values.append(_token_to_float(tok))
            idx += 1

        values += [_np.nan] * (8 - len(values))
        values = values[:8]

        vtpv = val = thres = _np.nan
        n_tokens: list[str] = []
        while idx < len(tokens):
            tok = tokens[idx]
            if tok.startswith("vtpv="):
                _, _, rest = tok.partition("=")
                if rest:
                    vtpv = _token_to_float(rest)
                elif idx + 1 < len(tokens):
                    idx += 1
                    vtpv = _token_to_float(tokens[idx])
            elif tok.startswith("val="):
                _, _, rest = tok.partition("=")
                if rest:
                    val = _token_to_float(rest)
                elif idx + 1 < len(tokens):
                    idx += 1
                    val = _token_to_float(tokens[idx])
            elif tok.startswith("thres="):
                _, _, rest = tok.partition("=")
                if rest:
                    thres = _token_to_float(rest)
                elif idx + 1 < len(tokens):
                    idx += 1
                    thres = _token_to_float(tokens[idx])
            elif tok.startswith("--"):
                if not flag:
                    flag = tok.strip("-").replace(" ", "_").lower()
            else:
                n_tokens.append(tok)
            idx += 1

        n_values = [_token_to_float(tok) for tok in n_tokens if tok]
        n_values += [_np.nan] * (3 - len(n_values))
        n_values = n_values[:3]

        # Append to individual lists instead of creating tuples
        date_list.append(date_token)
        time_list.append(time_token)
        sat_list.append(sat)
        mode_list.append(mode)
        flag_list.append(flag)
        el_list.append(el_val)
        lamw_list.append(values[0])
        gf12_list.append(values[1])
        mw12_list.append(values[2])
        siggf_list.append(values[3])
        sigmw_list.append(values[4])
        lamew_list.append(values[5])
        gf25_list.append(values[6])
        mw25_list.append(values[7])
        vtpv_list.append(vtpv)
        val_list.append(val)
        thres_list.append(thres)
        n1_list.append(n_values[0])
        n2_list.append(n_values[1])
        n5_list.append(n_values[2])

        if len(date_list) >= chunk_size:
            flush_chunk()

    flush_chunk()

    if not frames:
        return _pd.DataFrame(columns=columns)

    df = _pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=['datetime'])
    for col in ['sat', 'mode', 'flag']:
        df[col] = _pd.Categorical(df[col])
    return df[columns].reset_index(drop=True)


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


_OBS_STATUS_VALUES = frozenset({"OBSERVED", "MISSING", "CODE_ONLY", "PHASE_ONLY", "NOT_TRACKED"})
_OBS_RESULT_COLUMNS = [
    "datetime",
    "sat",
    "signal",
    "pseudorange",
    "carrier_phase",
    "snr",
    "elevation",
    "azimuth",
    "block",
    "status",
]
_OBS_FLOAT_COLUMNS = [
    "snr",
    "elevation",
    "azimuth",
]
_OBS_FLOAT64_COLUMNS = [
    "pseudorange",
    "carrier_phase",
]
_OBS_CHUNK_SIZE = 20000

# Regex for parsing obsRec lines - much faster than preprocessing loop
_OBS_REC_RE = _re.compile(
    r"""^obsRec:\s+
        epoch=\s*(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2}\.\d+)\s+
        sat=\s*(?P<sat>\S+)\s+
        sig=\s*(?P<sig>\S+)\s+
        P=\s*(?P<P>\S+)\s+
        L=\s*(?P<L>\S+)\s+
        S=\s*(?P<S>\S+)\s+
        el=\s*(?P<el>\S+)\s+
        az=\s*(?P<az>\S+)\s+
        block=\s*(?P<block>.+?)\s+
        status=\s*(?P<status>\S+)\s*$
    """,
    _re.VERBOSE,
)


def _empty_observation_df() -> _pd.DataFrame:
    return _pd.DataFrame(columns=_OBS_RESULT_COLUMNS)


def _is_observation_line(line: str) -> bool:
    """
    Fast structural checks to decide if a line carries observation data.
    New obsRec format: obsRec: epoch= ... status= OBSERVED
    """
    if not line or len(line) < 40:
        return False
    if not line.startswith("obsRec:"):
        return False
    # Quick check for status at the end
    return any(status in line for status in _OBS_STATUS_VALUES)


def _parse_observation_chunk(chunk_lines) -> _pd.DataFrame:
    """
    Materialize a batch of observation lines into a typed DataFrame.
    Uses compiled regex for fast extraction of obsRec format.
    """
    if not chunk_lines:
        return _empty_observation_df()

    # Parse all lines with compiled regex (very fast - single pass, C implementation)
    records = []
    for line in chunk_lines:
        m = _OBS_REC_RE.match(line)
        if not m:
            continue
        gd = m.groupdict()
        records.append({
            "date": gd["date"],
            "time": gd["time"],
            "sat": gd["sat"].strip(),
            "signal": gd["sig"].strip(),
            "pseudorange": _to_float_or_nan(gd["P"]),
            "carrier_phase": _to_float_or_nan(gd["L"]),
            "snr": _to_float_or_nan(gd["S"]),
            "elevation": _to_float_or_nan(gd["el"]),
            "azimuth": _to_float_or_nan(gd["az"]),
            "block": gd["block"].strip(),
            "status": gd["status"].strip(),
        })

    if not records:
        return _empty_observation_df()

    # Build DataFrame from records (fast for moderate chunk sizes)
    chunk = _pd.DataFrame.from_records(records)

    # Enforce expected statuses
    chunk = chunk[chunk["status"].isin(_OBS_STATUS_VALUES)]
    if chunk.empty:
        return _empty_observation_df()

    # Build datetimes in bulk (vectorized operation)
    chunk["datetime"] = _pd.to_datetime(
        chunk["date"] + " " + chunk["time"],
        errors="coerce",
    )
    chunk.drop(columns=["date", "time"], inplace=True)
    chunk = chunk.dropna(subset=["datetime"])
    if chunk.empty:
        return _empty_observation_df()

    # Convert float columns - float32 for smaller values, float64 for high-precision measurements
    chunk = chunk.astype({col: _np.float32 for col in _OBS_FLOAT_COLUMNS}, copy=False)
    chunk = chunk.astype({col: _np.float64 for col in _OBS_FLOAT64_COLUMNS}, copy=False)
    return chunk[_OBS_RESULT_COLUMNS]


def parse_observations(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse observation output lines from station TRACE files (obsRec format).

    Handles three observation statuses:
    - OBSERVED: Valid observations with pseudorange, carrier phase, and SNR values
    - MISSING: Satellite is tracked but specific signal is missing (some signals present)
    - NOT_TRACKED: Satellite is above elevation mask but not tracked at all (no signals)

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        Columns:
            - datetime      : pd.Timestamp — observation timestamp
            - sat           : str — satellite identifier (e.g. "G18", "R06")
            - signal        : str — signal code (e.g. "L1C", "L2S", "L2P")
            - pseudorange   : float64 — pseudorange measurement (m), NaN if not observed
            - carrier_phase : float64 — carrier phase measurement (cycles), NaN if not observed
            - snr           : float32 — signal-to-noise ratio (dB-Hz), NaN if not observed
            - elevation     : float32 — satellite elevation angle (degrees)
            - azimuth       : float32 — satellite azimuth angle (degrees)
            - block         : str — satellite block type (e.g. "GPS-IIIA", "GLO-M")
            - status        : str — observation status ("OBSERVED", "MISSING", "NOT_TRACKED")

    Examples
    --------
    >>> with open("station.TRACE") as f:
    ...     df = parse_observations(f)
    >>> observed = df[df['status'] == 'OBSERVED']
    >>> missing = df[df['status'] == 'MISSING']
    """
    chunk_lines = []
    frames = []
    append_frame = frames.append

    for ln in lines:
        if not isinstance(ln, str):
            continue
        line = ln.strip()
        if not _is_observation_line(line):
            continue
        chunk_lines.append(line)
        if len(chunk_lines) >= _OBS_CHUNK_SIZE:
            chunk_df = _parse_observation_chunk(chunk_lines)
            if not chunk_df.empty:
                append_frame(chunk_df)
            chunk_lines.clear()

    if chunk_lines:
        chunk_df = _parse_observation_chunk(chunk_lines)
        if not chunk_df.empty:
            append_frame(chunk_df)
        chunk_lines.clear()

    if not frames:
        return _empty_observation_df()

    df = _pd.concat(frames, ignore_index=True)
    if df.empty:
        return _empty_observation_df()

    for col in ['sat', 'signal', 'block', 'status']:
        df[col] = _pd.Categorical(df[col])

    return df.reset_index(drop=True)


def parse_detslp(lines: _Iterable[str]) -> _pd.DataFrame:
    """
    Parse cycle slip detection blocks (detslp_mw, detslp_gf, detslp_ll) from station TRACE files.

    These blocks contain cycle slip detection results from Melbourne-Wübbena (MW),
    geometry-free (GF), and loss-of-lock indicator (LL) tests.

    Parameters
    ----------
    lines : Iterable[str]
        Iterable of text lines (e.g. from open(file))

    Returns
    -------
    pd.DataFrame
        Columns:
            - datetime     : pd.Timestamp — epoch timestamp
            - sat          : str — satellite identifier
            - detector     : str — detection method (mw, gf, ll)
            - slip_detected: bool — True if slip was detected
            - mw0          : float — MW value at epoch 0 (mw only)
            - mw1          : float — MW value at epoch 1 (mw only)
            - gf0          : float — GF value at epoch 0 (gf only)
            - gf1          : float — GF value at epoch 1 (gf only)
            - f            : str — frequency identifier (ll only)
    """
    records = []

    for ln in lines:
        if not isinstance(ln, str):
            continue
        line = ln.strip()
        if not line or not line.startswith('detslp_'):
            continue

        # Skip summary lines (n=XX)
        if 'n=' in line and 'epoch=' not in line:
            continue

        # Parse detector type
        if line.startswith('detslp_mw:'):
            detector = 'mw'
            rest = line[10:].strip()
        elif line.startswith('detslp_gf:'):
            detector = 'gf'
            rest = line[10:].strip()
        elif line.startswith('detslp_ll:'):
            detector = 'll'
            rest = line[10:].strip()
        else:
            continue

        # Check for slip detected line
        is_slip = 'slip detected' in rest
        if is_slip:
            rest = rest.replace('slip detected:', '').strip()

        # Parse key=value pairs
        # Special handling for epoch which contains space-separated date and time
        parts = {}
        tokens = rest.split()
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if '=' in token:
                key, val = token.split('=', 1)
                # For epoch, combine with next token (time component)
                if key == 'epoch' and i + 1 < len(tokens) and '=' not in tokens[i + 1]:
                    val = val + ' ' + tokens[i + 1]
                    i += 1
                parts[key] = val
            i += 1

        # Must have epoch and sat
        if 'epoch' not in parts or 'sat' not in parts:
            continue

        epoch_str = parts.get('epoch', '')
        sat = parts.get('sat', '')

        try:
            epoch_dt = _pd.to_datetime(epoch_str, errors='coerce')
        except Exception:
            epoch_dt = _pd.NaT

        # Parse detector-specific values
        if detector == 'mw':
            mw0 = _to_float_or_nan(parts.get('mw0', 'nan'))
            mw1 = _to_float_or_nan(parts.get('mw1', 'nan'))
            records.append({
                'datetime': epoch_dt,
                'sat': sat,
                'detector': detector,
                'slip_detected': is_slip,
                'mw0': mw0,
                'mw1': mw1,
                'gf0': _np.nan,
                'gf1': _np.nan,
                'f': None,
            })
        elif detector == 'gf':
            gf0 = _to_float_or_nan(parts.get('gf0', 'nan'))
            gf1 = _to_float_or_nan(parts.get('gf1', 'nan'))
            records.append({
                'datetime': epoch_dt,
                'sat': sat,
                'detector': detector,
                'slip_detected': is_slip,
                'mw0': _np.nan,
                'mw1': _np.nan,
                'gf0': gf0,
                'gf1': gf1,
                'f': None,
            })
        elif detector == 'll':
            f_val = parts.get('f', None)
            records.append({
                'datetime': epoch_dt,
                'sat': sat,
                'detector': detector,
                'slip_detected': is_slip,
                'mw0': _np.nan,
                'mw1': _np.nan,
                'gf0': _np.nan,
                'gf1': _np.nan,
                'f': f_val,
            })

    if not records:
        return _pd.DataFrame(columns=[
            'datetime', 'sat', 'detector', 'slip_detected',
            'mw0', 'mw1', 'gf0', 'gf1', 'f'
        ])

    df = _pd.DataFrame.from_records(records)

    # Convert types
    df['slip_detected'] = df['slip_detected'].astype(bool)
    for col in ['sat', 'detector', 'f']:
        if col in df.columns:
            df[col] = _pd.Categorical(df[col])

    # Deduplicate: when slip is detected, we get both the regular line and "slip detected" line
    # Keep only the slip_detected=True version when duplicates exist
    # Group by (datetime, sat, detector) and keep the row with slip_detected=True if it exists
    df = df.sort_values('slip_detected', ascending=False)  # True comes before False
    df = df.drop_duplicates(subset=['datetime', 'sat', 'detector'], keep='first')
    df = df.sort_values(['datetime', 'sat', 'detector']).reset_index(drop=True)

    return df


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
