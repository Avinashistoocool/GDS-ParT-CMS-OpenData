"""CERN Open Data records used by this project and helpers to list their files.

All record IDs below were checked against https://opendata.cern.ch/api/records/<id>
(see docs/DATASETS.md). File lists are read at run time from the record's file
index; a few verified URLs are kept as an offline fallback.
"""
import json
import urllib.request

API = "https://opendata.cern.ch/api/records/{}"

RECORDS = {
    # collision data: NanoAOD + all PF candidates ("PFCands"), Run2016G UL, 13 TeV
    "jetht": {
        "recid": 31308, "kind": "data",
        "title": "JetHT dataset in NanoAOD format enhanced with Particle Flow candidates from RunG of 2016",
        "index_match": "_root_file_index",
        "fallback": [
            "root://eospublic.cern.ch//eos/opendata/cms/derived-data/PFNano/29-Feb-24/JetHT/"
            "Run2016G-UL2016_MiniAODv2_PFNanoAODv1/240218_191008/0000/nano_data2016_1-1.root",
            "root://eospublic.cern.ch//eos/opendata/cms/derived-data/PFNano/29-Feb-24/JetHT/"
            "Run2016G-UL2016_MiniAODv2_PFNanoAODv1/240218_191008/0000/nano_data2016_1-10.root",
        ],
    },
    "singlemuon": {
        "recid": 31313, "kind": "data",
        "title": "SingleMuon dataset in NanoAOD format enhanced with Particle Flow candidates from RunG of 2016",
        "index_match": "_root_file_index",
        "fallback": [
            "root://eospublic.cern.ch//eos/opendata/cms/derived-data/PFNano/29-Feb-24/SingleMuon/"
            "Run2016G-UL2016_MiniAODv2_PFNanoAODv1/240207_205649/0000/nano_data2016_1.root",
            "root://eospublic.cern.ch//eos/opendata/cms/derived-data/PFNano/29-Feb-24/SingleMuon/"
            "Run2016G-UL2016_MiniAODv2_PFNanoAODv1/240207_205649/0000/nano_data2016_10.root",
        ],
    },
    # simulation: AK8 CHS jets with their PF candidates, RunIISummer16 (2016) QCD + H->bb
    "mc_qcd_hbb": {
        "recid": 12102, "kind": "mc",
        "title": "Sample with jet, track and secondary vertex properties for Hbb tagging ML studies "
                 "HiggsToBBNTuple_HiggsToBB_QCD_RunII_13TeV_MC",
        "index_match": "_test_root_file_index",
        "fallback": [
            "root://eospublic.cern.ch//eos/opendata/cms/datascience/HiggsToBBNtupleProducerTool/"
            f"HiggsToBBNTuple_HiggsToBB_QCD_RunII_13TeV_MC/test/ntuple_merged_{i}.root"
            for i in range(9)
        ],
    },
}

# validated ("golden") luminosity sections for 2016 collision data, record 14220
GOLDEN_JSON_RECID = 14220
GOLDEN_JSON_URL = ("https://opendata.cern.ch/eos/opendata/cms/validated-runs/2016/"
                   "Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt")


def to_https(uri):
    """root://eospublic.cern.ch//eos/opendata/... -> https://opendata.cern.ch/eos/opendata/...
    The HTTPS mirror is reachable from Kaggle and serves a publicly trusted certificate."""
    if uri.startswith("root://"):
        path = uri.split("//", 2)[2]
        return "https://opendata.cern.ch/" + path.lstrip("/")
    return uri


def _get_json(url, timeout=120):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def list_files(source, limit=None, https=True):
    """File URIs of a record (from its file index), falling back to verified URLs."""
    rec = RECORDS[source]
    uris = []
    try:
        meta = _get_json(API.format(rec["recid"]))["metadata"]
        for idx in meta.get("_file_indices", []):
            if rec["index_match"] in idx.get("description", "") and \
                    idx["description"].endswith("root_file_index.json"):
                uris += [f["uri"] for f in idx["files"]]
        uris = sorted(set(uris), key=_natural_key)
    except Exception as e:  # network or schema problem: use the verified fallback
        print(f"[records] could not read file index of {rec['recid']} ({e}); using fallback list")
    if not uris:
        uris = list(rec["fallback"])
    if limit:
        uris = uris[:limit]
    return [to_https(u) for u in uris] if https else uris


def _natural_key(s):
    import re
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def load_golden_json(url=GOLDEN_JSON_URL):
    """{run: [[ls_start, ls_end], ...]} for certified 2016 luminosity sections."""
    return {int(k): v for k, v in _get_json(url).items()}


def golden_mask(run, lumi, golden):
    import numpy as np
    run, lumi = np.asarray(run), np.asarray(lumi)
    ok = np.zeros(len(run), dtype=bool)
    for r in np.unique(run):
        sel = run == r
        for lo, hi in golden.get(int(r), []):
            ok[sel] |= (lumi[sel] >= lo) & (lumi[sel] <= hi)
    return ok
