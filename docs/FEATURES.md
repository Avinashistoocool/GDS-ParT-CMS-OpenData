# Feature mapping: CMS PF candidates -> GDS-ParT inputs

The model consumes 17 per-particle features and 4 pairwise features exactly as
built by `gds_part/data/jetclass_cache.py` (`_process_chunk`,
`pairwise_features`). This repo never re-implements them: each source is
converted to JetClass branch names and passed through that code.

| # | feature (normalized as in training) | JetClass (Delphes) | CMS data (PFNano, rec. 31308/31313) | CMS sim (rec. 12102) | status |
|---|---|---|---|---|---|
| 0-3 | log pt, log E, log pt/pt_jet, log E/E_jet | Delphes eflow | PFCands pt, eta, phi, mass | pfcand_ptrel x fj_pt, etarel, phirel, mass | exact |
| 4-6 | dR, deta, dphi to jet axis | `part_deta` = (eta-eta_jet)·sign(eta_jet) | same convention, recomputed | `pfcand_etarel` has the same sign convention (verified) | exact |
| 7 | charge | | charge | charge | exact |
| 8-12 | isChargedHadron/NeutralHadron/Photon/Electron/Muon | | \|pdgId\| 211/130/22/11/13; HF hadronic (1) -> NH, HF EM (2) -> photon | one-hot flags | exact (HF approx.) |
| 13 | tanh(d0) | Delphes d0 [mm] | `PFCands_d0` [cm] x 10 | `pfcand_dxy` [cm] x 10 | **approximated**: unit-matched; CMS d0 is w.r.t. the PV, Delphes smearing differs |
| 14 | d0err (clip 0..1) | Delphes [mm] | `PFCands_d0Err` x 10 | \|dxy/dxysig\| x 10 (error not stored) | **approximated** |
| 15 | tanh(dz) | Delphes [mm] | `PFCands_dz` x 10 | `pfcand_dz` x 10 | **approximated** |
| 16 | dzerr (clip 0..1) | Delphes [mm] | `PFCands_dzErr` x 10 | \|dz/dzsig\| x 10 | **approximated** |
| pair 0-3 | ln dR, ln kT, ln z, ln m^2 | from 4-vectors | from 4-vectors | from 4-vectors | exact |

Neutral particles and charged candidates without track information (CMS stores
-1) get 0 for features 13-16, as in JetClass. The jet 4-vector is the sum of the
selected constituents (JetClass convention), not the calibrated CMS jet.

## Jet definition and known mismatches

* **JetClass**: anti-kT R=0.8 on Delphes eflow, 500 < pT < 1000 GeV, |eta| < 2.
* **CMS simulation (12102)**: AK8 *CHS* jets, constituents stored with pT > 0.95 GeV.
* **CMS data (PFNano)**: no jet->constituent links are stored. Constituents are
  PF candidates with pT > 0.95 GeV within dR < 0.8 of the AK8 PUPPI FatJet axis;
  charged hadrons with PUPPI weight 0 (not from the PV) are dropped to emulate
  CHS (`--no-chs` disables this). This is a cone, not an anti-kT clustering, and
  neutral pileup is not removed (CHS does not remove it either).
* Same pT/|eta| window (500-1000 GeV, |eta|<2) applied to the constituent-sum
  jet for all sources; simulation is reweighted to the data jet-pT spectrum.
* The CMS simulation is 80X legacy reco (Moriond17) while the data are UL2016
  reco. Part of any data/simulation difference is therefore a reconstruction
  release difference, not a modelling problem of the tagger; the sliced and
  input-level comparisons are meant to separate these effects.
* The 0.95 GeV constituent threshold is not applied in JetClass (training
  inputs go down to ~0.2 GeV), so all CMS jets have fewer constituents than the
  model saw in training -- a deliberate, documented domain shift.
