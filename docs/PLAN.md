# Plan and status

Goal: run the JetClass-trained GDS-ParT on real CMS Open Data and measure where
its outputs disagree with simulation.

| # | milestone | status |
|---|---|---|
| 1 | Find CMS Open Data with per-jet PF candidates in data and simulation; verify record IDs | **done** (31308, 31313, 12102, 14220; no simulated PFNano exists, see DATASETS.md) |
| 2 | Feature mapper PF candidates -> 17 + 4 features, reusing the training preprocessing | **done** (`features.py`, docs/FEATURES.md) |
| 3 | Control regions: QCD dijet (JetHT), ttbar mu+jets (SingleMuon) with golden JSON | **done** (code); ttbar CR only tested on synthetic events |
| 4 | Inference + data/MC comparison (ratio plots, KS, chi2, slices in pT, eta, n_const, nPV; input-feature KS) | **done** (code) |
| 5 | CPU tests incl. real-checkpoint inference | **done** (`pytest tests`, 7 passed) |
| 6 | Local end-to-end proof on one real file each (JetHT 3k events, CMS sim 6k jets, JetClass 6k jets) | **done**, see `results/local/report/SUMMARY.md` |
| 7 | Full-statistics run on Kaggle | **running**: version 4 of the kernel (CPU, internet on, because of the 2-GPU-session limit; repo metadata stays GPU) with the full-size config (8 JetHT files x 200k events, 60 SingleMuon files, 4 simulation files, 4 JetClass files, 10.5 h budget) |
| 8 | SingleMuon ttbar CR on real data | pending (Kaggle) |
| 9 | Fine-tune on CMS simulation (12102 train split) and redo comparison | pending |
| 10 | Systematic checks: cone vs anti-kT constituents (needs fastjet), CHS emulation on/off, d0 scale | pending |

## Preliminary local result (low statistics, one file each)

* Data (JetHT, 124 jets) vs CMS simulation QCD (pT-reweighted): tagger outputs
  agree within statistics: KS p = 0.35 (QCD score), 0.37 (TvsQCD); HbbvsQCD
  KS p = 0.024 (mild tension, mean 0.163 data vs 0.141 sim).
* CMS simulation vs JetClass (Delphes), both QCD: large shift; KS D = 0.25-0.39,
  p < 1e-40; mean QCD score drops 0.64 -> 0.53; present in every pT/eta slice;
  biggest input-level shifts in d0err (KS D 0.25), log pt/E rel (0.23) and dzerr.
* H->bb vs QCD AUC: 0.972 on CMS simulation vs 0.998 on JetClass in the same
  window: the domain shift costs performance but the tagger still separates.

These numbers are from a few thousand jets and are a pipeline validation, not a
physics result.
