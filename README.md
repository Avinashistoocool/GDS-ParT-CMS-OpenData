# GDS-ParT on CMS Open Data

Run the JetClass-trained **GDS-ParT** jet tagger
([Gated-Dual-Stream-Particle-Transformer](https://github.com/Avinashistoocool/Gated-Dual-Stream-Particle-Transformer),
checkpoint `v2_shared_10M_10ep/best.pt`, pinned commit `b38f1b7`) on **real CMS
collision data** from the CERN Open Data portal and measure where its outputs
disagree with simulation.

## Motivation and honest framing

GDS-ParT was trained on JetClass, a *Delphes* fast-simulation dataset. CMS Open
Data are fully reconstructed CMS events, so applying the model is a deliberate
domain-shift study, not a validated CMS tagger. The questions asked are:

1. Can the 17 particle + 4 pairwise inputs be built from real CMS PF candidates? (yes, `docs/FEATURES.md`)
2. On a selection whose jet content is known without truth (QCD dijets), do the
   tagger outputs in **data** match CMS **full simulation**?
3. Where (jet pT, eta, constituent multiplicity, pileup, input feature) do
   data, CMS simulation and Delphes (JetClass) diverge?

## Datasets

Collision data: JetHT (rec. 31308) and SingleMuon (rec. 31313), Run2016G
NanoAOD + PF candidates; simulation: AK8 jets with PF candidates, QCD + H->bb
(rec. 12102); certified lumi sections (rec. 14220). Details, URLs, what does
*not* exist on the portal, and the CC0 licence / acknowledgement text:
[docs/DATASETS.md](docs/DATASETS.md).

## Usage

```powershell
pip install uproot awkward aiohttp requests torch scipy scikit-learn matplotlib pytest
# model code + checkpoint: ../gds_part, or $env:GDS_PART_DIR, or --download-to <dir> (fetches from GitHub)
python src\cmsod\run.py --source jetht      --files 1 --max-events 3000 --out results\local
python src\cmsod\run.py --source mc_qcd_hbb --files 1 --max-jets 6000   --out results\local
python src\cmsod\run.py --source jetclass   --max-jets 3000 --jetclass-files D:\JetClass\val\ZJetsToNuNu_120.root D:\JetClass\val\HToBB_120.root --out results\local
python src\cmsod\analyze.py --in results\local --out results\local\report
python -m pytest -q tests
```

Heavy runs go to Kaggle: `kaggle/gds-part-cms-opendata/` (GPU, internet,
JetClass from the Kaggle dataset `suryatrainer/jetclass-val`), pushed with
`scripts/push_kaggle.ps1` (username from `KAGGLE_USERNAME` or `kaggle config view`).
Kernel: https://www.kaggle.com/code/avinashchandragupta/gds-part-cms-open-data

## Results so far

Full write-up with caveats: [docs/RESULTS.md](docs/RESULTS.md). Kaggle run v4
scored 31,160 JetHT data jets, 96 SingleMuon jets, 268,394 CMS-simulation jets
and 200,000 JetClass jets. Arrays and plots are in `results/kaggle_run/`.

* **Data vs CMS simulation (QCD dijets):** mean tagger outputs agree within
  0.01-0.02 (score_QCD 0.534 vs 0.522, TvsQCD 0.132 vs 0.133), but the shapes
  differ significantly (KS D 0.05-0.06, p < 1e-50). The difference is flat in
  pT and nPV and grows with constituent multiplicity (KS D 0.015 for < 30
  constituents, 0.12 for 60-80). Data jets have ~6 fewer constituents, which
  partly cancels the per-multiplicity shift.
* **CMS simulation vs JetClass (Delphes):** a 4-6x larger shift (KS D
  0.22-0.36), driven by d0err and relative-pT inputs. H->bb vs QCD AUC drops
  from 0.998 to 0.975.
* **ttbar CR (data):** top-like jets have mean TvsQCD 0.70 vs 0.13 for dijets,
  but only 33 jets and no ttbar simulation.

The model was trained on Delphes, and the simulation uses older (80X) reco than
the UL2016 data. Status and next steps: [docs/PLAN.md](docs/PLAN.md). Earlier
one-file local validation: [results/local/report/SUMMARY.md](results/local/report/SUMMARY.md).

## Layout

| path | content |
|---|---|
| `src/cmsod/records.py` | verified CERN Open Data records + file listing, 2016 golden JSON |
| `src/cmsod/features.py` | CMS PF candidates -> JetClass-format inputs (built by the original training code) |
| `src/cmsod/selection.py` | QCD dijet (JetHT) and ttbar mu+jets (SingleMuon) control regions |
| `src/cmsod/pipeline.py`, `run.py` | streaming inference with uproot over HTTPS |
| `src/cmsod/compare.py`, `analyze.py` | data/MC histograms, ratio panels, KS / chi2, slices |
| `kaggle/gds-part-cms-opendata/` | Kaggle kernel running the full chain on GPU |
| `tests/` | CPU smoke tests (synthetic PFNano / simulation arrays + real checkpoint) |

## Acknowledgement

This research has used data from the CMS Open Data portal (https://opendata.cern.ch),
released under CC0. It is not endorsed by the CMS Collaboration.
