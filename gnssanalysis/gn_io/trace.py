"""TRACE file parser. Note the separate functions for values and residuals"""

import logging as _logging
import os as _os
import re as _re
from io import BytesIO as _BytesIO

import pandas as _pd
import numpy as _np

from .. import gn_aux as _gn_aux
from .. import gn_const as _gn_const
from .. import gn_datetime as _gn_datetime
from .. import gn_io as _gn_io


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


_RE_TRACE_HEAD = _re.compile(
    rb"station\s*\:\s*(.{4})\n\w+\s*\:\s*(.+|)\n\w+\s*\:\s*(.+|)\n\w+\s*\:\s*(\d)\n\w+\s*\:\s*(.+)"
)
_RE_TRACE_LC = _re.compile(rb"PDE\sform\sLC.+((?:\n.+)+)")
_RE_EL = _re.compile(rb"PDE-CS GPST\s+(?:\w+\s+)?(\d+)\s+(\d+(?:\.\d+)?)\s+([GREC]\d\d)\s+(\d+\.\d+)")
_RE_PDE_CS_SECTION = _re.compile(
    rb"\*-------- PDE cycle slip detection & repair --------\*[^\n]*\n\s*\nPDE-CS\s+GPST[^\n]+\n\s*\n((?:PDE-CS[^\n]+\n?)*)",
    _re.MULTILINE
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


# def _read_trace_LC(path_or_bytes):
#     '''Parses the LC combo block of the trace files producing
#      a single dataframe. WORK-IN-PROGRESS'''
#     # regex search string
#     if isinstance(path_or_bytes, str):
#         trace_content = _gn_io.common.path2bytes(path_or_bytes) # will accept .trace.Z also
#     else:
#         trace_content = path_or_bytes
#     trace_LC_list = _RE_TRACE_LC.findall(string=trace_content)
#     LC_bytes = b''.join(trace_LC_list)
#     LC_bytes = LC_bytes.replace(b'=',b'') #getting rif of '='

#     df_LC = _pd.read_csv(_BytesIO(LC_bytes),sep="\\s+",header=None,usecols=[1,2,4,6,8,9,10,11,12,13]).astype(
#         {
#             1: _np.int16, 2:_np.int32, 4: '<U3',
#             6: '<U1', 8: '<U4',
#             9: _np.float64, 10: '<U4', 11: _np.float64,
#             12: '<U4', 13: _np.float64
#         })

#     df_LC.columns = ['W','S','PRN','LP',8,9,10,11,12,13]
#     df_LC['time'] = _gn_datetime.gpsweeksec2datetime(gps_week = df_LC.W,
#                                                 tow = df_LC.S,
#                                                 as_j2000=True)
#     df_LC.drop(columns=['W','S'],inplace=True)

#     df1 = df_LC[['time','PRN','LP',8,9]]
#     df1.columns = ['time','PRN','LP','combo','value']

#     df2 = df_LC[['time','PRN','LP',10,11]]
#     df2.columns = ['time','PRN','LP','combo','value']

#     df3 = df_LC[['time','PRN','LP',12,13]]
#     df3.columns = ['time','PRN','LP','combo','value']

#     df_LC = _pd.concat([df1,df2,df3],axis=0)
#     return df_LC.set_index(['time'])

def _read_trace_el(path_or_bytes):
    "Get elevation angles for satellites from trace file"
    if isinstance(path_or_bytes, str):
        trace_content = _gn_io.common.path2bytes(path_or_bytes) # will accept .trace.Z also
    else:
        trace_content = path_or_bytes
    trace_EL_list = _RE_EL.findall(string=trace_content)

    el_df = _pd.DataFrame(trace_EL_list)
    if len(el_df) > 0:
        el_df[0] = el_df[0].astype(_np.int32)  # GPS week
        el_df[1] = el_df[1].astype(float)      # Time of week
        el_df[2] = el_df[2].str.decode("utf-8") # Satellite PRN
        el_df[3] = el_df[3].astype(float)      # Elevation
        el_df['TIME'] = _gn_datetime.gpsweeksec2datetime(gps_week=el_df[0], tow=el_df[1], as_j2000=True)
        el_df.drop(columns=[0,1],inplace=True)
        el_df.columns = ['PRN','el','TIME']
    else:
        el_df = el_df.reindex(columns=['PRN','el','TIME'])
    return el_df.set_index(['TIME'])


def _read_trace_pde_cs(path_or_bytes):
    """Extract PDE cycle slip detection & repair metrics from trace file.

    Returns a DataFrame with columns:
    - TIME: J2000 timestamp
    - PRN: Satellite ID
    - mode: Frequency mode (TRIP/DUAL/None)
    - el: Elevation angle (degrees)
    - lamw: Lambda wide-lane (meters)
    - gf12: Geometry-free L1-L2 (meters)
    - mw12: Melbourne-Wubbena L1-L2 (meters)
    - siggf: Sigma geometry-free (meters)
    - sigmw: Sigma Melbourne-Wubbena (meters)
    - lamew: Lambda extra-wide-lane (meters)
    - gf25: Geometry-free L2-L5 (meters)
    - mw25: Melbourne-Wubbena L2-L5 (meters)
    - vtpv: V-transpose P V statistic
    - val: Validation statistic
    - thres: Threshold value
    - N1, N2, N5: Ambiguity values (cycles)
    """
    if isinstance(path_or_bytes, str):
        trace_content = _gn_io.common.path2bytes(path_or_bytes)
    else:
        trace_content = path_or_bytes

    # Find all PDE-CS sections
    pde_cs_sections = _RE_PDE_CS_SECTION.findall(string=trace_content)

    if not pde_cs_sections:
        return _pd.DataFrame()

    # Combine all sections and parse line by line
    pde_cs_bytes = b'\n'.join(pde_cs_sections)
    lines = pde_cs_bytes.decode('utf-8').strip().split('\n')

    records = []
    for line in lines:
        parts = line.split()
        if len(parts) < 6:  # Minimum: PDE-CS GPST week sec prn el
            continue

        # Parse base fields
        idx = 0
        marker = parts[idx]  # PDE-CS
        idx += 1
        timesys = parts[idx]  # GPST
        idx += 1

        # Check for optional mode (TRIP/DUAL)
        mode = None
        if parts[idx] in ['TRIP', 'DUAL']:
            mode = parts[idx]
            idx += 1

        # Week and second
        try:
            week = int(parts[idx])
            sec = float(parts[idx + 1])
            idx += 2
        except (ValueError, IndexError):
            continue

        # PRN and elevation
        try:
            prn = parts[idx]
            el = float(parts[idx + 1])
            idx += 2
        except (ValueError, IndexError):
            continue

        # Check for special markers
        if idx < len(parts) and parts[idx].startswith('--'):
            # Skip lines with --low_elevation--, --single frequency--, etc.
            continue

        # Parse metrics if available
        record = {
            'week': week,
            'sec': sec,
            'prn': prn,
            'mode': mode,
            'el': el,
            'lamw': _np.nan,
            'gf12': _np.nan,
            'mw12': _np.nan,
            'siggf': _np.nan,
            'sigmw': _np.nan,
            'lamew': _np.nan,
            'gf25': _np.nan,
            'mw25': _np.nan,
            'vtpv': _np.nan,
            'val': _np.nan,
            'thres': _np.nan,
            'N1': _np.nan,
            'N2': _np.nan,
            'N5': _np.nan,
        }

        # Try to parse the metric fields (lamw through mw25)
        try:
            if idx < len(parts):
                record['lamw'] = float(parts[idx])
                idx += 1
            if idx < len(parts):
                record['gf12'] = float(parts[idx])
                idx += 1
            if idx < len(parts):
                record['mw12'] = float(parts[idx])
                idx += 1
            if idx < len(parts):
                record['siggf'] = float(parts[idx])
                idx += 1
            if idx < len(parts):
                record['sigmw'] = float(parts[idx]) if parts[idx] not in ['inf', '-inf'] else _np.nan
                idx += 1
            if idx < len(parts):
                record['lamew'] = float(parts[idx]) if parts[idx] not in ['inf', '-inf'] else _np.nan
                idx += 1
            if idx < len(parts):
                record['gf25'] = float(parts[idx])
                idx += 1
            if idx < len(parts):
                record['mw25'] = float(parts[idx]) if parts[idx] not in ['nan', '-nan'] else _np.nan
                idx += 1
        except (ValueError, IndexError):
            pass

        # Parse LC field: vtpv= X val= Y thres= Z
        while idx < len(parts):
            if parts[idx].startswith('vtpv='):
                try:
                    record['vtpv'] = float(parts[idx + 1])
                    idx += 2
                except (ValueError, IndexError):
                    idx += 1
            elif parts[idx].startswith('val='):
                try:
                    record['val'] = float(parts[idx + 1])
                    idx += 2
                except (ValueError, IndexError):
                    idx += 1
            elif parts[idx].startswith('thres='):
                try:
                    record['thres'] = float(parts[idx + 1])
                    idx += 2
                except (ValueError, IndexError):
                    idx += 1
            else:
                # Try parsing as N1, N2, N5 at the end
                try:
                    if _np.isnan(record['N1']):
                        record['N1'] = float(parts[idx])
                    elif _np.isnan(record['N2']):
                        record['N2'] = float(parts[idx])
                    elif _np.isnan(record['N5']):
                        record['N5'] = float(parts[idx])
                except ValueError:
                    pass
                idx += 1

        records.append(record)

    if not records:
        return _pd.DataFrame()

    # Create DataFrame
    df = _pd.DataFrame(records)

    # Convert GPS week/sec to J2000 time
    df['TIME'] = _gn_datetime.gpsweeksec2datetime(gps_week=df['week'], tow=df['sec'], as_j2000=True)

    # Drop week/sec and rename prn
    df = df.drop(columns=['week', 'sec'])
    df = df.rename(columns={'prn': 'PRN'})

    return df.set_index(['TIME', 'PRN'])


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
