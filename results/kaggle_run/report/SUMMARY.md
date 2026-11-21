# GDS-ParT on CMS Open Data: data vs simulation

### data_JetHT_vs_CMSsim_QCD (A = JetHT data, B = CMS sim QCD, B reweighted to A in jet pT)

| observable | mean A | mean B | KS D | p(KS) | chi2/ndf |
|---|---|---|---|---|---|
| score_QCD | 0.5343 | 0.5217 | 0.052 | 5.7e-59 | 734.4/17 |
| TvsQCD | 0.1319 | 0.1325 | 0.055 | 4.8e-65 | 192.6/19 |
| WvsQCD | 0.1411 | 0.1211 | 0.049 | 1.2e-52 | 521.6/19 |
| HbbvsQCD | 0.1342 | 0.1440 | 0.064 | 6.8e-87 | 251.6/19 |

KS D of `TvsQCD` / `score_QCD` in slices of **jet_pt**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [500, 600) | 19866 | 58918 | 0.057 | 0.055 | 0.538 | 0.522 |
| [600, 700) | 6894 | 44688 | 0.056 | 0.051 | 0.529 | 0.521 |
| [700, 800) | 2749 | 44235 | 0.075 | 0.066 | 0.532 | 0.514 |
| [800, 1000) | 1651 | 68385 | 0.039 | 0.053 | 0.515 | 0.532 |

KS D of `TvsQCD` / `score_QCD` in slices of **abs_eta**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [0.0, 0.5) | 11814 | 80962 | 0.044 | 0.045 | 0.558 | 0.554 |
| [0.5, 1.0) | 10101 | 69807 | 0.062 | 0.059 | 0.546 | 0.532 |
| [1.0, 1.5) | 6055 | 44722 | 0.052 | 0.051 | 0.493 | 0.484 |
| [1.5, 2.0) | 3190 | 20735 | 0.075 | 0.061 | 0.489 | 0.467 |

KS D of `TvsQCD` / `score_QCD` in slices of **n_constituents**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [0, 30) | 9038 | 37375 | 0.025 | 0.015 | 0.746 | 0.750 |
| [30, 45) | 11099 | 67994 | 0.060 | 0.057 | 0.555 | 0.592 |
| [45, 60) | 7136 | 58188 | 0.112 | 0.103 | 0.375 | 0.436 |
| [60, 80) | 3325 | 39372 | 0.122 | 0.123 | 0.278 | 0.327 |
| [80, 200) | 562 | 13297 | 0.110 | 0.117 | 0.258 | 0.297 |

KS D of `TvsQCD` / `score_QCD` in slices of **npv**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [0, 10) | 1676 | 8231 | 0.057 | 0.058 | 0.542 | 0.522 |
| [10, 20) | 21201 | 98486 | 0.041 | 0.041 | 0.534 | 0.525 |
| [20, 30) | 7865 | 81924 | 0.054 | 0.052 | 0.534 | 0.521 |
| [30, 80) | 418 | 27566 | 0.051 | 0.048 | 0.508 | 0.510 |

Input-feature KS D (particle level, normalized as fed to the network): pt_log=0.006, e_log=0.011, logptrel=0.082, logerel=0.074, deltaR=0.022, deta=0.009, dphi=0.013, charge=0.005, isChargedHadron=0.009, isNeutralHadron=0.007, isPhoton=0.015, isElectron=0.001, isMuon=0.001, tanh_d0=0.007, d0err=0.030, tanh_dz=0.007, dzerr=0.056

### CMSsim_QCD_vs_JetClass_QCD (A = CMS sim QCD, B = JetClass QCD, B reweighted to A in jet pT)

| observable | mean A | mean B | KS D | p(KS) | chi2/ndf |
|---|---|---|---|---|---|
| score_QCD | 0.5234 | 0.6306 | 0.222 | 0 | 6784.3/17 |
| TvsQCD | 0.1372 | 0.0602 | 0.267 | 0 | 9266.4/19 |
| WvsQCD | 0.1137 | 0.1298 | 0.162 | 0 | 3188.0/19 |
| HbbvsQCD | 0.1432 | 0.0519 | 0.364 | 0 | 18471.8/19 |

KS D of `TvsQCD` / `score_QCD` in slices of **jet_pt**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [500, 600) | 58918 | 25876 | 0.254 | 0.213 | 0.522 | 0.622 |
| [600, 700) | 44688 | 12787 | 0.261 | 0.216 | 0.520 | 0.622 |
| [700, 800) | 44235 | 6417 | 0.286 | 0.247 | 0.515 | 0.635 |
| [800, 1000) | 68385 | 4920 | 0.274 | 0.231 | 0.532 | 0.641 |

KS D of `TvsQCD` / `score_QCD` in slices of **abs_eta**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [0.0, 0.5) | 80962 | 19200 | 0.242 | 0.181 | 0.556 | 0.629 |
| [0.5, 1.0) | 69807 | 15985 | 0.260 | 0.215 | 0.531 | 0.629 |
| [1.0, 1.5) | 44722 | 10469 | 0.310 | 0.286 | 0.480 | 0.634 |
| [1.5, 2.0) | 20735 | 4346 | 0.326 | 0.302 | 0.463 | 0.639 |

KS D of `TvsQCD` / `score_QCD` in slices of **n_constituents**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [0, 30) | 37375 | 21846 | 0.249 | 0.253 | 0.741 | 0.775 |
| [30, 45) | 67994 | 14805 | 0.161 | 0.092 | 0.591 | 0.592 |
| [45, 60) | 58188 | 8385 | 0.139 | 0.105 | 0.455 | 0.487 |
| [60, 80) | 39372 | 4117 | 0.278 | 0.140 | 0.365 | 0.438 |
| [80, 200) | 13297 | 847 | 0.488 | 0.284 | 0.335 | 0.461 |

Input-feature KS D (particle level, normalized as fed to the network): pt_log=0.172, e_log=0.173, logptrel=0.216, logerel=0.216, deltaR=0.090, deta=0.043, dphi=0.040, charge=0.059, isChargedHadron=0.115, isNeutralHadron=0.008, isPhoton=0.119, isElectron=0.005, isMuon=0.000, tanh_d0=0.075, d0err=0.237, tanh_dz=0.062, dzerr=0.118

### Data vs CMS simulation diagnostics

| jet variable | mean data | mean sim (pT-rw) | KS D |
|---|---|---|---|
| n_constituents | 40.09 | 45.86 | 0.133 |
| npv | 16.73 | 20.76 | 0.246 |
| jet_mass | 94.98 | 99.27 | 0.076 |
| msd | 59.78 | 57.15 | 0.017 |
| jet_pt | 598.78 | 599.12 | 0.006 |

constituent-sum pT / NanoAOD jet pT: data 0.895, sim 0.977

Tagger outputs after reweighting simulation in (jet pT x n_constituents):

| observable | mean data | mean sim | KS D | p(KS) | chi2/ndf |
|---|---|---|---|---|---|
| score_QCD | 0.5343 | 0.5718 | 0.060 | 6e-75 | 546.5/17 |
| TvsQCD | 0.1319 | 0.1022 | 0.059 | 6.7e-72 | 544.7/19 |
| WvsQCD | 0.1411 | 0.1166 | 0.068 | 1.4e-97 | 592.0/19 |
| HbbvsQCD | 0.1342 | 0.1226 | 0.031 | 3.2e-20 | 127.0/19 |

### ttbar mu+jets control region

- SingleMuon W-like msd 65-105: n=8, mean TvsQCD=0.325, frac(TvsQCD>0.5)=0.125
- SingleMuon top-like msd 105-210: n=33, mean TvsQCD=0.700, frac(TvsQCD>0.5)=0.727
- JetHT dijet: n=31160, mean TvsQCD=0.132, frac(TvsQCD>0.5)=0.088

- HbbvsQCD ROC AUC on CMS full simulation (truth labels): 0.9745

- HbbvsQCD ROC AUC on JetClass (same pT/eta window): 0.9983
