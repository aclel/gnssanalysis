import tempfile
import unittest
from pathlib import Path
import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np

from gnssanalysis.gn_io.pos import (
    parse_pos,
    parse_pos_files,
)
from test_datasets.pos_test_data import (
    pos_sample,
    pos_no_data,
)


class TestParsePos(unittest.TestCase):
    """Tests for parse_pos function"""

    def test_parse_pos_basic(self):
        """Test basic reading of .POS file"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(len(df), 0, "DataFrame should contain position records")

        # Check for expected columns
        expected_columns = [
            "datetime", "decimal_year", "X", "Y", "Z",
            "Sx", "Sy", "Sz", "Rxy", "Rxz", "Ryz",
            "Nlat", "Elong", "Height",
            "dN", "dE", "dU",
            "Sn", "Se", "Su",
            "Rne", "Rnu", "Reu",
            "soln"
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected column '{col}' not found")

    def test_parse_pos_column_types(self):
        """Test that columns have the correct data types"""
        df = parse_pos(pos_sample.decode().splitlines())

        # datetime should be datetime64
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # soln should be categorical
        self.assertIsInstance(df["soln"].dtype, pd.CategoricalDtype)

        # Numeric columns should be float
        numeric_cols = [
            "decimal_year", "X", "Y", "Z",
            "Sx", "Sy", "Sz", "Rxy", "Rxz", "Ryz",
            "Nlat", "Elong", "Height",
            "dN", "dE", "dU",
            "Sn", "Se", "Su",
            "Rne", "Rnu", "Reu"
        ]
        for col in numeric_cols:
            self.assertTrue(
                np.issubdtype(df[col].dtype, np.floating),
                f"Column '{col}' should be float type",
            )

    def test_parse_pos_datetime(self):
        """Test that datetime is correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check datetime is set
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["datetime"]))

        # Check we have expected number of epochs
        self.assertEqual(len(df), 5, "Should have 5 position epochs")

        # Check first datetime
        first_dt = df["datetime"].iloc[0]
        expected = pd.Timestamp("2025-10-05 00:00:00")
        self.assertEqual(first_dt, expected, "First datetime should match")

        # Check last datetime
        last_dt = df["datetime"].iloc[-1]
        expected_last = pd.Timestamp("2025-10-05 00:02:00")
        self.assertEqual(last_dt, expected_last, "Last datetime should match")

    def test_parse_pos_xyz_coordinates(self):
        """Test that XYZ coordinates are correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check X coordinate
        x_vals = df["X"].unique()
        self.assertEqual(len(x_vals), 1, "X should be constant in test data")
        self.assertAlmostEqual(x_vals[0], -5930303.49615, places=5)

        # Check Y coordinate
        y_vals = df["Y"].unique()
        self.assertEqual(len(y_vals), 1, "Y should be constant in test data")
        self.assertAlmostEqual(y_vals[0], -500149.25187, places=5)

        # Check Z coordinate
        z_vals = df["Z"].unique()
        self.assertEqual(len(z_vals), 1, "Z should be constant in test data")
        self.assertAlmostEqual(z_vals[0], -2286366.31796, places=5)

    def test_parse_pos_neu_offsets(self):
        """Test that NEU offsets are correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check dN (all should be same in test data)
        dn_vals = df["dN"].unique()
        self.assertEqual(len(dn_vals), 1)
        self.assertAlmostEqual(dn_vals[0], 0.00019, places=5)

        # Check dE
        de_vals = df["dE"].unique()
        self.assertEqual(len(de_vals), 1)
        self.assertAlmostEqual(de_vals[0], -0.01335, places=5)

        # Check dU
        du_vals = df["dU"].unique()
        self.assertEqual(len(du_vals), 1)
        self.assertAlmostEqual(du_vals[0], 0.02917, places=5)

    def test_parse_pos_sigmas(self):
        """Test that sigma values are correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check XYZ sigmas
        self.assertAlmostEqual(df["Sx"].iloc[0], 0.00244, places=5)
        self.assertAlmostEqual(df["Sy"].iloc[0], 0.00159, places=5)
        self.assertAlmostEqual(df["Sz"].iloc[0], 0.00093, places=5)

        # Check NEU sigmas
        self.assertAlmostEqual(df["Sn"].iloc[0], 0.00045, places=5)
        self.assertAlmostEqual(df["Se"].iloc[0], 0.00158, places=5)
        self.assertAlmostEqual(df["Su"].iloc[0], 0.00258, places=5)

    def test_parse_pos_correlations(self):
        """Test that correlation values are correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check XYZ correlations
        self.assertAlmostEqual(df["Rxy"].iloc[0], 0.069, places=3)
        self.assertAlmostEqual(df["Rxz"].iloc[0], 0.868, places=3)
        self.assertAlmostEqual(df["Ryz"].iloc[0], 0.048, places=3)

        # Check NEU correlations
        self.assertAlmostEqual(df["Rne"].iloc[0], 0.111, places=3)
        self.assertAlmostEqual(df["Rnu"].iloc[0], 0.225, places=3)
        self.assertAlmostEqual(df["Reu"].iloc[0], -0.014, places=3)

    def test_parse_pos_geodetic(self):
        """Test that geodetic coordinates are correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check latitude
        lat_vals = df["Nlat"].unique()
        self.assertEqual(len(lat_vals), 1)
        self.assertAlmostEqual(lat_vals[0], -21.1447141422, places=8)

        # Check longitude
        lon_vals = df["Elong"].unique()
        self.assertEqual(len(lon_vals), 1)
        self.assertAlmostEqual(lon_vals[0], -175.1792034739, places=8)

        # Check height
        height_vals = df["Height"].unique()
        self.assertEqual(len(height_vals), 1)
        self.assertAlmostEqual(height_vals[0], 56.31635, places=5)

    def test_parse_pos_solution_type(self):
        """Test that solution type is correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check soln column
        soln_vals = df["soln"].unique()
        self.assertEqual(len(soln_vals), 1)
        self.assertEqual(soln_vals[0], "ginan")

    def test_parse_pos_decimal_year(self):
        """Test that decimal year is correctly parsed"""
        df = parse_pos(pos_sample.decode().splitlines())

        # Check decimal year
        dec_year = df["decimal_year"].iloc[0]
        self.assertAlmostEqual(dec_year, 2025.761643265, places=6)

    def test_parse_pos_header_info(self):
        """Test that header information is extracted when requested"""
        df = parse_pos(pos_sample.decode().splitlines(), include_header_info=True)

        # Check header attributes
        self.assertEqual(df.attrs["reference_frame"], "IGS20")
        self.assertEqual(df.attrs["format_version"], "2.0.0")
        self.assertEqual(df.attrs["station_id"], "TONG")

        # Check XYZ reference position
        xyz_ref = df.attrs["xyz_ref"]
        self.assertEqual(len(xyz_ref), 3)
        self.assertAlmostEqual(xyz_ref[0], -5930303.467855, places=6)
        self.assertAlmostEqual(xyz_ref[1], -500149.262879, places=6)
        self.assertAlmostEqual(xyz_ref[2], -2286366.307619, places=6)

        # Check NEU reference position
        neu_ref = df.attrs["neu_ref"]
        self.assertEqual(len(neu_ref), 3)
        self.assertAlmostEqual(neu_ref[0], -21.144714143866, places=10)
        self.assertAlmostEqual(neu_ref[1], -175.179203345436, places=10)
        self.assertAlmostEqual(neu_ref[2], 56.287189315, places=6)

    def test_parse_pos_empty_input(self):
        """Test behavior with content that doesn't contain data section"""
        df = parse_pos(pos_no_data.decode().splitlines())

        # Should return empty DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0, "Should return empty DataFrame for no data")


class TestParsePosFiles(unittest.TestCase):
    """Tests for parse_pos_files function"""

    POS_FORWARD = """PBO Station Position Time Series. Reference Frame : IGS20
Format Version: 2.0.0
4-character ID: TEST
*YYYY-MM-DDTHH:MM:SS.SSS YYYY.YYYYYYYYY        X             Y              Z           Sx         Sy        Sz      Rxy     Rxz     Ryz        NLat            Elong        Height         dN          dE          dU        Sn       Se         Su       Rne     Rnu     Reu  soln
 2025-10-05T00:00:00.000 2025.761643265 -5930303.50000 -500149.26000 -2286366.32000   0.00300   0.00200   0.00100   0.100   0.900   0.050  -21.1447141422 -175.1792034739    56.32000     1.00000     2.00000     3.00000   0.00500   0.00200   0.00300   0.100   0.200  -0.010 ginan
 2025-10-05T00:00:30.000 2025.761644216 -5930303.51000 -500149.27000 -2286366.33000   0.00300   0.00200   0.00100   0.100   0.900   0.050  -21.1447141422 -175.1792034739    56.33000     1.10000     2.10000     3.10000   0.00500   0.00200   0.00300   0.100   0.200  -0.010 ginan
"""

    POS_SMOOTHED = """PBO Station Position Time Series. Reference Frame : IGS20
Format Version: 2.0.0
4-character ID: TEST
*YYYY-MM-DDTHH:MM:SS.SSS YYYY.YYYYYYYYY        X             Y              Z           Sx         Sy        Sz      Rxy     Rxz     Ryz        NLat            Elong        Height         dN          dE          dU        Sn       Se         Su       Rne     Rnu     Reu  soln
 2025-10-05T00:00:00.000 2025.761643265 -5930303.49615 -500149.25187 -2286366.31796   0.00244   0.00159   0.00093   0.069   0.868   0.048  -21.1447141422 -175.1792034739    56.31635     0.00019    -0.01335     0.02917   0.00045   0.00158   0.00258   0.111   0.225  -0.014 ginan
 2025-10-05T00:00:30.000 2025.761644216 -5930303.49615 -500149.25187 -2286366.31796   0.00244   0.00159   0.00093   0.069   0.868   0.048  -21.1447141422 -175.1792034739    56.31635     0.00019    -0.01335     0.02917   0.00045   0.00158   0.00258   0.111   0.225  -0.014 ginan
"""

    def _write_pos_file(self, directory: Path, name: str, content: str) -> Path:
        path = directory / name
        path.write_text(content)
        return path

    def test_prefers_smoothed_when_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_pos_file(
                tmpdir_path, "TEST_2025.POS", self.POS_FORWARD
            )
            smoothed_path = self._write_pos_file(
                tmpdir_path, "TEST_2025_smoothed.POS", self.POS_SMOOTHED
            )

            df = parse_pos_files([forward_path, smoothed_path])

            self.assertEqual(len(df), 2, "Should select smoothed positions when available")
            self.assertTrue((df["pos_type"] == "smoothed").all())
            self.assertIn("pos_type", df.columns)

            # Check that smoothed values are present
            self.assertAlmostEqual(df["dN"].iloc[0], 0.00019, places=5)

    def test_forward_only_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_pos_file(
                tmpdir_path, "TEST_2025.POS", self.POS_FORWARD
            )

            df = parse_pos_files([forward_path], strategy="auto")

            self.assertEqual(len(df), 2, "Forward positions should be returned when smoothed missing")
            self.assertSetEqual(set(df["pos_type"]), {"forward"})

            # Check that forward values are present
            self.assertAlmostEqual(df["dN"].iloc[0], 1.00000, places=5)

    def test_strategy_both(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_pos_file(
                tmpdir_path, "TEST_2025.POS", self.POS_FORWARD
            )
            smoothed_path = self._write_pos_file(
                tmpdir_path, "TEST_2025_smoothed.POS", self.POS_SMOOTHED
            )

            df = parse_pos_files(
                [forward_path, smoothed_path],
                strategy="both",
            )

            self.assertEqual(len(df), 4, "Both forward and smoothed positions should be returned")
            self.assertSetEqual(set(df["pos_type"]), {"forward", "smoothed"})

            # Check we have both types at first epoch
            first_epoch = df[df["datetime"] == df["datetime"].iloc[0]]
            self.assertEqual(len(first_epoch), 2, "Should have both types at first epoch")

    def test_strategy_forward_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_pos_file(
                tmpdir_path, "TEST_2025.POS", self.POS_FORWARD
            )
            smoothed_path = self._write_pos_file(
                tmpdir_path, "TEST_2025_smoothed.POS", self.POS_SMOOTHED
            )

            df = parse_pos_files(
                [forward_path, smoothed_path],
                strategy="forward",
            )

            self.assertEqual(len(df), 2, "Should use forward strategy")
            self.assertTrue((df["pos_type"] == "forward").all())

    def test_strategy_smoothed_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            forward_path = self._write_pos_file(
                tmpdir_path, "TEST_2025.POS", self.POS_FORWARD
            )
            smoothed_path = self._write_pos_file(
                tmpdir_path, "TEST_2025_smoothed.POS", self.POS_SMOOTHED
            )

            df = parse_pos_files(
                [forward_path, smoothed_path],
                strategy="smoothed",
            )

            self.assertEqual(len(df), 2, "Should use smoothed strategy")
            self.assertTrue((df["pos_type"] == "smoothed").all())

    def test_empty_input(self):
        df = parse_pos_files([])
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)

    def test_invalid_strategy(self):
        with self.assertRaises(ValueError):
            parse_pos_files([], strategy="invalid")


if __name__ == "__main__":
    unittest.main()
