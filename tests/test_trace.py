import tempfile
import unittest
from pathlib import Path
import textwrap
import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np

from gnssanalysis.gn_io.trace import (
    parse_pde_cs,
    parse_lc,
    parse_residuals,
    parse_residual_lines,
    parse_large_errors,
    parse_ambiguity_resets,
    parse_elevation,
)
from test_datasets.trace_test_data import (
    trace_pde_cs_sample,
    trace_no_pde_cs,
    trace_lc_sample,
    trace_no_lc,
    trace_residual_lines_sample,
    trace_large_errors_sample,
    trace_ambiguity_resets_sample,
)


class TestParsePdeCs(unittest.TestCase):
    """Tests for parse_pde_cs function"""

    def test_parse_pde_cs_basic(self):
        """Test basic reading of PDE-CS data"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(len(df), 0, "DataFrame should contain PDE-CS records")

        # Check for expected columns
        expected_columns = [
            "datetime",
            "sat",
            "mode",
            "flag",
            "el",
            "lamw",
            "gf12",
            "mw12",
            "siggf",
            "sigmw",
            "lamew",
            "gf25",
            "mw25",
            "vtpv",
            "val",
            "thres",
            "N1",
            "N2",
            "N5",
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected column '{col}' not found")

    def test_parse_pde_cs_column_types(self):
        """Test that columns have the correct data types"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # datetime should be datetime64
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # sat should be object (string)
        self.assertEqual(df["sat"].dtype, object)

        # mode should be object (string or None)
        self.assertEqual(df["mode"].dtype, object)

        # flag should be object (string or None)
        self.assertEqual(df["flag"].dtype, object)

        # Numeric columns should be float
        numeric_cols = [
            "el",
            "lamw",
            "gf12",
            "mw12",
            "siggf",
            "sigmw",
            "lamew",
            "gf25",
            "mw25",
            "vtpv",
            "val",
            "thres",
            "N1",
            "N2",
            "N5",
        ]
        for col in numeric_cols:
            self.assertTrue(
                np.issubdtype(df[col].dtype, np.floating),
                f"Column '{col}' should be float type",
            )

    def test_parse_pde_cs_mode_values(self):
        """Test that mode column contains expected values"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # mode should be None, 'TRIP', or 'DUAL'
        unique_modes = df["mode"].dropna().unique()
        valid_modes = ["TRIP", "DUAL"]
        for mode in unique_modes:
            self.assertIn(mode, valid_modes, f"Unexpected mode value: {mode}")

        # Verify we have both TRIP and DUAL modes in the test data
        self.assertIn("TRIP", unique_modes)
        self.assertIn("DUAL", unique_modes)

    def test_parse_pde_cs_sat_format(self):
        """Test that sat values have the expected format"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # sat should be in format like G01, E02, R03, etc.
        sats = df["sat"].unique()
        self.assertGreater(len(sats), 0, "Should have sat values")

        # Check format: first char is constellation, followed by 2 digits
        for sat in sats:
            self.assertEqual(len(sat), 3, f"sat '{sat}' should be 3 characters")
            self.assertIn(
                sat[0], ["G", "E", "R", "C"], f"sat '{sat}' should start with G/E/R/C"
            )
            self.assertTrue(
                sat[1:].isdigit(), f"sat '{sat}' last 2 chars should be digits"
            )

    def test_parse_pde_cs_elevation_range(self):
        """Test that elevation values are in reasonable range"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # Elevation should be between 0 and 90 degrees
        self.assertTrue((df["el"] >= 0).all(), "Elevation should be >= 0")
        self.assertTrue((df["el"] <= 90).all(), "Elevation should be <= 90")

    def test_parse_pde_cs_datetime(self):
        """Test that datetime column is properly set"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # Check datetime is set
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # Check we have multiple time epochs
        unique_times = df["datetime"].unique()
        self.assertGreater(len(unique_times), 1, "Should have multiple time epochs")

    def test_parse_pde_cs_special_values(self):
        """Test handling of special values like inf, -inf, nan"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # All finite columns should remain finite after parsing
        float_cols = df.select_dtypes(include=[np.floating])
        self.assertFalse(
            np.isinf(float_cols).to_numpy().any(),
            "Floating columns should not contain +/-inf values",
        )

        # E02 lines contain explicit 'inf'/'nan' markers that must become NaN
        e02_rows = df[df["sat"] == "E02"]
        self.assertGreater(len(e02_rows), 0, "Expected E02 rows in PDE-CS sample")
        self.assertTrue(
            e02_rows["sigmw"].isna().all(),
            "sigmw values tagged as 'inf' should convert to NaN",
        )
        self.assertTrue(
            e02_rows["mw25"].isna().all(),
            "mw25 values tagged as 'nan' should convert to NaN",
        )

        # R11 rows carry '-nan' validation stats that should become NaN
        r11_rows = df[df["sat"] == "R11"]
        self.assertGreater(len(r11_rows), 0, "Expected R11 rows in PDE-CS sample")
        self.assertTrue(r11_rows["vtpv"].isna().all())
        self.assertTrue(r11_rows["val"].isna().all())

    def test_parse_pde_cs_empty_input(self):
        """Test behavior with content that doesn't contain PDE-CS section"""
        df = parse_pde_cs(trace_no_pde_cs.decode().splitlines())

        # Should return empty DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0, "Should return empty DataFrame for no PDE-CS data")

    def test_parse_pde_cs_trip_mode_fields(self):
        """Test that TRIP mode records have expected fields populated"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # Filter for TRIP mode records
        trip_records = df[df["mode"] == "TRIP"]
        self.assertGreater(len(trip_records), 0, "Should have TRIP mode records")

        # TRIP mode should produce extended metrics populated with real numbers
        for col in ["lamew", "gf25"]:
            self.assertTrue(
                trip_records[col].notna().any(),
                f"{col} should be populated for at least one TRIP record",
            )

    def test_parse_pde_cs_dual_mode_fields(self):
        """Test that DUAL mode records have expected fields"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # Filter for DUAL mode records
        dual_records = df[df["mode"] == "DUAL"]
        self.assertGreater(len(dual_records), 0, "Should have DUAL mode records")

        # DUAL mode records exist and have basic fields
        self.assertTrue((dual_records["el"] > 0).all())
        self.assertTrue((dual_records["lamw"] > 0).all())

        # DUAL mode does not report the TRIP-only metrics
        for col in ["lamew", "gf25", "mw25"]:
            self.assertTrue(
                dual_records[col].isna().all(),
                f"{col} should remain NaN for DUAL mode records",
            )

    def test_parse_pde_cs_flagged_records(self):
        """Ensure low elevation and single-frequency PRNs are retained with flags"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        flagged = df[df["flag"].notna()]
        self.assertGreater(len(flagged), 0, "Expected flagged PDE-CS records")

        expected_flags = {"low_elevation", "single_frequency"}
        self.assertTrue(
            set(flagged["flag"]).issubset(expected_flags),
            "Unexpected flag values present",
        )

        flagged_prns = {"E27", "G31", "R22", "E25", "R10"}
        for prn in flagged_prns:
            self.assertGreater(
                len(flagged[flagged["sat"] == prn]),
                0,
                f"{prn} should appear as a flagged record",
            )

        numeric_cols = [
            "lamw",
            "gf12",
            "mw12",
            "siggf",
            "sigmw",
            "lamew",
            "gf25",
            "mw25",
            "vtpv",
            "val",
            "thres",
            "N1",
            "N2",
            "N5",
        ]
        flagged_numeric = flagged[numeric_cols]
        self.assertTrue(
            flagged_numeric.isna().all().all(),
            "Flagged records should have NaN metric values",
        )

    def test_parse_pde_cs_specific_satellite(self):
        """Test parsing of a specific satellite record"""
        df = parse_pde_cs(trace_pde_cs_sample.decode().splitlines())

        # Check if G18 exists in the data
        g18_data = df[df["sat"] == "G18"]
        self.assertGreater(len(g18_data), 0, "Should have G18 data")
        # G18 should be in TRIP mode
        self.assertTrue((g18_data["mode"] == "TRIP").any())

        # Should have elevation values around 20 degrees
        self.assertTrue((g18_data["el"] >= 20).any())
        self.assertTrue((g18_data["el"] <= 21).any())


class TestParseLc(unittest.TestCase):
    """Tests for parse_lc function in wide-column format"""

    @staticmethod
    def _parse():
        return parse_lc(trace_lc_sample.decode().splitlines())

    def test_parse_lc_basic(self):
        df = self._parse()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0, "LC DataFrame should not be empty")
        self.assertIn("datetime", df.columns)
        self.assertIn("sat", df.columns)

    def test_parse_lc_column_types(self):
        df = self._parse()
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))
        self.assertIsInstance(df["sat"].dtype, CategoricalDtype)
        numeric_cols = [col for col in df.columns if col not in {"datetime", "sat"}]
        self.assertTrue(
            all(df[col].dtype == np.float32 for col in numeric_cols),
            "All LC value columns should be float32",
        )

    def test_expected_columns_present(self):
        df = self._parse()
        expected_columns = [
            "zd_L_L1",
            "mp_P_mp1",
            "gf_L_gf12",
            "mw_L_mw12",
            "wl_L_wl12",
            "if_L_if12",
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected LC column '{col}' missing")

    def test_code_type_columns(self):
        df = self._parse()
        mp_columns = [col for col in df.columns if col.startswith("mp_")]
        self.assertTrue(mp_columns, "Expected multipath columns")
        self.assertTrue(
            all("_P_" in col for col in mp_columns),
            "Multipath columns should be associated with code type P",
        )
        phase_columns = [col for col in df.columns if "_L_" in col]
        self.assertTrue(phase_columns, "Expected phase (L) columns")

    def test_specific_values(self):
        df = self._parse()
        row = df[
            (df["sat"] == "G02")
            & (df["datetime"] == pd.Timestamp("2019-01-01 00:00:30"))
        ].iloc[0]
        self.assertAlmostEqual(row["zd_L_L1"], 22093585.6788, places=3)
        self.assertEqual(row["zd_L_L5"], 0.0)
        self.assertAlmostEqual(row["mp_P_mp1"], -26.3576, places=3)

    def test_parse_lc_empty_input(self):
        df = parse_lc(trace_no_lc.decode().splitlines())
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
class TestParseResiduals(unittest.TestCase):
    """Tests for parse_residuals helper"""

    FORWARD_TRACE = textwrap.dedent(
        """
        Network header line
        +RESIDUALS/PPP
        %  0 2025-10-05 00:00:00.00 CODE_MEAS G01 STAT L1C -1.2300  0.1000 0.5000 P-L1C
        %  1 2025-10-05 00:00:00.00 CODE_MEAS G01 STAT L1C -0.8000  0.0500 0.4000 P-L1C
        %  0 2025-10-05 00:00:30.00 PHAS_MEAS G02 OTHR L1W  2.0000  0.0000 0.0200 L-L1W
        -RESIDUALS/PPP
        """
    ).strip()

    SMOOTHED_TRACE = textwrap.dedent(
        """
        +RESIDUALS/PPP
        % -1 2025-10-05 00:00:00.00 CODE_MEAS G01 STAT L1C -0.3000  0.0200 0.0000 P-L1C
        % -1 2025-10-05 00:00:30.00 PHAS_MEAS G02 OTHR L1W  1.7000  0.0000 0.0000 L-L1W
        -RESIDUALS/PPP
        """
    ).strip()

    FORWARD_TRACE_MULTI = textwrap.dedent(
        """
        +RESIDUALS/PPP
        %  0 2025-10-05 00:00:00.00 CODE_MEAS G06 HOB2 L1W -5.74025971 0.06586412 0.3449291 P-L1W
        %  0 2025-10-05 00:00:00.00 CODE_MEAS G06 HOB2 L2W -9.63267831 -0.04041255 0.3449291 P-L2W
        %  0 2025-10-05 00:00:00.00 PHAS_MEAS G06 HOB2 L1W 6.21998206 0.00000000 0.0034493 L-L1W
        %  0 2025-10-05 00:00:00.00 PHAS_MEAS G06 HOB2 L2W 10.04347349 0.00000000 0.0034493 L-L2W
        %  0 2025-10-05 00:00:30.00 CODE_MEAS G06 HOB2 L1W 0.79316409 -0.03955825 0.3448066 P-L1W
        %  0 2025-10-05 00:00:30.00 CODE_MEAS G06 HOB2 L2W 0.85894545 -0.01656954 0.3448066 P-L2W
        %  0 2025-10-05 00:00:30.00 PHAS_MEAS G06 HOB2 L1W 0.87663820 0.00084738 0.0034481 L-L1W
        %  0 2025-10-05 00:00:30.00 PHAS_MEAS G06 HOB2 L2W 0.87129878 -0.00051872 0.0034481 L-L2W
        %  0 2025-10-05 00:01:00.00 CODE_MEAS G06 HOB2 L1W -0.12997923 0.10875943 0.3446935 P-L1W
        %  0 2025-10-05 00:01:00.00 CODE_MEAS G06 HOB2 L2W -0.35699512 -0.07082514 0.3446935 P-L2W
        %  0 2025-10-05 00:01:00.00 PHAS_MEAS G06 HOB2 L1W 1.23456789 0.00000000 0.0034356 L-L1W
        %  0 2025-10-05 00:01:00.00 PHAS_MEAS G06 HOB2 L2W 1.11111111 0.00000000 0.0034356 L-L2W
        -RESIDUALS/PPP
        """
    ).strip()

    SMOOTHED_TRACE_MULTI = textwrap.dedent(
        """
        +RESIDUALS/PPP
        % -1 2025-10-05 00:00:00.00 CODE_MEAS G06 HOB2 L1W 0.00000000 0.16205732 0.0000000 P-L1W
        % -1 2025-10-05 00:00:00.00 CODE_MEAS G06 HOB2 L2W 0.00000000 0.12038636 0.0000000 P-L2W
        % -1 2025-10-05 00:00:00.00 PHAS_MEAS G06 HOB2 L1W 0.00000000 0.00008205 0.0000000 L-L1W
        % -1 2025-10-05 00:00:00.00 PHAS_MEAS G06 HOB2 L2W 0.00000000 -0.00002716 0.0000000 L-L2W
        % -1 2025-10-05 00:00:30.00 CODE_MEAS G06 HOB2 L1W 0.00000000 0.00702357 0.0000000 P-L1W
        % -1 2025-10-05 00:00:30.00 CODE_MEAS G06 HOB2 L2W 0.00000000 0.13498779 0.0000000 P-L2W
        % -1 2025-10-05 00:00:30.00 PHAS_MEAS G06 HOB2 L1W 0.00000000 0.00188854 0.0000000 L-L1W
        % -1 2025-10-05 00:00:30.00 PHAS_MEAS G06 HOB2 L2W 0.00000000 -0.00113384 0.0000000 L-L2W
        % -1 2025-10-05 00:01:00.00 CODE_MEAS G06 HOB2 L1W 0.00000000 0.18148249 0.0000000 P-L1W
        % -1 2025-10-05 00:01:00.00 CODE_MEAS G06 HOB2 L2W 0.00000000 0.06148189 0.0000000 P-L2W
        % -1 2025-10-05 00:01:00.00 PHAS_MEAS G06 HOB2 L1W 0.00000000 0.00063349 0.0000000 L-L1W
        % -1 2025-10-05 00:01:00.00 PHAS_MEAS G06 HOB2 L2W 0.00000000 -0.00042137 0.0000000 L-L2W
        -RESIDUALS/PPP
        """
    ).strip()

    def _write_trace(self, directory: Path, name: str, content: str) -> Path:
        path = directory / name
        path.write_text(content)
        return path

    def test_prefers_smoothed_when_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_trace(
                tmpdir_path, "Network_TEST.TRACE", self.FORWARD_TRACE
            )
            smoothed_path = self._write_trace(
                tmpdir_path, "Network_TEST_smoothed.TRACE", self.SMOOTHED_TRACE
            )

            df = parse_residuals([forward_path, smoothed_path])

            self.assertEqual(len(df), 2, "Should select smoothed residuals when available")
            self.assertTrue((df["trace_type"] == "smoothed").all())
            self.assertTrue((df["iter"] == -1).all())
            self.assertSetEqual(set(df["recv"]), {"STAT", "OTHR"})
            self.assertNotIn("datetime", df.columns)
            code_sigma = df[df["meas"] == "CODE_MEAS"]["sigma"].iloc[0]
            phase_sigma = df[df["meas"] == "PHAS_MEAS"]["sigma"].iloc[0]
            self.assertAlmostEqual(code_sigma, 0.4000, places=4)
            self.assertAlmostEqual(phase_sigma, 0.0200, places=4)

    def test_smoothed_merge_with_multiple_epochs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_trace(
                tmpdir_path, "Network_TEST.TRACE", self.FORWARD_TRACE_MULTI
            )
            smoothed_path = self._write_trace(
                tmpdir_path, "Network_TEST_smoothed.TRACE", self.SMOOTHED_TRACE_MULTI
            )

            df = parse_residuals([forward_path, smoothed_path])

            self.assertGreater(len(df), 0)
            self.assertTrue((df["trace_type"] == "smoothed").all())
            zero_mask = df["prefit"] == 0
            self.assertTrue(zero_mask.any(), "Smoothed results should keep zero prefit")
            self.assertNotIn("datetime", df.columns)

            timestamps = pd.to_datetime(df["date"] + " " + df["time"])
            sigma_values = df.assign(timestamp=timestamps).groupby(["timestamp", "sig"])["sigma"].first()
            self.assertAlmostEqual(
                sigma_values.loc[(pd.Timestamp("2025-10-05 00:00:00"), "L1W")],
                0.3449291,
                places=6,
            )
            self.assertAlmostEqual(
                sigma_values.loc[(pd.Timestamp("2025-10-05 00:00:30"), "L2W")],
                0.3448066,
                places=6,
            )
            self.assertAlmostEqual(
                sigma_values.loc[(pd.Timestamp("2025-10-05 00:01:00"), "L1W")],
                0.3446935,
                places=6,
            )

    def test_forward_only_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_trace(
                tmpdir_path, "Network_TEST.TRACE", self.FORWARD_TRACE
            )

            df = parse_residuals([forward_path], strategy="auto")

            self.assertEqual(len(df), 2, "Forward residuals should be returned when smoothed missing")
            self.assertSetEqual(set(df["trace_type"]), {"forward"})
            self.assertIn(1, set(df["iter"]))
            self.assertNotIn(-1, set(df["iter"]))
            self.assertNotIn("datetime", df.columns)

    def test_forward_keep_all_iterations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_trace(
                tmpdir_path, "Network_TEST.TRACE", self.FORWARD_TRACE
            )

            df = parse_residuals(
                [forward_path],
                strategy="forward",
                forward_keep_last=False,
            )

            self.assertEqual(len(df), 3, "All forward iterations should be retained")
            stat_iters = sorted(df[df["recv"] == "STAT"]["iter"].tolist())
            self.assertEqual(stat_iters, [0, 1])

    def test_include_source_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_trace(
                tmpdir_path, "Network_TEST.TRACE", self.FORWARD_TRACE
            )
            smoothed_path = self._write_trace(
                tmpdir_path, "Network_TEST_smoothed.TRACE", self.SMOOTHED_TRACE
            )

            df = parse_residuals(
                [forward_path, smoothed_path],
                include_source=True,
            )

            self.assertIn("source_path", df.columns)
            self.assertTrue(
                df["source_path"].str.endswith("Network_TEST_smoothed.TRACE").all()
            )

    def test_strategy_both(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_trace(
                tmpdir_path, "Network_TEST.TRACE", self.FORWARD_TRACE
            )
            smoothed_path = self._write_trace(
                tmpdir_path, "Network_TEST_smoothed.TRACE", self.SMOOTHED_TRACE
            )

            df = parse_residuals(
                [forward_path, smoothed_path],
                strategy="both",
            )

            self.assertEqual(len(df), 4, "Both forward and smoothed residuals should be returned")
            self.assertSetEqual(set(df["trace_type"]), {"forward", "smoothed"})

    def test_empty_input(self):
        df = parse_residuals([])
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
        self.assertIn("trace_type", df.columns)


class TestParseResidualLines(unittest.TestCase):
    """Tests for parse_residual_lines function"""

    def test_parse_residual_lines_basic(self):
        """Test basic reading of residual lines"""
        df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(len(df), 0, "DataFrame should contain residual records")

        # Check for expected columns
        expected_columns = [
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
            "datetime",
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected column '{col}' not found")

    def test_parse_residual_lines_column_types(self):
        """Test that columns have the correct data types"""
        df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())

        # datetime should be datetime64
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # iter should be int
        self.assertTrue(
            np.issubdtype(df["iter"].dtype, np.integer), "iter should be int"
        )

        # Numeric columns should be float
        numeric_cols = ["prefit", "postfit", "sigma"]
        for col in numeric_cols:
            self.assertTrue(
                np.issubdtype(df[col].dtype, np.floating),
                f"Column '{col}' should be float",
            )

    def test_parse_residual_lines_negative_iteration(self):
        """Test handling of negative iteration numbers (smoothed files)"""
        lines = [
            "% -1 2025-10-05 00:01:00.00 PHAS_MEAS G01 ALIC L1C -0.0234 0.0012 0.0500 LARGE",
            "% -1 2025-10-05 00:01:00.00 CODE_MEAS G01 ALIC L1C -0.1200 0.0110 0.5000 LARGE",
        ]
        df = parse_residual_lines(lines)

        self.assertEqual(len(df), 2)
        self.assertTrue((df["iter"] == -1).all())
        self.assertTrue(df["prefit_ratio"].isna().all())
        self.assertTrue(df["postfit_ratio"].isna().all())

    def test_parse_residual_lines_with_ratios(self):
        """Test parsing of 14-field format with prefit_ratio and postfit_ratio"""
        lines = [
            "% 1 2025-10-05 00:02:00.00 PHAS_MEAS G01 ALIC L1C -0.0234 0.0012 0.0500 1.25 0.75 OK",
            "% 1 2025-10-05 00:02:00.00 CODE_MEAS G01 ALIC L1C -0.1200 0.0110 0.5000 2.50 0.90 OK",
        ]
        df = parse_residual_lines(lines)

        self.assertEqual(len(df), 2)
        self.assertTrue((df["iter"] == 1).all())
        self.assertTrue((df["prefit_ratio"] > 0).all())
        self.assertTrue((df["postfit_ratio"] > 0).all())

        # Dataset fixture does not include ratio values, but should still expose the columns
        fixture_df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())
        self.assertIn("prefit_ratio", fixture_df.columns)
        self.assertTrue(fixture_df["prefit_ratio"].isna().all())
        self.assertTrue(fixture_df["postfit_ratio"].isna().all())

    def test_parse_residual_lines_without_ratios(self):
        """Test parsing of 12-field format without ratios"""
        df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())

        # Negative iterations don't have ratios
        neg_iter = df[df["iter"] < 0]
        if "prefit_ratio" in df.columns:
            self.assertTrue(
                neg_iter["prefit_ratio"].isna().all(),
                "Negative iterations should not have ratios",
            )

    def test_parse_residual_lines_measurements(self):
        """Test that measurement types are correctly parsed"""
        df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())

        # Should have PHAS_MEAS and CODE_MEAS
        meas_types = df["meas"].unique()
        self.assertIn("PHAS_MEAS", meas_types, "Should have phase measurements")
        self.assertIn("CODE_MEAS", meas_types, "Should have code measurements")

    def test_parse_residual_lines_receivers(self):
        """Test that receivers are correctly parsed"""
        df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())

        receivers = df["recv"].unique()
        self.assertGreater(len(receivers), 0, "Residuals should include at least one receiver")
        for recv in receivers:
            self.assertRegex(recv, r"^[A-Z0-9]{4}$", f"Unexpected receiver format: {recv}")

    def test_parse_residual_lines_labels(self):
        """Test that labels are correctly parsed"""
        df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())

        labels = df["label"].unique()
        self.assertGreater(len(labels), 0, "Should expose residual labels")
        for label in labels:
            self.assertRegex(
                label,
                r"^[LP]-L[12][A-Z]$",
                f"Unexpected residual label format: {label}",
            )

    def test_parse_residual_lines_specific_record(self):
        """Test parsing of a specific record"""
        df = parse_residual_lines(trace_residual_lines_sample.decode().splitlines())

        # Find G06 ALIC L1W phase measurement
        record = df[
            (df["sat"] == "G06")
            & (df["recv"] == "ALIC")
            & (df["sig"] == "L1W")
            & (df["meas"] == "PHAS_MEAS")
        ]
        self.assertGreater(len(record), 0, "Expected G06 ALIC L1W residuals")
        first_rec = record.iloc[0]
        self.assertAlmostEqual(first_rec["prefit"], 10.3103, places=3)
        self.assertAlmostEqual(first_rec["postfit"], 0.0, places=4)
        self.assertAlmostEqual(first_rec["sigma"], 0.0045, places=4)


class TestParseLargeErrors(unittest.TestCase):
    """Tests for parse_large_errors function"""

    def test_parse_large_errors_basic(self):
        """Test basic reading of large error lines"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(len(df), 0, "DataFrame should contain large error records")

        # Check for expected columns
        expected_columns = ["datetime", "kind", "value", "recv"]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected column '{col}' not found")

    def test_parse_large_errors_column_types(self):
        """Test that columns have the correct data types"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        # datetime should be datetime64
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # kind should be object (string)
        self.assertEqual(df["kind"].dtype, object)

        # value should be float
        self.assertTrue(
            np.issubdtype(df["value"].dtype, np.floating), "value should be float"
        )

    def test_parse_large_errors_kinds(self):
        """Test that kind values are as expected"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        # Should have MEAS and STATE kinds
        kinds = df["kind"].unique()
        self.assertIn("MEAS", kinds, "Should have MEAS kind")
        self.assertIn("STATE", kinds, "Should have STATE kind")

    def test_parse_large_errors_meas_columns(self):
        """Test that MEAS errors have expected columns"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        # Filter for MEAS errors
        meas_errors = df[df["kind"] == "MEAS"]
        self.assertGreater(len(meas_errors), 0, "Should have MEAS errors")

        # Should have meas_type, sat, sig columns
        self.assertIn("meas_type", meas_errors.columns)
        self.assertIn("sat", meas_errors.columns)
        self.assertIn("sig", meas_errors.columns)

        # Check that these columns are not null
        self.assertTrue(meas_errors["meas_type"].notna().all())
        self.assertTrue(meas_errors["sat"].notna().all())
        self.assertTrue(meas_errors["sig"].notna().all())

    def test_parse_large_errors_state_columns(self):
        """Test that STATE errors have expected columns"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        # Filter for STATE errors
        state_errors = df[df["kind"] == "STATE"]
        self.assertGreater(len(state_errors), 0, "Should have STATE errors")

        # Should have param, comp columns
        self.assertIn("param", state_errors.columns)
        self.assertIn("comp", state_errors.columns)

        # Check that these columns are not null
        self.assertTrue(state_errors["param"].notna().all())
        self.assertTrue(state_errors["comp"].notna().all())

    def test_parse_large_errors_meas_specific(self):
        """Test parsing of a specific MEAS error"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        # Find G19 TONG L1W measurement error
        g19_error = df[
            (df["kind"] == "MEAS")
            & (df["sat"] == "G19")
            & (df["recv"] == "TONG")
            & (df["sig"] == "L1W")
        ]
        self.assertGreater(len(g19_error), 0, "Expected G19 MEAS error lines")
        first_rec = g19_error.iloc[0]
        self.assertAlmostEqual(first_rec["value"], 9.16139, places=5)
        self.assertEqual(first_rec["meas_type"], "PHAS_MEAS")

    def test_parse_large_errors_state_specific(self):
        """Test parsing of a specific STATE error"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        # Find ABMF REC_POS X state error
        rec_pos_x = df[
            (df["kind"] == "STATE")
            & (df["recv"] == "ABMF")
            & (df["param"] == "REC_POS")
            & (df["comp"] == "X")
        ]
        self.assertGreater(len(rec_pos_x), 0, "Expected ABMF REC_POS X state errors")
        first_rec = rec_pos_x.iloc[0]
        self.assertAlmostEqual(first_rec["value"], 8.38286, places=5)

    def test_parse_large_errors_receivers(self):
        """Test that receivers are correctly parsed"""
        df = parse_large_errors(trace_large_errors_sample.decode().splitlines())

        receivers = set(df["recv"].dropna().unique())
        self.assertGreater(len(receivers), 0, "Large errors should include receivers")
        self.assertTrue(
            {"ABMF", "TONG"}.issubset(receivers),
            "Expected ABMF and TONG receivers in large errors",
        )


class TestParseAmbiguityResets(unittest.TestCase):
    """Tests for parse_ambiguity_resets function"""

    def test_parse_ambiguity_resets_basic(self):
        """Test basic reading of ambiguity reset lines"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(
            len(df), 0, "DataFrame should contain ambiguity reset records"
        )

        # Check for expected columns
        expected_columns = ["datetime", "action", "sat", "recv", "sig", "reasons"]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected column '{col}' not found")

    def test_parse_ambiguity_resets_column_types(self):
        """Test that columns have the correct data types"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        # datetime should be datetime64
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # String columns
        for col in ["action", "sat", "recv", "sig", "reasons"]:
            self.assertEqual(df[col].dtype, object, f"Column '{col}' should be object")

    def test_parse_ambiguity_resets_actions(self):
        """Test that action values are as expected"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        # Should have PREPROC and REJECT actions
        actions = df["action"].unique()
        self.assertIn("PREPROC", actions, "Should have PREPROC action")
        self.assertIn("REJECT", actions, "Should have REJECT action")

    def test_parse_ambiguity_resets_preproc_reasons(self):
        """Test that PREPROC reasons are correctly parsed"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        # Filter for PREPROC actions
        preproc = df[df["action"] == "PREPROC"]
        self.assertGreater(len(preproc), 0, "Should have PREPROC records")

        # Check for expected reasons
        all_reasons = set()
        for reasons_str in preproc["reasons"]:
            all_reasons.update([r.strip() for r in reasons_str.split(",")])

        expected_reasons = ["GF", "MW", "LLI", "SCDIA"]
        for reason in expected_reasons:
            self.assertIn(
                reason, all_reasons, f"Expected PREPROC reason '{reason}' not found"
            )

    def test_parse_ambiguity_resets_reject_reasons(self):
        """Test that REJECT reasons include KF"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        # Filter for REJECT actions
        reject = df[df["action"] == "REJECT"]
        self.assertGreater(len(reject), 0, "Should have REJECT records")

        # All REJECT actions should have KF in their reasons
        for reasons_str in reject["reasons"]:
            reasons_list = [r.strip() for r in reasons_str.split(",")]
            self.assertIn("KF", reasons_list, "REJECT actions should include KF reason")

    def test_parse_ambiguity_resets_multiple_reasons(self):
        """Test parsing of records with multiple reasons"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        multi_reason = df[df["reasons"].str.contains(",", regex=False)]
        self.assertGreater(len(multi_reason), 0, "Should have multi-reason entries")
        self.assertTrue(
            multi_reason["reasons"].str.contains("GF").any(),
            "Expected at least one multi-reason to include GF",
        )
        self.assertTrue(
            multi_reason["reasons"].str.contains("MW").any(),
            "Expected at least one multi-reason to include MW",
        )

    def test_parse_ambiguity_resets_receivers(self):
        """Test that receivers are correctly parsed"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        receivers = set(df["recv"].unique())
        self.assertTrue(
            {"ABMF", "TONG"}.issubset(receivers),
            "Expected both ABMF and TONG receivers in ambiguity resets",
        )

    def test_parse_ambiguity_resets_sat_format(self):
        """Test that sat values have the expected format"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        # sat should be in format like G01, E02, R03, etc.
        sats = df["sat"].unique()
        self.assertGreater(len(sats), 0, "Should have sat values")

        # Check format: first char is constellation, followed by 2 digits
        for sat in sats:
            self.assertEqual(len(sat), 3, f"sat '{sat}' should be 3 characters")
            self.assertIn(
                sat[0], ["G", "E", "R", "C"], f"sat '{sat}' should start with G/E/R/C"
            )
            self.assertTrue(
                sat[1:].isdigit(), f"sat '{sat}' last 2 chars should be digits"
            )

    def test_parse_ambiguity_resets_deduplication(self):
        """Test that duplicate reasons are correctly deduplicated"""
        df = parse_ambiguity_resets(
            trace_ambiguity_resets_sample.decode().splitlines()
        )

        # Each reasons string should not have duplicates
        for reasons_str in df["reasons"]:
            reasons_list = [r.strip() for r in reasons_str.split(",")]
            self.assertEqual(
                len(reasons_list),
                len(set(reasons_list)),
                "Reasons should not have duplicates",
            )


class TestParseElevation(unittest.TestCase):
    """Tests for parse_elevation function"""

    def test_parse_elevation_basic(self):
        """Test basic reading of elevation data"""
        df = parse_elevation(trace_pde_cs_sample.decode().splitlines())

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(len(df), 0, "DataFrame should contain elevation records")

        # Check for expected columns
        expected_columns = ["datetime", "sat", "el", "mode"]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected column '{col}' not found")

    def test_parse_elevation_column_types(self):
        """Test that columns have the correct data types"""
        df = parse_elevation(trace_pde_cs_sample.decode().splitlines())

        # datetime should be datetime64
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # el should be float
        self.assertTrue(
            np.issubdtype(df["el"].dtype, np.floating), "el should be float"
        )

        # mode should be object
        self.assertEqual(df["mode"].dtype, object)

    def test_parse_elevation_range(self):
        """Test that elevation values are in reasonable range"""
        df = parse_elevation(trace_pde_cs_sample.decode().splitlines())

        # Elevation should be between 0 and 90 degrees
        self.assertTrue((df["el"] >= 0).all(), "Elevation should be >= 0")
        self.assertTrue((df["el"] <= 90).all(), "Elevation should be <= 90")

    def test_parse_elevation_sat_format(self):
        """Test that sat values have the expected format"""
        df = parse_elevation(trace_pde_cs_sample.decode().splitlines())

        # sat should be in format like G01, E02, R03, etc.
        sats = df["sat"].unique()
        self.assertGreater(len(sats), 0, "Should have sat values")

        # Check format: first char is constellation, followed by 2 digits
        for sat in sats:
            self.assertEqual(len(sat), 3, f"sat '{sat}' should be 3 characters")
            self.assertIn(
                sat[0], ["G", "E", "R", "C"], f"sat '{sat}' should start with G/E/R/C"
            )
            self.assertTrue(
                sat[1:].isdigit(), f"sat '{sat}' last 2 chars should be digits"
            )

    def test_parse_elevation_mode_values(self):
        """Test that mode column contains expected values"""
        df = parse_elevation(trace_pde_cs_sample.decode().splitlines())

        # mode should be None, 'TRIP', or 'DUAL'
        unique_modes = df["mode"].dropna().unique()
        valid_modes = ["TRIP", "DUAL"]
        for mode in unique_modes:
            self.assertIn(mode, valid_modes, f"Unexpected mode value: {mode}")

    def test_parse_elevation_no_extra_columns(self):
        """Test that only elevation-relevant columns are returned"""
        df = parse_elevation(trace_pde_cs_sample.decode().splitlines())

        # Should only have the 4 expected columns
        expected_columns = ["datetime", "sat", "el", "mode"]
        self.assertEqual(
            set(df.columns),
            set(expected_columns),
            "Should only have elevation-relevant columns",
        )

    def test_parse_elevation_empty_input(self):
        """Test behavior with content that doesn't contain PDE-CS section"""
        df = parse_elevation(trace_no_pde_cs.decode().splitlines())

        # Should return empty DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0, "Should return empty DataFrame for no PDE-CS data")


if __name__ == "__main__":
    unittest.main()
