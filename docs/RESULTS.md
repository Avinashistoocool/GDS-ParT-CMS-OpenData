# Results: GDS-ParT on CMS Open Data (Kaggle run, kernel version 4)

Model: GDS-ParT `v2_shared_10M_10ep/best.pt` (JetClass val acc 0.8487), trained
on JetClass (Delphes). Phase space for every sample: constituent-sum jet
500 < pT < 1000 GeV, |eta| < 2. All numbers below come from
`results/kaggle_run/report/summary.json` / `SUMMARY.md`, produced by
`python src\cmsod\analyze.py --in <kaggle output> --out results\kaggle_run\report`.

## What ran

Kaggle kernel `avinashchandragupta/gds-part-cms-open-data`, version 4, **CPU**
(no GPU slot at the time), finished normally in 2.28 h of a 10.5 h budget (the
deadline was never reached).

| source | record | files read | events read | jets scored |
|---|---|---|---|---|
| JetHT 2016G data, QCD dijet CR, golden JSON | 31308 | 7 of 8 requested (all events) | 658,283 | **31,160** (10 runs, 278969-280385) |
| SingleMuon 2016G data, ttbar mu+jets CR, golden JSON | 31313 | 60 | 14,279,635 | **96** (8 W-like, 33 top-like) |
| CMS full sim, QCD + H->bb (80X) | 12102 | 4 test files | - | **268,394** (216,226 QCD, 42,549 H->bb, 9,619 other) |
| JetClass val (Delphes) | Kaggle `suryatrainer/jetclass-val` | 4 (ZJetsToNuNu, HToBB, WToQQ, TTBar) | - | **200,000** (50k each) |

Problem found in the log: the 8th JetHT file (`nano_data2016_1-8.root`) was lost
after ~100k events to a dropped HTTPS connection (`aiohttp ClientPayloadError`
surfacing as `TypeError`), and the whole file was discarded. Fixed in
`pipeline.RetryTree` (reopen + retry the same entry range up to 3 times);
version 5 of the kernel with the fix and a larger config (40 JetHT files, 200
SingleMuon files) was pushed afterwards (see PLAN.md).

## 1. Data vs CMS simulation in the QCD dijet control region

JetHT data (31,160 jets) vs CMS simulation QCD jets (216,226; reweighted to the
data jet-pT spectrum, Kish effective N = 115k). Plots:
`results/kaggle_run/report/data_JetHT_vs_CMSsim_QCD_*.png` (normalized
histograms with data/sim ratio panels).

| observable | mean data | mean sim | KS D | p(KS) | chi2/ndf (20 bins) |
|---|---|---|---|---|---|
| score_QCD | 0.534 | 0.522 | 0.052 | 6e-59 | 734/17 |
| TvsQCD | 0.132 | 0.133 | 0.055 | 5e-65 | 193/19 |
| WvsQCD | 0.141 | 0.121 | 0.049 | 1e-52 | 522/19 |
| HbbvsQCD | 0.134 | 0.144 | 0.064 | 7e-87 | 252/19 |

The **means agree to 0.01-0.02** and the KS distance is only ~0.05, but with
these statistics the shapes are incompatible (p < 1e-50). For scale, the
Delphes-vs-CMS-simulation shift on the same jets is 4-6x larger (section 3).

### Where the disagreement sits (KS D of score_QCD per slice; mean score_QCD data / sim)

| slice variable | bins -> KS D | comment |
|---|---|---|
| jet pT [500,600,700,800,1000) | 0.055, 0.051, 0.066, 0.053 | flat in pT |
| abs eta [0,0.5,1,1.5,2) | 0.045, 0.059, 0.051, 0.061 | mild growth forward |
| nPV [0,10,20,30,80) | 0.058, 0.041, 0.052, 0.048 | **no pileup dependence** |
| n_constituents [0,30,45,60,80,200) | **0.015, 0.057, 0.103, 0.123, 0.117** | grows with multiplicity |

In n_constituents slices the mean QCD score is 0.746/0.750 (data/sim) for
< 30 constituents, but 0.375/0.436 (45-60) and 0.278/0.327 (60-80): **at fixed
multiplicity, data jets look less QCD-like than simulated ones**, by up to 0.06
in mean score. Profiles: `data_JetHT_vs_CMSsim_QCD_profile_{score_QCD,TvsQCD,HbbvsQCD}.png`.

### Jet-level inputs (sim pT-reweighted)

| variable | data | sim | KS D |
|---|---|---|---|
| n_constituents (pT > 0.95 GeV) | 40.1 | 45.9 | 0.133 |
| nPV | 16.7 | 20.8 | 0.246 |
| jet mass (constituent sum) [GeV] | 95.0 | 99.3 | 0.076 |
| soft-drop mass (stored) [GeV] | 59.8 | 57.2 | 0.017 |
| constituent-sum pT / stored jet pT | 0.895 | 0.977 | - |

Data jets have ~6 fewer constituents. Since fewer constituents push the tagger
towards QCD, this **partly cancels** the per-multiplicity shift above: after
reweighting simulation in (pT x n_constituents) the agreement gets *worse* for
score_QCD (means 0.534 vs 0.572, KS D 0.060) and TvsQCD (0.132 vs 0.102, KS D
0.059), and better only for HbbvsQCD (KS D 0.031). The near-agreement of the
global means is therefore partly a cancellation, not evidence that the tagger
is well modelled. Plots: `data_JetHT_vs_CMSsim_QCD_rwNconst_*.png`.

Particle-level inputs (KS D, as fed to the network): largest are logptrel 0.082,
logerel 0.074, dzerr 0.056, d0err 0.030; all others <= 0.022. The relative-pT
shift is consistent with the constituent-sum/stored pT ratio (0.895 vs 0.977),
i.e. with the cone-based constituent definition in data vs CHS anti-kT
constituents in simulation, more than with a physics difference.

## 2. ttbar mu+jets control region (data only, very low statistics)

Only 96 SingleMuon jets passed (pT > 500 GeV boosted selection, 14.3M events).
Mean TvsQCD: top-like (msd 105-210, n = 33) **0.70**, 73% above 0.5; W-like
(msd 65-105, n = 8) 0.33; JetHT dijets 0.13 (8.8% above 0.5). The tagger does
identify boosted tops in real data, qualitatively. No ttbar simulation with PF
candidates exists on the portal, so there is no data/MC comparison here.

## 3. CMS simulation vs JetClass (Delphes), both QCD

| observable | mean CMS sim | mean JetClass | KS D |
|---|---|---|---|
| score_QCD | 0.523 | 0.631 | 0.222 |
| TvsQCD | 0.137 | 0.060 | 0.267 |
| HbbvsQCD | 0.143 | 0.052 | 0.364 |

Present in every pT slice (KS D 0.21-0.25 for score_QCD), grows with |eta|
(0.18 central -> 0.30 at 1.5-2.0) and is largest for low (< 30) and high (> 80)
multiplicity. Input-level KS D: d0err 0.237, logptrel/logerel 0.216, pt_log
0.172, isPhoton 0.119, dzerr 0.118, isChargedHadron 0.115. H->bb vs QCD ROC
AUC: **0.9745 on CMS full simulation vs 0.9983 on JetClass**.

Arrays committed in `results/kaggle_run/*.npz` contain the per-jet scores and
jet variables. The particle-level `part_feats` samples are left out to keep the
files small, so the input-feature plots need the full Kaggle output.

## Summary

* Data vs CMS simulation (QCD dijets): small (KS D ~0.05, means within 0.02)
  but highly significant differences. They don't depend on pT or pileup.
  They grow with constituent multiplicity (KS D 0.015 -> 0.12), and a lower
  constituent count in data partly hides them.
* The simulation-domain gap (Delphes -> CMS full sim) is 4-6x larger than the
  data/MC gap and is dominated by impact-parameter errors and relative-pT
  inputs. It costs ~2.4 points of H->bb AUC but the tagger still separates.

## Caveats (read before quoting any number)

* **Delphes training.** The model has never seen CMS reconstruction. Impact
  parameters and their errors are unit-matched but not equivalent (FEATURES.md).
* **Older simulation reco than the data.** The simulation (rec. 12102) is 80X
  Moriond17 reco with CHS AK8 constituents. The data are UL2016 PFNano, with
  cone-based (dR < 0.8 around the PUPPI FatJet) constituents and CHS emulated
  through PUPPI weights. Part of the data/MC difference is reconstruction
  release and constituent definition, not tagger mismodelling. The 0.895 vs 0.977
  pT-recovery ratio shows this directly.
* **Pileup not reweighted.** Simulation nPV (mean 20.8) differs from data
  (PV_npvsGood, 16.7) and the two nPV definitions may differ. The flat nPV slices
  suggest this matters little.
* **No ttbar MC.** The ttbar CR has 96 jets in data and no simulation to
  compare to. No W/Z/top-enriched data/MC comparison is possible yet.
* **Simulation QCD is the 12102 QCD sample, not a JetHT-triggered sample.** Only
  the jet pT spectrum (and optionally n_constituents) is reweighted.
  Quark/gluon fractions and generator tunes are not matched.
* Statistical tests use unbinned weighted KS with Kish effective N and a
  20-bin shape chi2. Only statistical errors, no systematics. p-values of
  1e-50 mean "different shapes", not "large difference".
* One of the 8 requested JetHT files was lost to a network error (fixed in code).
  The JetHT sample is 10 runs of 2016G and is not representative of the full era.
