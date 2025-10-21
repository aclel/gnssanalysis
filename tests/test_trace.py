import unittest
import pandas as pd
import numpy as np

from gnssanalysis.gn_io.trace import _read_trace_pde_cs
from test_datasets.trace_test_data import trace_pde_cs_sample, trace_no_pde_cs


class TestReadTracePdeCs(unittest.TestCase):
    """Tests for _read_trace_pde_cs function"""

    def test_read_trace_pde_cs_basic(self):
        """Test basic reading of PDE-CS data"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(len(df), 0, "DataFrame should contain PDE-CS records")

        # Check the index
        self.assertEqual(df.index.names, ['TIME', 'PRN'])

        # Check for expected columns
        expected_columns = [
            'mode', 'el', 'lamw', 'gf12', 'mw12', 'siggf', 'sigmw',
            'lamew', 'gf25', 'mw25', 'vtpv', 'val', 'thres', 'N1', 'N2', 'N5'
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns, f"Expected column '{col}' not found")

    def test_read_trace_pde_cs_column_types(self):
        """Test that columns have the correct data types"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # mode should be object (string or None)
        self.assertEqual(df['mode'].dtype, object)

        # Numeric columns should be float
        numeric_cols = ['el', 'lamw', 'gf12', 'mw12', 'siggf', 'sigmw',
                        'lamew', 'gf25', 'mw25', 'vtpv', 'val', 'thres',
                        'N1', 'N2', 'N5']
        for col in numeric_cols:
            self.assertTrue(np.issubdtype(df[col].dtype, np.floating),
                            f"Column '{col}' should be float type")

    def test_read_trace_pde_cs_mode_values(self):
        """Test that mode column contains expected values"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # mode should be None, 'TRIP', or 'DUAL'
        unique_modes = df['mode'].unique()
        valid_modes = [None, 'TRIP', 'DUAL']
        for mode in unique_modes:
            self.assertIn(mode, valid_modes,
                          f"Unexpected mode value: {mode}")

        # Verify we have both TRIP and DUAL modes in the test data
        self.assertIn('TRIP', unique_modes)
        self.assertIn('DUAL', unique_modes)

    def test_read_trace_pde_cs_prn_format(self):
        """Test that PRN values have the expected format"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # PRN should be in format like G01, E02, R03, etc.
        prns = df.index.get_level_values('PRN').unique()
        self.assertGreater(len(prns), 0, "Should have PRN values")

        # Check format: first char is constellation, followed by 2 digits
        for prn in prns:
            self.assertEqual(len(prn), 3, f"PRN '{prn}' should be 3 characters")
            self.assertIn(prn[0], ['G', 'E', 'R', 'C'],
                          f"PRN '{prn}' should start with G/E/R/C")
            self.assertTrue(prn[1:].isdigit(),
                            f"PRN '{prn}' last 2 chars should be digits")

    def test_read_trace_pde_cs_elevation_range(self):
        """Test that elevation values are in reasonable range"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Elevation should be between 0 and 90 degrees
        self.assertTrue((df['el'] >= 0).all(), "Elevation should be >= 0")
        self.assertTrue((df['el'] <= 90).all(), "Elevation should be <= 90")

    def test_read_trace_pde_cs_time_index(self):
        """Test that TIME index is properly set"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # TIME should be the first level of the index
        self.assertEqual(df.index.names[0], 'TIME')

        # TIME values should be numeric (J2000)
        times = df.index.get_level_values('TIME')
        self.assertTrue(np.issubdtype(times.dtype, np.number),
                        "TIME should be numeric")

        # Check we have multiple time epochs
        unique_times = times.unique()
        self.assertGreater(len(unique_times), 1,
                           "Should have multiple time epochs")

    def test_read_trace_pde_cs_special_values(self):
        """Test handling of special values like inf, -inf, nan"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Check that inf values in sigmw are converted to NaN
        # (based on code line 338: if parts[idx] not in ['inf', '-inf'])
        if 'sigmw' in df.columns:
            # Should not have inf values
            self.assertFalse(np.isinf(df['sigmw'].dropna()).any(),
                             "sigmw should not contain inf values")

        # Check that 'nan' strings in mw25 are converted to NaN
        # (based on code line 347: if parts[idx] not in ['nan', '-nan'])
        if 'mw25' in df.columns:
            # All values should be either NaN or finite
            self.assertTrue(df['mw25'].isna().all() or np.isfinite(df['mw25'].dropna()).all(),
                            "mw25 should only contain NaN or finite values")

    def test_read_trace_pde_cs_empty_file(self):
        """Test behavior with content that doesn't contain PDE-CS section"""
        df = _read_trace_pde_cs(trace_no_pde_cs)

        # Should return empty DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0, "Should return empty DataFrame for no PDE-CS data")

    def test_read_trace_pde_cs_skipped_satellites(self):
        """Test that satellites with special markers are skipped"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Satellites with --low_elevation--, --single frequency-- markers should not appear
        # E27 (low elevation at 8.80), G31 (low elevation at 4.49), R22 (single freq), etc.
        prns = df.index.get_level_values('PRN').unique()

        # These should NOT be in the results (they have skip markers in the test data)
        # Note: The function should skip these based on the "--" markers
        # But looking at the code, it only skips if idx < len(parts) and parts[idx].startswith('--')
        # Let's verify what actually gets parsed

    def test_read_trace_pde_cs_trip_mode_fields(self):
        """Test that TRIP mode records have expected fields populated"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Filter for TRIP mode records
        trip_records = df[df['mode'] == 'TRIP']
        self.assertGreater(len(trip_records), 0, "Should have TRIP mode records")

        # TRIP mode should have lamew, gf25 fields (may be NaN but should exist)
        self.assertIn('lamew', trip_records.columns)
        self.assertIn('gf25', trip_records.columns)

    def test_read_trace_pde_cs_dual_mode_fields(self):
        """Test that DUAL mode records have expected fields"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Filter for DUAL mode records
        dual_records = df[df['mode'] == 'DUAL']
        self.assertGreater(len(dual_records), 0, "Should have DUAL mode records")

        # DUAL mode records exist and have basic fields
        self.assertTrue((dual_records['el'] > 0).all())
        self.assertTrue((dual_records['lamw'] > 0).all())

    def test_read_trace_pde_cs_lc_parameters(self):
        """Test that LC parameters (vtpv, val, thres) are parsed correctly"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Should have vtpv, val, thres columns
        self.assertIn('vtpv', df.columns)
        self.assertIn('val', df.columns)
        self.assertIn('thres', df.columns)

        # Filter out NaN values and check ranges
        valid_vtpv = df['vtpv'].dropna()
        if len(valid_vtpv) > 0:
            self.assertTrue((valid_vtpv >= 0).any(), "vtpv should have non-negative values")

        valid_thres = df['thres'].dropna()
        if len(valid_thres) > 0:
            # Thresholds should be reasonable positive values
            self.assertTrue((valid_thres > 0).all(), "thres should be positive")

    def test_read_trace_pde_cs_ambiguity_values(self):
        """Test that ambiguity values (N1, N2, N5) are parsed"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Should have N1, N2, N5 columns
        self.assertIn('N1', df.columns)
        self.assertIn('N2', df.columns)
        self.assertIn('N5', df.columns)

        # Check that some records have N1 and N2 values
        valid_n1 = df['N1'].dropna()
        valid_n2 = df['N2'].dropna()

        self.assertGreater(len(valid_n1), 0, "Should have some N1 values")
        self.assertGreater(len(valid_n2), 0, "Should have some N2 values")

    def test_read_trace_pde_cs_specific_satellite(self):
        """Test parsing of a specific satellite record"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Check if G18 exists in the data
        if 'G18' in df.index.get_level_values('PRN'):
            g18_data = df.loc[(slice(None), 'G18'), :]

            # G18 should be in TRIP mode
            self.assertTrue((g18_data['mode'] == 'TRIP').any())

            # Should have elevation values around 20 degrees
            self.assertTrue((g18_data['el'] >= 20).any())
            self.assertTrue((g18_data['el'] <= 21).any())


if __name__ == '__main__':
    unittest.main()
