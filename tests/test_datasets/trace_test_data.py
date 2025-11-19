# Central record of TRACE test data sets to be shared across unit tests

# Sample TRACE file with PDE cycle slip detection & repair section (epoch timestamps)
# Extracted from real TRACE output with various scenarios:
# - TRIP mode (triple-frequency)
# - DUAL mode (dual-frequency)
# - Low elevation satellites (skipped)
# - Single frequency satellites (skipped)
# - Special values: inf, -inf, nan, -nan
trace_pde_cs_sample = b"""
   *-------- PDE cycle slip detection & repair --------*

PDE-CS GPST       epoch                  prn   el   lamw     gf12    mw12    siggf  sigmw  lamew     gf25    mw25               LC                   N1   N2   N5

PDE-CS GPST TRIP  2025-10-05 00:00:30.00  G18 20.18 0.862  -0.0050 -0.0746   0.0174          5.86  -0.0056 -0.0186      vtpv=     0.4 val=     0.1 thres=  4.10    7    2
PDE-CS GPST       2025-10-05 00:00:30.00  E27  8.80 --low_elevation --
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  G20 36.13 0.862  -0.0042 -0.5642   0.0102                                     vtpv=     1.9 val=     0.6 thres=  5.43    5    2
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  G05 34.78 0.862  -0.0046 -0.2522   0.0105                                     vtpv=     0.3 val=     0.1 thres=  5.43    5    2
PDE-CS GPST       2025-10-05 00:00:30.00  G31  4.49 --low_elevation --
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  E02 58.33 0.751   0.0053  0.2772   0.0071           inf   0.0000     nan      vtpv=     1.0 val=     0.2 thres=  4.10    7    2
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  G25 51.74 0.862  -0.0030 -0.2178   0.0076          5.86   0.0006  0.0142      vtpv=     0.6 val=     0.1 thres=  4.10    7    2
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  G29 40.79 0.862  -0.0009 -0.0186   0.0092                                     vtpv=     0.0 val=     0.0 thres=  5.43    5    2
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  G02 43.34 0.862   0.0087 -0.1644   0.0087                                     vtpv=     1.0 val=     0.3 thres=  5.43    5    2
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  G24 32.11 0.862   0.0250  0.0340   0.0113          5.86   0.0063 -0.0024      vtpv=     7.4 val=     1.5 thres=  4.10    7    2
PDE-CS GPST       2025-10-05 00:00:30.00  R22 21.30 --single frequency--

PDE-CS GPST DUAL  2025-10-05 00:00:30.00  G12 66.48 0.862   0.0056 -0.0860   0.0065                                     vtpv=     1.0 val=     0.3 thres=  5.43    5    2
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  E15 45.88 0.751  -0.0047 -0.1934   0.0084           inf   0.0000     nan      vtpv=     0.6 val=     0.1 thres=  4.10    7    2
PDE-CS GPST       2025-10-05 00:00:30.00  E25 10.77 --low_elevation --
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  R11 40.64 0.842  -0.0139  0.0947   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  E30 60.88 0.751  -0.0015 -0.0691   0.0069           inf   0.0000     nan      vtpv=     0.1 val=     0.0 thres=  4.10    7    2
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  R21 54.08 0.841  -0.0029 -0.0481   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  E18 32.26 0.751   0.0098  0.2184   0.0112           inf   0.0000     nan      vtpv=     1.0 val=     0.2 thres=  4.10    7    2
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  E36 22.88 0.751   0.0169 -0.2148   0.0154           inf   0.0000     nan      vtpv=     1.6 val=     0.3 thres=  4.10    7    2
PDE-CS GPST TRIP  2025-10-05 00:00:30.00  G11 35.23 0.862   0.0098  0.0367   0.0104          5.86   0.0053  0.0471      vtpv=     2.0 val=     0.4 thres=  4.10    7    2
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  R20 30.68 0.842   0.0147 -0.0777   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST DUAL  2025-10-05 00:00:30.00  R09 28.41 0.843   0.0359 -0.1926   0.0000                                     vtpv=    -nan val=    -nan thres=  5.43    5    2
PDE-CS GPST       2025-10-05 00:00:30.00  R10 79.95 --single frequency--

   *-------- PDE cycle slip detection & repair --------*

PDE-CS GPST       epoch                  prn   el   lamw     gf12    mw12    siggf  sigmw  lamew     gf25    mw25               LC                   N1   N2   N5

PDE-CS GPST TRIP  2025-10-05 00:01:00.00  G18 20.37 0.862  -0.0112  0.1482   0.0172          5.86  -0.0014 -0.0179      vtpv=     0.2 val=     0.0 thres=  4.10    7    2
PDE-CS GPST       2025-10-05 00:01:00.00  E27  8.94 --low_elevation --
PDE-CS GPST DUAL  2025-10-05 00:01:00.00  G20 36.15 0.862  -0.0005  0.1254   0.0102                                     vtpv=     1.4 val=     0.5 thres=  5.43    5    2
PDE-CS GPST DUAL  2025-10-05 00:01:00.00  G05 34.92 0.862  -0.0037  0.0210   0.0105                                     vtpv=     0.0 val=     0.0 thres=  5.43    5    2

   *-------- PDE cycle slip detection & repair --------*

detslp_ll: n=30
detslp_ll: slip detected sat=R05 f=F11

detslp_gf: n=30
detslp_gf: sat=G02 gf0=9.597363 gf1=9.595546
detslp_gf: sat=G06 gf0=4.765946 gf1=4.761807
detslp_gf: sat=G20 gf0=1.234567 gf1=1.234890

PDE-CS GPST       epoch                  prn   el   lamw     gf12    mw12    siggf  sigmw  lamew     gf25    mw25               LC                   N1   N2   N5

PDE-CS GPST DUAL  2025-10-05 00:01:30.00  G20 36.20 0.862  -0.0020  0.2000   0.0100                                     vtpv=     1.5 val=     0.5 thres=  5.43    5    2
PDE-CS GPST TRIP  2025-10-05 00:01:30.00  G02 40.10 0.862  -0.0030  0.1500   0.0095          5.86  -0.0010 -0.0150      vtpv=     0.8 val=     0.2 thres=  4.10    7    2
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
PDE-CS GPST       epoch                  prn   el   lamw     gf12    mw12
-RESIDUALS
"""

# Sample TRACE file with residual lines (starting with %)
# Format: % iter date time meas sat recv sig prefit postfit sigma [prefit_ratio postfit_ratio] label
trace_residual_lines_sample = b"""
+RESIDUALS/PPP
#	It	                  Time	        Type	 Sat	 Str	   Code	   Prefit Res	  Postfit Res	      Meas Sigma	Comments
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G06	ALIC	    L1W	  -6.46872547	  -0.01068288	       0.4453146	P-L1W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G06	ALIC	    L2W	 -10.60534228	   0.00575502	       0.4453146	P-L2W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G06	ALIC	    L1W	  10.31029097	   0.00000000	       0.0044531	L-L1W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G06	ALIC	    L2W	  17.00641759	   0.00000000	       0.0044531	L-L2W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G11	ALIC	    L1W	  -5.56421192	   0.04828610	       0.3565402	P-L1W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G11	ALIC	    L2W	  -9.01145024	  -0.02971239	       0.3565402	P-L2W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G11	ALIC	    L1W	   4.64794543	   0.00000000	       0.0035654	L-L1W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G11	ALIC	    L2W	   7.81674548	   0.00000000	       0.0035654	L-L2W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G12	ALIC	    L1W	  -5.87844469	   0.20446519	       0.4738041	P-L1W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G12	ALIC	    L2W	 -10.42941651	  -0.12500941	       0.4738041	P-L2W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G12	ALIC	    L1W	   5.77047900	   0.00000000	       0.0047380	L-L1W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G12	ALIC	    L2W	   8.74317569	   0.00000000	       0.0047380	L-L2W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G15	ALIC	    L1W	  -2.58799870	   0.05719840	       1.1572358	P-L1W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G15	ALIC	    L2W	  -4.21700336	  -0.03652186	       1.1572358	P-L2W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G15	ALIC	    L1W	  20.55671279	   0.00000000	       0.0115724	L-L1W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G15	ALIC	    L2W	  33.86268422	   0.00000000	       0.0115724	L-L2W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G19	ALIC	    L1W	  -7.99138228	  -0.17837123	       0.8579547	P-L1W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G19	ALIC	    L2W	 -12.93456811	   0.10488883	       0.8579547	P-L2W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G19	ALIC	    L1W	   9.90555532	   0.00000000	       0.0085795	L-L1W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G19	ALIC	    L2W	  16.56418275	   0.00000000	       0.0085795	L-L2W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G24	ALIC	    L1W	  -5.57714820	  -0.07411421	       0.3191403	P-L1W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G24	ALIC	    L2W	  -9.03215910	   0.04469046	       0.3191403	P-L2W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G24	ALIC	    L1W	   7.37546559	   0.00000000	       0.0031914	L-L1W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G24	ALIC	    L2W	  12.27975572	   0.00000000	       0.0031914	L-L2W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G25	ALIC	    L1W	  -6.03962189	  -0.29500480	       1.0851047	P-L1W
%	 0	2025-10-05 00:00:00.00	   CODE_MEAS	 G25	ALIC	    L2W	  -9.64299364	   0.17489223	       1.0851047	P-L2W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G25	ALIC	    L1W	  17.05658100	   0.00000000	       0.0108510	L-L1W
%	 0	2025-10-05 00:00:00.00	   PHAS_MEAS	 G25	ALIC	    L2W	  28.37320674	   0.00000000	       0.0108510	L-L2W
-RESIDUALS/PPP
"""

# Sample TRACE file with LARGE STATE ERROR and LARGE MEAS ERROR lines
trace_large_errors_sample = b"""
2025-10-05 23:04:30.00	LARGE MEAS    ERROR OF : 9.16139	AT 19 :	 PHAS_MEAS	 G19	TONG	    L1W
2025-10-05 23:04:30.00	LARGE MEAS    ERROR OF : 8.21844	AT 20 :	 PHAS_MEAS	 G19	TONG	    L2W
2025-10-05 23:05:00.00	LARGE MEAS    ERROR OF : 7.53623	AT 33 :	 PHAS_MEAS	 E23	TONG	    L5Q
2025-10-05 23:07:30.00	LARGE MEAS    ERROR OF : 6.16053	AT 45 :	 PHAS_MEAS	 R20	TONG	    L1C
2025-10-05 23:22:00.00	LARGE MEAS    ERROR OF : 6.4397	AT 20 :	 PHAS_MEAS	 G19	TONG	    L2W
2025-10-05 23:25:30.00	LARGE MEAS    ERROR OF : 6.4015	AT 21 :	 CODE_MEAS	 G19	TONG	    L1W
2025-10-10 06:28:00.00	LARGE STATE   ERROR OF : 8.7594	AT 3 :	   REC_POS	    	ABMF	      Z
2025-10-10 06:32:00.00	LARGE STATE   ERROR OF : 8.38286	AT 1 :	   REC_POS	    	ABMF	      X
2025-10-10 06:32:30.00	LARGE STATE   ERROR OF : 9.43842	AT 1 :	   REC_POS	    	ABMF	      X
2025-10-10 06:32:30.00	LARGE STATE   ERROR OF : 8.74216	AT 1 :	   REC_POS	    	ABMF	      X

"""

# Sample TRACE file with Ambiguity Removed lines (PREPROC and REJECT actions)
# Testing various preprocessing reasons (GF, MW, LLI, SCDIA, lli, singleFreq) and KF rejection
trace_ambiguity_resets_sample = b"""
2025-10-10 01:45:00.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 E08	ABMF	    L1C
2025-10-10 01:54:30.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 G07	ABMF	    L1W
2025-10-10 02:07:00.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 E02	ABMF	    L1C
2025-10-10 02:08:30.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 E08	ABMF	    L5Q
2025-10-10 23:54:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 G31	ABMF	    L1W	- GF	- MW	- SCDIA
2025-10-10 23:54:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 G31	ABMF	    L2W	- LLI	- GF	- MW	- SCDIA
2025-10-10 23:54:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E04	ABMF	    L1C	- GF
2025-10-10 23:54:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E04	ABMF	    L5Q	- GF
2025-10-10 23:54:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E33	ABMF	    L1C	- GF
2025-10-10 23:54:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E33	ABMF	    L5Q	- GF
2025-10-10 23:54:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E04	ABMF	    L1C	- GF
2025-10-10 23:54:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E04	ABMF	    L5Q	- GF
2025-10-10 23:54:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E33	ABMF	    L1C	- GF
2025-10-10 23:54:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E33	ABMF	    L5Q	- GF
2025-10-10 20:53:00.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 G14	TONG	    L2W
2025-10-10 21:04:00.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 E25	TONG	    L5Q
2025-10-10 21:15:00.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 E25	TONG	    L1C
2025-10-10 23:04:30.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 G17	TONG	    L1W
2025-10-10 23:52:30.00	Ambiguity Removed       	-  REJECT	 AMBIGUITY	 R16	TONG	    L1C
2025-10-10 23:53:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E11	TONG	    L1C	- singleFreq
2025-10-10 23:53:00.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E11	TONG	    L5Q	- singleFreq
2025-10-10 23:53:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 G20	TONG	    L1W	- GF
2025-10-10 23:53:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 G20	TONG	    L2W	- GF
2025-10-10 23:53:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E16	TONG	    L1C	- GF
2025-10-10 23:53:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E16	TONG	    L5Q	- GF
2025-10-10 23:53:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 R17	TONG	    L1C	- LLI	- singleFreq
2025-10-10 23:53:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 R17	TONG	    L2C	- singleFreq
2025-10-10 23:54:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E16	TONG	    L1C	- GF
2025-10-10 23:54:30.00	Ambiguity Removed       	- PREPROC	 AMBIGUITY	 E16	TONG	    L5Q	- GF
"""

# Sample TRACE file with detslp (cycle slip detection) blocks
# Includes Melbourne-Wübbena (MW), Geometry-Free (GF), and Loss-of-Lock (LL) detections
trace_detslp_sample = b"""
detslp_mw: epoch=2025-10-05 17:31:30.00 sat=E21 mw0=-0.510183 mw1=-1.049210
detslp_mw: epoch=2025-10-05 17:31:30.00 sat=E08 mw0=129.136976 mw1=129.466777
detslp_mw: epoch=2025-10-05 17:31:30.00 sat=R14 mw0=-65.120641 mw1=-44.321635
detslp_mw: slip detected: epoch=2025-10-05 17:31:30.00 sat=R14 mw0=-65.120641 mw1=-44.321635
detslp_mw: epoch=2025-10-05 17:31:30.00 sat=E18 mw0=0.261886 mw1=1.201919
detslp_mw: epoch=2025-10-05 17:31:30.00 sat=R27 mw0=-63.772798 mw1=-62.089077
detslp_ll: n=53
detslp_ll: slip detected: epoch=2025-10-05 17:32:00.00 sat=G01 f=F5
detslp_gf: n=53
detslp_gf: epoch=2025-10-05 17:32:00.00 sat=G08 gf0=-5.693530 gf1=-5.680146
detslp_gf: epoch=2025-10-05 17:32:00.00 sat=G02 gf0=4.881156 gf1=4.897541
detslp_gf: epoch=2025-10-05 17:32:00.00 sat=E27 gf0=-27.418274 gf1=-27.405408
detslp_gf: epoch=2025-10-05 17:32:00.00 sat=E30 gf0=-61.742250 gf1=-61.701717
detslp_gf: epoch=2025-10-05 17:32:00.00 sat=G04 gf0=0.322484 gf1=0.336804
detslp_gf: epoch=2025-10-05 17:32:00.00 sat=G03 gf0=0.564167 gf1=0.603729
"""

# Empty TRACE file without detslp section
trace_no_detslp = b"""
+STATES
Some state data here
-STATES
+RESIDUALS
Some residual data here
-RESIDUALS
"""

# Sample TRACE file with observation output lines
# Contains three types: OBSERVED, MISSING, and NOT_TRACKED
# Format: date time sat signal pseudorange carrier_phase snr elevation azimuth status
trace_observations_sample = b"""
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R16 sig= L1C P= 20364111.2290 L= 106055068.0070 S= 43.75 el= 49.81 az= 94.66 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R16 sig= L2C P= 20364112.3280 L= 84607819.9080 S= 43.05 el= 49.81 az= 94.66 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R16 sig= L2P P= 20364112.1520 L= 84607795.9190 S= 42.45 el= 49.81 az= 94.66 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R20 sig= L1C P= 23445641.7350 L= 125374343.3240 S= 38.20 el= 12.46 az= 347.36 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R20 sig= L2C P= 23445644.8440 L= 97513393.2910 S= 37.95 el= 12.46 az= 347.36 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R20 sig= L2P P= 23445642.9990 L= 97513376.2760 S= 38.55 el= 12.46 az= 347.36 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R21 sig= L1C P= 21222571.2460 L= 113566258.3830 S= 48.75 el= 36.54 az= 292.25 block= GLO-K1B status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R21 sig= L2C P= 21222571.0930 L= 88329301.9890 S= 45.85 el= 36.54 az= 292.25 block= GLO-K1B status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R21 sig= L2P P= 21222570.3750 L= 88329299.9950 S= 45.40 el= 36.54 az= 292.25 block= GLO-K1B status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R22 sig= L1C P= 22539885.8610 L= 120319428.6380 S= 47.75 el= 20.56 az= 228.57 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R22 sig= L2C P= 22539886.5720 L= 93581794.4910 S= 43.00 el= 20.56 az= 228.57 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 00:24:00.00 sat= R22 sig= L2P P= 22539885.3350 L= 93581787.4920 S= 42.45 el= 20.56 az= 228.57 block= GLO-M status= OBSERVED
obsRec: epoch= 2019-07-18 23:51:00.00 sat= G18 sig= L2S P= NaN L= NaN S= NaN el= 65.23 az= 346.34 block= GPS-IIF status= MISSING
obsRec: epoch= 2019-07-18 23:51:00.00 sat= G22 sig= L2S P= NaN L= NaN S= NaN el= 57.15 az= 182.11 block= GPS-IIR-M status= MISSING
obsRec: epoch= 2019-07-18 23:51:00.00 sat= G23 sig= L2S P= NaN L= NaN S= NaN el= 41.72 az= 262.73 block= GPS-IIIA status= MISSING
obsRec: epoch= 2019-07-18 23:51:00.00 sat= R06 sig= L2C P= NaN L= NaN S= NaN el= 24.80 az= 131.03 block= GLO-M status= MISSING
obsRec: epoch= 2019-07-18 23:51:00.00 sat= R06 sig= L2P P= NaN L= NaN S= NaN el= 24.80 az= 131.03 block= GLO-M status= MISSING
obsRec: epoch= 2019-07-18 23:51:30.00 sat= G11 sig= L2S P= NaN L= NaN S= NaN el= 48.32 az= 305.25 block= GPS-IIF status= MISSING
obsRec: epoch= 2019-07-18 23:51:30.00 sat= G14 sig= L2S P= NaN L= NaN S= NaN el= 17.41 az= 135.54 block= GPS-IIR-M status= MISSING
obsRec: epoch= 2019-07-18 23:51:30.00 sat= G16 sig= L2S P= NaN L= NaN S= NaN el= 7.73 az= 39.77 block= GPS-IIR-M status= MISSING
obsRec: epoch= 2019-07-18 23:51:30.00 sat= G18 sig= L2S P= NaN L= NaN S= NaN el= 64.98 az= 346.54 block= GPS-IIF status= MISSING
obsRec: epoch= 2019-07-18 23:51:30.00 sat= G22 sig= L2S P= NaN L= NaN S= NaN el= 57.29 az= 181.77 block= GPS-IIR-M status= MISSING
obsRec: epoch= 2019-07-18 23:52:00.00 sat= E01 sig= L1C P= NaN L= NaN S= NaN el= 15.30 az= 45.20 block= GAL-1 status= NOT_TRACKED
obsRec: epoch= 2019-07-18 23:52:00.00 sat= E01 sig= L5Q P= NaN L= NaN S= NaN el= 15.30 az= 45.20 block= GAL-1 status= NOT_TRACKED
obsRec: epoch= 2019-07-18 23:52:30.00 sat= E12 sig= L1C P= NaN L= NaN S= NaN el= 22.45 az= 120.50 block= GAL-1 status= NOT_TRACKED
obsRec: epoch= 2019-07-18 23:52:30.00 sat= E12 sig= L5Q P= NaN L= NaN S= NaN el= 22.45 az= 120.50 block= GAL-1 status= NOT_TRACKED
"""

# Empty TRACE file without observation lines
trace_no_observations = b"""
+STATES
Some state data here
-STATES
+RESIDUALS
Some residual data here
-RESIDUALS
"""
