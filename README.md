# GDS-ParT on CMS Open Data

Run the JetClass-trained **GDS-ParT** jet tagger
([Gated-Dual-Stream-Particle-Transformer](https://github.com/Avinashistoocool/Gated-Dual-Stream-Particle-Transformer))
on real CMS collision data from the CERN Open Data portal and measure where its
outputs disagree with simulation.

> Work in progress: see [docs/PLAN.md](docs/PLAN.md) for status.

## Layout

| path | content |
|---|---|
| `src/cmsod/records.py` | verified CERN Open Data records + file listing, 2016 golden JSON |
| `src/cmsod/features.py` | CMS PF candidates -> JetClass 17 particle features (+ 4 pairwise via the original code) |
| `src/cmsod/selection.py` | QCD dijet (JetHT) and ttbar mu+jets (SingleMuon) control regions |
| `src/cmsod/pipeline.py`, `run.py` | streaming inference with uproot over HTTPS |
| `src/cmsod/compare.py`, `analyze.py` | data/MC histograms, ratio panels, KS / chi2, slices |
| `kaggle/gds-part-cms-opendata/` | Kaggle kernel running the full chain on GPU |
| `scripts/push_kaggle.ps1` | pushes kernels (username from `KAGGLE_USERNAME` / `kaggle config view`) |
| `tests/` | CPU smoke tests |
