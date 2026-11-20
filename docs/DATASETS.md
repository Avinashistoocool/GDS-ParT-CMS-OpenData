# Datasets (all verified via `https://opendata.cern.ch/api/records/<id>` on 2026-11-21)

| role | record | title | files / size | access |
|---|---|---|---|---|
| collision data, QCD dijet CR | [31308](https://opendata.cern.ch/record/31308) | JetHT dataset in NanoAOD format enhanced with Particle Flow candidates from RunG of 2016 | 842 files, 120.5 M events | `root://eospublic.cern.ch//eos/opendata/cms/derived-data/PFNano/29-Feb-24/JetHT/Run2016G-UL2016_MiniAODv2_PFNanoAODv1/240218_191008/0000/nano_data2016_*.root` |
| collision data, ttbar mu+jets CR | [31313](https://opendata.cern.ch/record/31313) | SingleMuon dataset in NanoAOD format enhanced with Particle Flow candidates from RunG of 2016 | 381 files, 149.9 M events | `.../PFNano/29-Feb-24/SingleMuon/Run2016G-UL2016_MiniAODv2_PFNanoAODv1/240207_205649/0000/nano_data2016_*.root` |
| simulation (QCD + H->bb AK8 jets, PF candidates, truth labels) | [12102](https://opendata.cern.ch/record/12102), DOI [10.7483/OPENDATA.CMS.JGJX.MS7Q](https://doi.org/10.7483/OPENDATA.CMS.JGJX.MS7Q) | Sample with jet, track and secondary vertex properties for Hbb tagging ML studies HiggsToBBNTuple_HiggsToBB_QCD_RunII_13TeV_MC (J. Duarte) | 91 ROOT files (9 test), ~1.2 GB each, 200k jets each | `root://eospublic.cern.ch//eos/opendata/cms/datascience/HiggsToBBNtupleProducerTool/HiggsToBBNTuple_HiggsToBB_QCD_RunII_13TeV_MC/test/ntuple_merged_*.root` |
| validated lumi sections 2016 | [14220](https://opendata.cern.ch/record/14220) | Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt | 1 | `.../eos/opendata/cms/validated-runs/2016/...` |
| PFNano producer | [12504](https://opendata.cern.ch/record/12504) | PFNano producer tool for CMS 2016 | software | |
| JetClass (training domain, Delphes) | Zenodo 6619768; Kaggle mirror `suryatrainer/jetclass-val` | JetClass val_5M | | Kaggle dataset source |

Every `root://eospublic.cern.ch//eos/opendata/...` path is also served over HTTPS at
`https://opendata.cern.ch/eos/opendata/...`, which is what the code uses (works
from Kaggle and Windows without XRootD).

Other PFNano 2016G collision records exist: 31300-31316 (BTagCSV, BTagMu,
Charmonium, DisplacedJet, DoubleEG, DoubleMuon, DoubleMuonLowMass, HTMHT, MET,
MuOnia, MuonEG, SingleElectron, SinglePhoton, Tau, ZeroBias).

## What does not exist (searched, 2026-11-21)

* **No simulated PFNano samples** on the portal (queries `PFNano`, `nanoaod-pf`,
  `TTToSemiLeptonic PFNano`, ... return only the 17 collision records + tool).
  The only CMS full-simulation sample with per-jet PF candidates for AK8 jets is
  record 12102 (2016 RunIISummer16 / Moriond17, 80X reco, CHS jets), and record
  12100 (AK4 jets, JetNTuple). Consequence: the data (UL2016 reco, PUPPI-era
  NanoAOD with all PF candidates) and simulation (legacy 80X reco, CHS jet
  constituents) differ in reconstruction release as well as in physics; see
  docs/FEATURES.md for how this is mitigated and what remains.
* No ttbar simulation with PF candidates: the ttbar control region is therefore
  compared *data vs data* (top-like vs W-like vs dijet) and vs JetClass TTBar,
  not vs CMS simulation.

## Licence and acknowledgement

All CMS Open Data used here are released under **CC0-1.0** (field `license.attribution`
of each record). CMS asks that users acknowledge the data source; suggested text:

> This research has used data from the CMS Open Data portal
> (https://opendata.cern.ch): records 31308, 31313, 12102 and 14220. CMS Collaboration
> (2024). JetHT / SingleMuon primary datasets in NanoAOD format enhanced with
> Particle Flow candidates from RunG of 2016. CERN Open Data Portal.
> Duarte, J. (2019). Sample with jet, track and secondary vertex properties for
> Hbb tagging ML studies. CERN Open Data Portal. DOI:10.7483/OPENDATA.CMS.JGJX.MS7Q.

The analysis presented here is not endorsed by, and does not represent the
views of, the CMS Collaboration.
