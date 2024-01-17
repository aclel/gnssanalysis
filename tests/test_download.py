import unittest
import datetime
from gnssanalysis.gn_download import gen_prod_filename


class TestLongFilenameGeneration(unittest.TestCase):
    def test_long_filename_for_sp3(self):
        dt = datetime.date(2023, 2, 1)
        result = gen_prod_filename(dt, "IGS", "", "sp3", solution_type="FIN")
        expected = "IGS0OPSFIN_20230320000_01D_15M_ORB.SP3.gz"
        self.assertEqual(result[0], expected)

    def test_long_filename_for_clk(self):
        dt = datetime.date(2023, 2, 1)
        result = gen_prod_filename(dt, "IGS", "", "clk", solution_type="FIN")
        expected = "IGS0OPSFIN_20230320000_01D_05M_CLK.CLK.gz"
        self.assertEqual(result[0], expected)

    def test_long_filename_for_bia(self):
        dt = datetime.date(2023, 2, 1)
        result = gen_prod_filename(dt, "IGS", "", "bia", solution_type="FIN")
        expected = "IGS0OPSFIN_20230320000_01D_01D_OSB.BIA.gz"
        self.assertEqual(result[0], expected)

    def test_long_filename_for_erp_weekly(self):
        # 30-Nov-2023 is a Thurs and the weekly files are on Sundays
        dt = datetime.date(2023, 11, 30)
        result = gen_prod_filename(dt, "IGS", "", "erp", wkly_file=True, solution_type="FIN")
        expected = "IGS0OPSFIN_20233300000_07D_01D_ERP.ERP.gz"
        self.assertEqual(result[0], expected)
