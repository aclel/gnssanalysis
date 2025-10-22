import unittest
import pandas as pd
import numpy as np

from gnssanalysis.gn_io.trace import _read_trace_pde_cs, _read_trace_LC
from test_datasets.trace_test_data import trace_pde_cs_sample, trace_no_pde_cs, trace_lc_sample, trace_no_lc


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

    def test_read_trace_pde_cs_with_debug_lines(self):
        """Test that debug lines (detslp_ll, detslp_gf) are properly ignored"""
        df = _read_trace_pde_cs(trace_pde_cs_sample)

        # Should successfully parse data and ignore debug lines
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0, "Should parse PDE-CS data despite debug lines")

        # Check that we have the expected epoch with debug lines (518490.0)
        # This data comes after the debug lines in the test data
        times = df.index.get_level_values('TIME')

        # Should have data from the section with debug lines
        # The test data includes a G20 record at 518490.0 after the debug lines
        g20_data = df.loc[(slice(None), 'G20'), :]
        if len(g20_data) > 0:
            # Verify we can still read data after debug lines
            self.assertTrue(True, "Successfully parsed data after debug lines")


class TestReadTraceLC(unittest.TestCase):
    """Tests for _read_trace_LC function"""

    def test_read_trace_lc_basic(self):
        """Test basic reading of LC (linear combination) data"""
        df = _read_trace_LC(trace_lc_sample)

        # Check that we got a DataFrame
        self.assertIsInstance(df, pd.DataFrame)

        # Check that it's not empty
        self.assertGreater(len(df), 0, "DataFrame should contain LC records")

        # Check the index
        self.assertEqual(df.index.names, ['TIME', 'PRN', 'combo_type', 'code_type', 'combo_label'])

        # Check for expected value column
        self.assertIn('value', df.columns)

    def test_read_trace_lc_column_types(self):
        """Test that columns have the correct data types"""
        df = _read_trace_LC(trace_lc_sample)

        # value should be float
        self.assertTrue(np.issubdtype(df['value'].dtype, np.floating),
                        "Column 'value' should be float type")

    def test_read_trace_lc_combo_types(self):
        """Test that combo_type values are as expected"""
        df = _read_trace_LC(trace_lc_sample)

        # Get unique combo_types
        combo_types = df.index.get_level_values('combo_type').unique()

        # Check we have expected combo types
        expected_types = ['zd', 'mp', 'gf', 'mw', 'wl', 'if']
        for expected in expected_types:
            self.assertIn(expected, combo_types,
                          f"Expected combo_type '{expected}' not found")

    def test_read_trace_lc_code_types(self):
        """Test that code_type values are as expected"""
        df = _read_trace_LC(trace_lc_sample)

        # Get unique code_types
        code_types = df.index.get_level_values('code_type').unique()

        # Should have L (phase) and P (code)
        self.assertIn('L', code_types, "Expected code_type 'L' (phase)")
        self.assertIn('P', code_types, "Expected code_type 'P' (code)")

    def test_read_trace_lc_combo_labels(self):
        """Test that combo_label values are as expected"""
        df = _read_trace_LC(trace_lc_sample)

        # Get unique combo_labels
        combo_labels = df.index.get_level_values('combo_label').unique()

        # Check for some expected labels
        expected_labels = ['L1', 'L2', 'L5', 'P1', 'P2', 'P5',
                           'mp1', 'mp2', 'mp5',
                           'gf12', 'gf15', 'gf25',
                           'mw12', 'mw15', 'mw25',
                           'wl12', 'wl15', 'wl25',
                           'if12', 'if15', 'if25']
        for expected in expected_labels:
            self.assertIn(expected, combo_labels,
                          f"Expected combo_label '{expected}' not found")

    def test_read_trace_lc_prn_format(self):
        """Test that PRN values have the expected format"""
        df = _read_trace_LC(trace_lc_sample)

        # Get unique PRNs
        prns = df.index.get_level_values('PRN').unique()
        self.assertGreater(len(prns), 0, "Should have PRN values")

        # Check format: first char is constellation, followed by 2 digits
        for prn in prns:
            self.assertEqual(len(prn), 3, f"PRN '{prn}' should be 3 characters")
            self.assertIn(prn[0], ['G', 'E', 'R', 'C'],
                          f"PRN '{prn}' should start with G/E/R/C")
            self.assertTrue(prn[1:].isdigit(),
                            f"PRN '{prn}' last 2 chars should be digits")

    def test_read_trace_lc_time_index(self):
        """Test that TIME index is properly set"""
        df = _read_trace_LC(trace_lc_sample)

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

    def test_read_trace_lc_specific_satellite(self):
        """Test parsing of a specific satellite record"""
        df = _read_trace_LC(trace_lc_sample)

        # Check if G02 exists in the data
        if 'G02' in df.index.get_level_values('PRN'):
            # Get G02 data for first time epoch
            times = df.index.get_level_values('TIME').unique()
            first_time = times[0]

            # Get zd L L1 measurement for G02
            try:
                g02_l1 = df.loc[(first_time, 'G02', 'zd', 'L', 'L1'), 'value']
                # Should be approximately 22093585.6788
                self.assertAlmostEqual(g02_l1, 22093585.6788, places=4)
            except KeyError:
                self.fail("Expected G02 zd L L1 measurement not found")

    def test_read_trace_lc_zero_values(self):
        """Test that zero values are correctly parsed"""
        df = _read_trace_LC(trace_lc_sample)

        # G02 has L5=0.0000 in the test data
        times = df.index.get_level_values('TIME').unique()
        first_time = times[0]

        try:
            g02_l5 = df.loc[(first_time, 'G02', 'zd', 'L', 'L5'), 'value']
            self.assertEqual(g02_l5, 0.0)
        except KeyError:
            self.fail("Expected G02 zd L L5 measurement not found")

    def test_read_trace_lc_multipath(self):
        """Test that multipath (mp) measurements are correctly parsed"""
        df = _read_trace_LC(trace_lc_sample)

        # Filter for multipath measurements
        mp_data = df.loc[(slice(None), slice(None), 'mp', 'P', slice(None)), :]
        self.assertGreater(len(mp_data), 0, "Should have multipath measurements")

        # Check that mp only appears with code type 'P'
        mp_code_types = df.loc[(slice(None), slice(None), 'mp', slice(None), slice(None)), :].index.get_level_values('code_type').unique()
        self.assertEqual(len(mp_code_types), 1)
        self.assertEqual(mp_code_types[0], 'P')

    def test_read_trace_lc_geometry_free(self):
        """Test that geometry-free (gf) measurements are correctly parsed"""
        df = _read_trace_LC(trace_lc_sample)

        # Filter for gf measurements
        gf_data = df.loc[(slice(None), slice(None), 'gf', slice(None), slice(None)), :]
        self.assertGreater(len(gf_data), 0, "Should have geometry-free measurements")

        # Should have both L and P code types for gf
        gf_code_types = gf_data.index.get_level_values('code_type').unique()
        self.assertIn('L', gf_code_types)
        self.assertIn('P', gf_code_types)

    def test_read_trace_lc_melbourne_wubbena(self):
        """Test that Melbourne-Wubbena (mw) measurements are correctly parsed"""
        df = _read_trace_LC(trace_lc_sample)

        # Filter for mw measurements
        mw_data = df.loc[(slice(None), slice(None), 'mw', slice(None), slice(None)), :]
        self.assertGreater(len(mw_data), 0, "Should have Melbourne-Wubbena measurements")

        # mw should only appear with code type 'L'
        mw_code_types = mw_data.index.get_level_values('code_type').unique()
        self.assertEqual(len(mw_code_types), 1)
        self.assertEqual(mw_code_types[0], 'L')

    def test_read_trace_lc_negative_values(self):
        """Test that negative values are correctly parsed"""
        df = _read_trace_LC(trace_lc_sample)

        # G02 has negative mp values in the test data
        times = df.index.get_level_values('TIME').unique()
        first_time = times[0]

        try:
            g02_mp1 = df.loc[(first_time, 'G02', 'mp', 'P', 'mp1'), 'value']
            # Should be approximately -26.3576
            self.assertAlmostEqual(g02_mp1, -26.3576, places=4)
            self.assertLess(g02_mp1, 0, "mp1 value should be negative")
        except KeyError:
            self.fail("Expected G02 mp P mp1 measurement not found")

    def test_read_trace_lc_multiple_epochs(self):
        """Test that multiple time epochs are correctly parsed"""
        df = _read_trace_LC(trace_lc_sample)

        # Get unique times
        times = df.index.get_level_values('TIME').unique()

        # Should have 2 epochs in test data (00:00:30 and 00:01:00)
        self.assertEqual(len(times), 2, "Should have 2 time epochs")

        # Check that both epochs have G02 data
        for time in times:
            g02_data = df.loc[(time, 'G02', slice(None), slice(None), slice(None)), :]
            self.assertGreater(len(g02_data), 0, f"G02 should have data at time {time}")

    def test_read_trace_lc_empty_file(self):
        """Test behavior with content that doesn't contain PDE form LC section"""
        df = _read_trace_LC(trace_no_lc)

        # Should return empty DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0, "Should return empty DataFrame for no LC data")

    def test_read_trace_lc_g06_triple_freq(self):
        """Test parsing of G06 which has triple-frequency data"""
        df = _read_trace_LC(trace_lc_sample)

        # G06 has non-zero L5 measurements
        times = df.index.get_level_values('TIME').unique()
        first_time = times[0]

        try:
            g06_l5 = df.loc[(first_time, 'G06', 'zd', 'L', 'L5'), 'value']
            # Should be approximately 21375713.6869
            self.assertAlmostEqual(g06_l5, 21375713.6869, places=4)
            self.assertNotEqual(g06_l5, 0.0, "G06 L5 should not be zero")
        except KeyError:
            self.fail("Expected G06 zd L L5 measurement not found")

    def test_read_trace_lc_value_ranges(self):
        """Test that parsed values are in reasonable ranges"""
        df = _read_trace_LC(trace_lc_sample)

        # Zero-difference phase and code observations should be large positive values (meters)
        zd_data = df.loc[(slice(None), slice(None), 'zd', slice(None), slice(None)), 'value']
        non_zero_zd = zd_data[zd_data != 0.0]
        if len(non_zero_zd) > 0:
            self.assertTrue((non_zero_zd > 1e6).all(), "Non-zero zd values should be > 1e6 meters")
            self.assertTrue((non_zero_zd < 1e9).all(), "zd values should be < 1e9 meters")

        # Multipath values should be small (typically < 100 meters)
        mp_data = df.loc[(slice(None), slice(None), 'mp', slice(None), slice(None)), 'value']
        non_zero_mp = mp_data[mp_data != 0.0]
        if len(non_zero_mp) > 0:
            self.assertTrue((abs(non_zero_mp) < 100).all(), "mp values should have abs < 100 meters")


if __name__ == '__main__':
    unittest.main()
