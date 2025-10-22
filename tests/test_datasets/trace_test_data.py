# Central record of TRACE test data sets to be shared across unit tests

# Sample TRACE file with PDE cycle slip detection & repair section
# Extracted from real TRACE output with various scenarios:
# - TRIP mode (triple-frequency)
# - DUAL mode (dual-frequency)
# - Low elevation satellites (skipped)
# - Single frequency satellites (skipped)
# - Special values: inf, -inf, nan, -nan
trace_pde_cs_sample = b"""
   *-------- PDE cycle slip detection & repair --------*

PDE-CS GPST       week      sec  prn   el   lamw     gf12    mw12    siggf  sigmw  lamew     gf25    mw25               LC                   N1   N2   N5

PDE-CS GPST TRIP  2190 518430.0  G18 20.18 0.862  -0.0050 -0.0746   0.0174          5.86  -0.0056 -0.0186      vtpv=     0.4 val=     0.1 thres=  4.10    7    2
PDE-CS GPST       2190 518430.0  E27  8.80 --low_elevation --
PDE-CS GPST DUAL  2190 518430.0  G20 36.13 0.862  -0.0042 -0.5642   0.0102                                     vtpv=     1.9 val=     0.6 thres=  5.43    5    2
PDE-CS GPST DUAL  2190 518430.0  G05 34.78 0.862  -0.0046 -0.2522   0.0105                                     vtpv=     0.3 val=     0.1 thres=  5.43    5    2
PDE-CS GPST       2190 518430.0  G31  4.49 --low_elevation --
PDE-CS GPST TRIP  2190 518430.0  E02 58.33 0.751   0.0053  0.2772   0.0071           inf   0.0000     nan      vtpv=     1.0 val=     0.2 thres=  4.10    7    2
PDE-CS GPST TRIP  2190 518430.0  G25 51.74 0.862  -0.0030 -0.2178   0.0076          5.86   0.0006  0.0142      vtpv=     0.6 val=     0.1 thres=  4.10    7    2
PDE-CS GPST DUAL  2190 518430.0  G29 40.79 0.862  -0.0009 -0.0186   0.0092                                     vtpv=     0.0 val=     0.0 thres=  5.43    5    2
PDE-CS GPST DUAL  2190 518430.0  G02 43.34 0.862   0.0087 -0.1644   0.0087                                     vtpv=     1.0 val=     0.3 thres=  5.43    5    2
PDE-CS GPST TRIP  2190 518430.0  G24 32.11 0.862   0.0250  0.0340   0.0113          5.86   0.0063 -0.0024      vtpv=     7.4 val=     1.5 thres=  4.10    7    2
PDE-CS GPST       2190 518430.0  R22 21.30 --single frequency--

PDE-CS GPST DUAL  2190 518430.0  G12 66.48 0.862   0.0056 -0.0860   0.0065                                     vtpv=     1.0 val=     0.3 thres=  5.43    5    2
PDE-CS GPST TRIP  2190 518430.0  E15 45.88 0.751  -0.0047 -0.1934   0.0084           inf   0.0000     nan      vtpv=     0.6 val=     0.1 thres=  4.10    7    2
PDE-CS GPST       2190 518430.0  E25 10.77 --low_elevation --
PDE-CS GPST DUAL  2190 518430.0  R11 40.64 0.842  -0.0139  0.0947   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST TRIP  2190 518430.0  E30 60.88 0.751  -0.0015 -0.0691   0.0069           inf   0.0000     nan      vtpv=     0.1 val=     0.0 thres=  4.10    7    2
PDE-CS GPST DUAL  2190 518430.0  R21 54.08 0.841  -0.0029 -0.0481   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST TRIP  2190 518430.0  E18 32.26 0.751   0.0098  0.2184   0.0112           inf   0.0000     nan      vtpv=     1.0 val=     0.2 thres=  4.10    7    2
PDE-CS GPST TRIP  2190 518430.0  E36 22.88 0.751   0.0169 -0.2148   0.0154           inf   0.0000     nan      vtpv=     1.6 val=     0.3 thres=  4.10    7    2
PDE-CS GPST TRIP  2190 518430.0  G11 35.23 0.862   0.0098  0.0367   0.0104          5.86   0.0053  0.0471      vtpv=     2.0 val=     0.4 thres=  4.10    7    2
PDE-CS GPST DUAL  2190 518430.0  R20 30.68 0.842   0.0147 -0.0777   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST DUAL  2190 518430.0  R09 28.41 0.843   0.0359 -0.1926   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST       2190 518430.0  R10 79.95 --single frequency--

   *-------- PDE cycle slip detection & repair --------*

PDE-CS GPST       week      sec  prn   el   lamw     gf12    mw12    siggf  sigmw  lamew     gf25    mw25               LC                   N1   N2   N5

PDE-CS GPST TRIP  2190 518460.0  G18 20.37 0.862  -0.0112  0.1482   0.0172          5.86  -0.0014 -0.0179      vtpv=     0.2 val=     0.0 thres=  4.10    7    2
PDE-CS GPST       2190 518460.0  E27  8.94 --low_elevation --
PDE-CS GPST DUAL  2190 518460.0  G20 36.15 0.862  -0.0005  0.1254   0.0102                                     vtpv=     1.4 val=     0.5 thres=  5.43    5    2
PDE-CS GPST DUAL  2190 518460.0  G05 34.92 0.862  -0.0037  0.0210   0.0105                                     vtpv=     0.0 val=     0.0 thres=  5.43    5    2

   *-------- PDE cycle slip detection & repair --------*

detslp_ll: n=30
detslp_ll: slip detected sat=R05 f=F11

detslp_gf: n=30
detslp_gf: sat=G02 gf0=9.597363 gf1=9.595546
detslp_gf: sat=G06 gf0=4.765946 gf1=4.761807
detslp_gf: sat=G20 gf0=1.234567 gf1=1.234890

PDE-CS GPST       week      sec  prn   el   lamw     gf12    mw12    siggf  sigmw  lamew     gf25    mw25               LC                   N1   N2   N5

PDE-CS GPST DUAL  2190 518490.0  G20 36.20 0.862  -0.0020  0.2000   0.0100                                     vtpv=     1.5 val=     0.5 thres=  5.43    5    2
PDE-CS GPST TRIP  2190 518490.0  G02 40.10 0.862  -0.0030  0.1500   0.0095          5.86  -0.0010 -0.0150      vtpv=     0.8 val=     0.2 thres=  4.10    7    2
"""

# Empty TRACE file without PDE-CS section
trace_no_pde_cs = b"""
+STATES
Some state data here
-STATES
+RESIDUALS
Some residual data here
-RESIDUALS
"""

# Sample TRACE file with PDE form LC (linear combination preprocessing) section
# Extracted from real TRACE output showing various linear combinations:
# - zd: zero-difference measurements (L for phase, P for code)
# - mp: multipath (P only)
# - gf: geometry-free combinations (L and P)
# - mw: Melbourne-Wubbena combinations (L only)
# - wl: wide-lane combinations (L only)
# - if: ionosphere-free combinations (L and P)
trace_lc_sample = b"""
   *-------- PDE form LC 2019-01-01 00:00:30.00             --------*
2019-01-01 00:00:30.00 sat= G02 zd L -- L1  = 22093585.6788 L2  = 22093577.8266 L5  =        0.0000
2019-01-01 00:00:30.00 sat= G02 zd P -- P1  = 22093583.5960 P2  = 22093575.9920 P5  =        0.0000
2019-01-01 00:00:30.00 sat= G02 mp P -- mp1 =      -26.3576 mp2 =      -41.8139 mp5 =        0.0000
2019-01-01 00:00:30.00 sat= G02 gf L -- gf12=        7.8522 gf15=        0.0000 gf25=        0.0000
2019-01-01 00:00:30.00 sat= G02 gf P -- gf12=        7.6040 gf15=        0.0000 gf25=        0.0000
2019-01-01 00:00:30.00 sat= G02 mw L -- mw12=       38.4338 mw15=        0.0000 mw25=        0.0000
2019-01-01 00:00:30.00 sat= G02 wl L -- wl12= 22093613.3926 wl15=        0.0000 wl25=        0.0000
2019-01-01 00:00:30.00 sat= G02 if L -- if12= 22093597.8162 if15=        0.0000 if25=        0.0000
2019-01-01 00:00:30.00 sat= G02 if P -- if12= 22093595.3497 if15=        0.0000 if25=        0.0000
2019-01-01 00:00:30.00 sat= G06 zd L -- L1  = 21375713.0424 L2  = 21375714.6819 L5  = 21375713.6869
2019-01-01 00:00:30.00 sat= G06 zd P -- P1  = 21375712.2940 P2  = 21375710.5610 P5  = 21375711.8920
2019-01-01 00:00:30.00 sat= G06 mp P -- mp1 =        4.3200 mp2 =        4.2265 mp5 =        1.1188
2019-01-01 00:00:30.00 sat= G06 gf L -- gf12=       -1.6395 gf15=       -0.6444 gf25=        0.9951
2019-01-01 00:00:30.00 sat= G06 gf P -- gf12=        1.7330 gf15=        0.4020 gf25=       -1.3310
2019-01-01 00:00:30.00 sat= G06 mw L -- mw12=       -4.9646 mw15=       -1.3042 mw25=        4.4968
2019-01-01 00:00:30.00 sat= G06 wl L -- wl12= 21375707.2560 wl15= 21375711.1421 wl25= 21375737.5681
2019-01-01 00:00:30.00 sat= G06 if L -- if12= 21375710.5082 if15= 21375712.2300 if25= 21375725.8815
2019-01-01 00:00:30.00 sat= G06 if P -- if12= 21375714.9727 if15= 21375712.8008 if25= 21375695.5802
   *-------- PDE form LC 2019-01-01 00:01:00.00             --------*
2019-01-01 00:01:00.00 sat= G02 zd L -- L1  = 22093559.6964 L2  = 22093551.8444 L5  =        0.0000
2019-01-01 00:01:00.00 sat= G02 zd P -- P1  = 22093557.6250 P2  = 22093550.0190 P5  =        0.0000
2019-01-01 00:01:00.00 sat= G02 mp P -- mp1 =      -26.3576 mp2 =      -41.8030 mp5 =        0.0000
2019-01-01 00:01:00.00 sat= G02 gf L -- gf12=        7.8520 gf15=        0.0000 gf25=        0.0000
2019-01-01 00:01:00.00 sat= G02 gf P -- gf12=        7.6060 gf15=        0.0000 gf25=        0.0000
2019-01-01 00:01:00.00 sat= G06 zd L -- L1  = 21375623.6164 L2  = 21375625.2561 L5  = 21375624.2610
2019-01-01 00:01:00.00 sat= G06 zd P -- P1  = 21375622.8670 P2  = 21375621.1350 P5  = 21375622.4650
"""

# Empty TRACE file without PDE form LC section
trace_no_lc = b"""
+STATES
Some state data here
-STATES
   *-------- PDE cycle slip detection & repair --------*
PDE-CS GPST       week      sec  prn   el   lamw     gf12    mw12
-RESIDUALS
"""
