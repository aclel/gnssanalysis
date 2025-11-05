# Central record of .POS test data sets to be shared across unit tests

# Sample Ginan .POS file (station position time series)
pos_sample = b"""PBO Station Position Time Series. Reference Frame : IGS20
Format Version: 2.0.0
4-character ID: TONG
First Epoch   : 2025-10-05T00:00:00.00
XYZ Reference position :  -5930303.467855 -500149.262879 -2286366.307619 (IGS20)
NEU Reference position :  -21.144714143866 -175.179203345436 56.287189315 (IGS20/WGS84)
Start Field Description
YYYY-MM-DDTHH:MM:SS.SSS  Date and Time of given position epoch (GPS Time)
YYYY.YYYYYYYYY          Decimal year of given position epoch (GPS Time)
X                       X coordinate, Specified Reference Frame, meters
Y                       Y coordinate, Specified Reference Frame, meters
Z                       Z coordinate, Specified Reference Frame, meters
Sx                      Sigma of the X position
Sy                      Sigma of the Y position
Sz                      Sigma of the Z position
Rxy                     Correlation between the X and Y position
Rxz                     Correlation between the X and Z position
Ryz                     Correlation between the Y and Z position
Nlat                    North latitude, WGS-84 ellipsoid, decimal degrees
Elong                   East longitude, WGS-84 ellipsoid, decimal degrees
Height (Up)             Height relative to WGS-84 ellipsoid, meters
dN                      Difference in North component from NEU reference position, meters
dE                      Difference in East component from NEU reference position, meters
dU                      Difference in vertical component from NEU reference position, meters
Sn                      Sigma of dN, meters
Se                      Sigma of dE, meters
Su                      Sigma of dU, meters
Rne                     Correlation between dN and dE
Rnu                     Correlation between dN and dU
Reu                     Correlation between dE and dU
Soln                    Solution type
End Field Description
*YYYY-MM-DDTHH:MM:SS.SSS YYYY.YYYYYYYYY        X             Y              Z           Sx         Sy        Sz      Rxy     Rxz     Ryz        NLat            Elong        Height         dN          dE          dU        Sn       Se         Su       Rne     Rnu     Reu  soln
 2025-10-05T00:00:00.000 2025.761643265 -5930303.49615 -500149.25187 -2286366.31796   0.00244   0.00159   0.00093   0.069   0.868   0.048  -21.1447141422 -175.1792034739    56.31635     0.00019    -0.01335     0.02917   0.00045   0.00158   0.00258   0.111   0.225  -0.014 ginan
 2025-10-05T00:00:30.000 2025.761644216 -5930303.49615 -500149.25187 -2286366.31796   0.00244   0.00159   0.00093   0.069   0.868   0.048  -21.1447141422 -175.1792034739    56.31635     0.00019    -0.01335     0.02917   0.00045   0.00158   0.00258   0.111   0.225  -0.014 ginan
 2025-10-05T00:01:00.000 2025.761645167 -5930303.49615 -500149.25187 -2286366.31796   0.00244   0.00159   0.00093   0.069   0.868   0.048  -21.1447141422 -175.1792034739    56.31635     0.00019    -0.01335     0.02917   0.00045   0.00158   0.00258   0.111   0.225  -0.014 ginan
 2025-10-05T00:01:30.000 2025.761646119 -5930303.49615 -500149.25187 -2286366.31796   0.00244   0.00159   0.00093   0.069   0.868   0.048  -21.1447141422 -175.1792034739    56.31635     0.00019    -0.01335     0.02917   0.00045   0.00158   0.00258   0.111   0.225  -0.014 ginan
 2025-10-05T00:02:00.000 2025.761647070 -5930303.49615 -500149.25187 -2286366.31796   0.00244   0.00159   0.00093   0.069   0.868   0.048  -21.1447141422 -175.1792034739    56.31635     0.00019    -0.01335     0.02917   0.00045   0.00158   0.00258   0.111   0.225  -0.014 ginan
"""

# Empty .POS file without data section
pos_no_data = b"""PBO Station Position Time Series. Reference Frame : IGS20
Format Version: 2.0.0
4-character ID: TEST
"""
