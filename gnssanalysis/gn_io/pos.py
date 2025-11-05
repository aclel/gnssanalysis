"""Ginan .POS file parser for station position time series."""

import pandas as _pd
from pathlib import Path as _Path
from typing import Iterable as _Iterable, Optional as _Optional
import warnings as _warnings


def parse_pos(path_or_lines, include_header_info: bool = False) -> _pd.DataFrame:
    """
    Parse Ginan .POS file (station position time series).

    Handles both forward and smoothed .POS files. The format includes a header
    with reference frame information and field descriptions, followed by
    whitespace-separated position data.

    Parameters
    ----------
    path_or_lines : str, Path, or Iterable[str]
        Path to .POS file or iterable of lines from the file
    include_header_info : bool, default False
        If True, attach header metadata as DataFrame attributes

    Returns
    -------
    pd.DataFrame
        Columns:
            - datetime       : pd.Timestamp — GPS time of position epoch
            - decimal_year   : float — Decimal year of position epoch
            - X              : float — X coordinate (m, specified reference frame)
            - Y              : float — Y coordinate (m, specified reference frame)
            - Z              : float — Z coordinate (m, specified reference frame)
            - Sx             : float — Sigma of X position (m)
            - Sy             : float — Sigma of Y position (m)
            - Sz             : float — Sigma of Z position (m)
            - Rxy            : float — Correlation between X and Y
            - Rxz            : float — Correlation between X and Z
            - Ryz            : float — Correlation between Y and Z
            - Nlat           : float — North latitude (degrees, WGS-84)
            - Elong          : float — East longitude (degrees, WGS-84)
            - Height         : float — Height above WGS-84 ellipsoid (m)
            - dN             : float — North offset from reference (m)
            - dE             : float — East offset from reference (m)
            - dU             : float — Up offset from reference (m)
            - Sn             : float — Sigma of dN (m)
            - Se             : float — Sigma of dE (m)
            - Su             : float — Sigma of dU (m)
            - Rne            : float — Correlation between dN and dE
            - Rnu            : float — Correlation between dN and dU
            - Reu            : float — Correlation between dE and dU
            - soln           : str — Solution type (e.g., "ginan")

        If include_header_info=True, the following attributes are attached:
            - station_id     : 4-character station ID
            - reference_frame: Reference frame name (e.g., "IGS20")
            - format_version : Format version string
            - first_epoch    : First epoch timestamp
            - xyz_ref        : XYZ reference position (list of 3 floats)
            - neu_ref        : NEU reference position (list of 3 floats)
            - source_path    : Path to source file (if path was provided)

    Examples
    --------
    >>> df = parse_pos("TONG00TON_R_20252780000_01D_30S_MO.rnx_smoothed.POS")
    >>> print(df[['datetime', 'X', 'Y', 'Z', 'dN', 'dE', 'dU']].head())
    """
    # Determine if input is a path or lines
    if isinstance(path_or_lines, (str, _Path)):
        path = _Path(path_or_lines)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        source_path = str(path)
    else:
        lines = list(path_or_lines)
        source_path = None

    # Parse header and extract metadata
    header_info = {}
    data_start_idx = None

    for i, line in enumerate(lines):
        line = line.strip()

        # Extract header metadata
        if line.startswith('PBO Station Position Time Series. Reference Frame :'):
            header_info['reference_frame'] = line.split(':')[1].strip()
        elif line.startswith('Format Version:'):
            header_info['format_version'] = line.split(':')[1].strip()
        elif line.startswith('4-character ID:'):
            header_info['station_id'] = line.split(':')[1].strip()
        elif line.startswith('First Epoch'):
            header_info['first_epoch'] = line.split(':')[1].strip()
        elif line.startswith('XYZ Reference position :'):
            parts = line.split(':')[1].strip().split()
            header_info['xyz_ref'] = [float(parts[0]), float(parts[1]), float(parts[2])]
            if len(parts) > 3:
                header_info['xyz_ref_frame'] = parts[3].strip('()')
        elif line.startswith('NEU Reference position :'):
            parts = line.split(':')[1].strip().split()
            header_info['neu_ref'] = [float(parts[0]), float(parts[1]), float(parts[2])]
            if len(parts) > 3:
                header_info['neu_ref_frame'] = parts[3].strip('()')

        # Find start of data (line starting with '*')
        if line.startswith('*YYYY-MM-DD'):
            data_start_idx = i + 1
            break

    if data_start_idx is None:
        _warnings.warn("Could not find data section in .POS file", RuntimeWarning)
        return _pd.DataFrame()

    # Column names based on the header format
    columns = [
        'datetime_str', 'decimal_year', 'X', 'Y', 'Z',
        'Sx', 'Sy', 'Sz', 'Rxy', 'Rxz', 'Ryz',
        'Nlat', 'Elong', 'Height',
        'dN', 'dE', 'dU',
        'Sn', 'Se', 'Su',
        'Rne', 'Rnu', 'Reu',
        'soln'
    ]

    # Parse data section
    data_lines = [line.strip() for line in lines[data_start_idx:] if line.strip()]

    if not data_lines:
        return _pd.DataFrame(columns=['datetime'] + columns[1:])

    # Read data using pandas
    from io import StringIO
    data_str = '\n'.join(data_lines)
    df = _pd.read_csv(
        StringIO(data_str),
        sep=r'\s+',
        names=columns,
        comment='#',
        na_values=['nan', '-nan', 'inf', '-inf'],
    )

    # Convert datetime string to pandas datetime
    df['datetime'] = _pd.to_datetime(df['datetime_str'], errors='coerce')
    df = df.drop(columns=['datetime_str'])

    # Reorder columns to put datetime first
    cols = ['datetime'] + [col for col in df.columns if col != 'datetime']
    df = df[cols]

    # Convert soln to categorical
    df['soln'] = _pd.Categorical(df['soln'])

    # Attach header info as attributes if requested
    if include_header_info:
        for key, value in header_info.items():
            df.attrs[key] = value
        if source_path:
            df.attrs['source_path'] = source_path

    return df


def parse_pos_files(
    paths: _Iterable[_Path],
    strategy: str = "auto",
    include_header_info: bool = False,
) -> _pd.DataFrame:
    """
    Parse multiple Ginan .POS files (forward and/or smoothed).

    Parameters
    ----------
    paths : Iterable[Path or str]
        Collection of .POS files (forward and/or smoothed). Files are grouped by
        their base name (with the ``_smoothed`` suffix removed) so that forward and
        smoothed pairs can be resolved automatically.
    strategy : {"auto", "smoothed", "forward", "both"}, default "auto"
        Selection strategy for choosing between smoothed and forward positions.
        - "auto": prefer smoothed positions, fall back to forward when smoothed missing.
        - "smoothed": use smoothed positions, fall back to forward with a warning.
        - "forward": use forward positions, fall back to smoothed with a warning.
        - "both": include both smoothed and forward positions.
    include_header_info : bool, default False
        If True, attach header metadata as DataFrame attributes

    Returns
    -------
    pd.DataFrame
        Combined position time series with an additional column:
            - pos_type : str — "smoothed" or "forward"
        All other columns match parse_pos() output.

    Examples
    --------
    >>> from pathlib import Path
    >>> paths = list(Path("outputs").glob("**/*.POS"))
    >>> df = parse_pos_files(paths, strategy="auto")
    >>> print(df.groupby('pos_type').size())
    """
    strategy = strategy.lower()
    valid_strategies = {"auto", "smoothed", "forward", "both"}
    if strategy not in valid_strategies:
        raise ValueError(
            f"Invalid strategy '{strategy}'. Expected one of {sorted(valid_strategies)}."
        )

    paths = list(paths or [])
    if not paths:
        return _pd.DataFrame()

    # Group files by base name (removing _smoothed suffix)
    grouped = {}
    for raw in paths:
        path = _Path(raw)
        if not path.exists():
            _warnings.warn(f".POS file not found: {path}", RuntimeWarning, stacklevel=2)
            continue

        stem_lower = path.stem.lower()
        is_smoothed = "_smoothed" in stem_lower
        base_stem = path.stem.replace("_smoothed", "")
        key = (base_stem, path.parent)
        entry = grouped.setdefault(key, {"smoothed": [], "forward": []})
        entry["smoothed" if is_smoothed else "forward"].append(path)

    # Select files based on strategy
    selected = []
    for (base_stem, parent), entry in grouped.items():
        smoothed_files = entry["smoothed"]
        forward_files = entry["forward"]

        def _warn_fallback(missing: str) -> None:
            available = "forward" if missing == "smoothed" else "smoothed"
            if entry[available]:
                msg = (
                    f"No {missing} positions found for '{base_stem}' in {parent}; "
                    f"using {available} positions instead."
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

    # Parse selected files
    frames = []
    for path, pos_type in selected:
        try:
            df = parse_pos(path, include_header_info=include_header_info)
            if df.empty:
                continue
            df['pos_type'] = pos_type
            frames.append(df)
        except Exception as exc:
            _warnings.warn(
                f"Failed to parse positions from {path}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue

    if not frames:
        return _pd.DataFrame()

    result = _pd.concat(frames, ignore_index=True)
    result['pos_type'] = _pd.Categorical(result['pos_type'])
    result = result.sort_values(['datetime', 'pos_type']).reset_index(drop=True)

    return result
