# GDS-ParT on CMS Open Data: data vs simulation

### data_JetHT_vs_CMSsim_QCD (A = JetHT data, B = CMS sim QCD, B reweighted to A in jet pT)

| observable | mean A | mean B | KS D | p(KS) | chi2/ndf |
|---|---|---|---|---|---|
| score_QCD | 0.5206 | 0.5227 | 0.090 | 0.35 | 23.1/17 |
| TvsQCD | 0.1386 | 0.1289 | 0.089 | 0.37 | 28.0/19 |
| WvsQCD | 0.1455 | 0.1240 | 0.080 | 0.51 | 27.7/18 |
| HbbvsQCD | 0.1633 | 0.1412 | 0.144 | 0.024 | 39.3/19 |

KS D of `TvsQCD` / `score_QCD` in slices of **jet_pt**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [500, 600) | 93 | 422 | 0.121 | 0.104 | 0.542 | 0.523 |

KS D of `TvsQCD` / `score_QCD` in slices of **abs_eta**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|

KS D of `TvsQCD` / `score_QCD` in slices of **n_constituents**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|

KS D of `TvsQCD` / `score_QCD` in slices of **npv**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [10, 20) | 79 | 718 | 0.085 | 0.101 | 0.510 | 0.525 |

Input-feature KS D (particle level, normalized as fed to the network): pt_log=0.019, e_log=0.023, logptrel=0.099, logerel=0.089, deltaR=0.023, deta=0.019, dphi=0.010, charge=0.002, isChargedHadron=0.000, isNeutralHadron=0.014, isPhoton=0.015, isElectron=0.001, isMuon=0.001, tanh_d0=0.014, d0err=0.025, tanh_dz=0.006, dzerr=0.042

### CMSsim_QCD_vs_JetClass_QCD (A = CMS sim QCD, B = JetClass QCD, B reweighted to A in jet pT)

| observable | mean A | mean B | KS D | p(KS) | chi2/ndf |
|---|---|---|---|---|---|
| score_QCD | 0.5262 | 0.6392 | 0.252 | 1.6e-45 | 282.0/17 |
| TvsQCD | 0.1324 | 0.0573 | 0.310 | 1.6e-68 | 194.6/19 |
| WvsQCD | 0.1158 | 0.1243 | 0.194 | 4.1e-27 | 135.7/19 |
| HbbvsQCD | 0.1401 | 0.0484 | 0.387 | 1.1e-106 | 386.2/19 |

KS D of `TvsQCD` / `score_QCD` in slices of **jet_pt**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [500, 600) | 422 | 1593 | 0.289 | 0.241 | 0.526 | 0.625 |
| [600, 700) | 349 | 747 | 0.317 | 0.260 | 0.513 | 0.625 |
| [700, 800) | 324 | 376 | 0.299 | 0.237 | 0.513 | 0.640 |
| [800, 1000) | 520 | 284 | 0.348 | 0.283 | 0.544 | 0.660 |

KS D of `TvsQCD` / `score_QCD` in slices of **abs_eta**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [0.0, 0.5) | 603 | 1175 | 0.288 | 0.216 | 0.553 | 0.636 |
| [0.5, 1.0) | 517 | 941 | 0.315 | 0.257 | 0.536 | 0.644 |
| [1.0, 1.5) | 347 | 642 | 0.350 | 0.321 | 0.489 | 0.642 |
| [1.5, 2.0) | 148 | 242 | 0.309 | 0.279 | 0.471 | 0.630 |

KS D of `TvsQCD` / `score_QCD` in slices of **n_constituents**:

| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |
|---|---|---|---|---|---|---|
| [0, 30) | 268 | 1318 | 0.281 | 0.273 | 0.728 | 0.786 |
| [30, 45) | 511 | 912 | 0.247 | 0.140 | 0.596 | 0.612 |
| [45, 60) | 469 | 462 | 0.136 | 0.104 | 0.459 | 0.472 |
| [60, 80) | 278 | 253 | 0.312 | 0.162 | 0.366 | 0.444 |
| [80, 200) | 89 | 55 | 0.325 | 0.180 | 0.374 | 0.438 |

Input-feature KS D (particle level, normalized as fed to the network): pt_log=0.180, e_log=0.174, logptrel=0.229, logerel=0.233, deltaR=0.108, deta=0.051, dphi=0.071, charge=0.064, isChargedHadron=0.127, isNeutralHadron=0.009, isPhoton=0.129, isElectron=0.005, isMuon=0.001, tanh_d0=0.072, d0err=0.254, tanh_dz=0.071, dzerr=0.145

- HbbvsQCD ROC AUC on CMS full simulation (truth labels): 0.9723

- HbbvsQCD ROC AUC on JetClass (same pT/eta window): 0.9982
