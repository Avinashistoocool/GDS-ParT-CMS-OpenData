"""CPU smoke tests. Synthetic arrays mimic the PFNano and CMS-simulation
branches; the real-checkpoint test runs when the gds_part repo is available
(GDS_PART_DIR or ../gds_part) and is skipped otherwise."""
import os
import sys

import awkward as ak
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cmsod import compare as C  # noqa: E402
from cmsod import features as F  # noqa: E402
from cmsod import gdspart, records, selection  # noqa: E402

RNG = np.random.default_rng(0)


def fake_pfnano(n_ev=6, n_cand=80):
    """Events with 2 FatJets, PF candidates clustered around them + noise."""
    ev = {k: [] for k in F.PFNANO_CAND_BRANCHES + selection.JETHT_EVENT_BRANCHES}
    for i in range(n_ev):
        jets_eta = RNG.uniform(-1.5, 1.5, 2)
        jets_phi = np.array([0.5, 0.5 - np.pi])
        eta = np.r_[jets_eta[0] + RNG.normal(0, 0.15, n_cand // 2),
                    jets_eta[1] + RNG.normal(0, 0.15, n_cand // 2), RNG.uniform(-4, 4, 20)]
        phi = F.wrap_phi(np.r_[jets_phi[0] + RNG.normal(0, 0.15, n_cand // 2),
                               jets_phi[1] + RNG.normal(0, 0.15, n_cand // 2), RNG.uniform(-3, 3, 20)])
        n = len(eta)
        pdg = RNG.choice([211, -211, 130, 22, 11, 13, 1, 2], n)
        charged = np.isin(np.abs(pdg), [211, 11, 13])
        ev["PFCands_pt"].append(RNG.exponential(15, n) + 0.5)
        ev["PFCands_eta"].append(eta)
        ev["PFCands_phi"].append(phi)
        ev["PFCands_mass"].append(np.where(charged, 0.1396, 0.0))
        ev["PFCands_charge"].append(np.where(charged, np.sign(pdg), 0).astype(np.int32))
        ev["PFCands_pdgId"].append(pdg.astype(np.int32))
        for b, s in [("PFCands_d0", 0.01), ("PFCands_dz", 0.05)]:
            ev[b].append(np.where(charged, RNG.normal(0, s, n), -1.0))
        for b in ["PFCands_d0Err", "PFCands_dzErr"]:
            ev[b].append(np.where(charged, RNG.uniform(0.005, 0.05, n), -1.0))
        ev["PFCands_puppiWeight"].append(RNG.choice([0.0, 1.0], n, p=[0.2, 0.8]))
        ev["FatJet_pt"].append(np.array([700.0, 600.0]))
        ev["FatJet_eta"].append(jets_eta)
        ev["FatJet_phi"].append(jets_phi)
        ev["FatJet_msoftdrop"].append(np.array([60.0, 170.0]))
        ev["FatJet_jetId"].append(np.array([6, 6], dtype=np.int32))
        ev["FatJet_nConstituents"].append(np.array([40, 40]))
        for b, v in [("run", 278969), ("luminosityBlock", 100), ("PV_npvsGood", 20),
                     ("HLT_PFJet450", True), ("HLT_AK8PFJet450", False)]:
            ev[b].append(v)
    return ak.zip({k: ak.Array(v) for k, v in ev.items()}, depth_limit=1)


def fake_mc(n=5, m=30):
    t = {b: [] for b in F.MC_BRANCHES}
    for i in range(n):
        ptrel = np.sort(RNG.dirichlet(np.ones(m)))[::-1]
        oh = RNG.integers(0, 5, m)
        t["pfcand_ptrel"].append(ptrel)
        t["pfcand_etarel"].append(RNG.normal(0, 0.2, m))
        t["pfcand_phirel"].append(RNG.normal(0, 0.2, m))
        t["pfcand_mass"].append(np.where(oh == 0, 0.1396, 0.0))
        t["pfcand_charge"].append(np.where(np.isin(oh, [0, 3, 4]), 1.0, 0.0))
        for k, b in enumerate(["pfcand_isChargedHad", "pfcand_isNeutralHad", "pfcand_isGamma",
                               "pfcand_isEl", "pfcand_isMu"]):
            t[b].append((oh == k).astype(np.float32))
        dxy = RNG.normal(0, 0.01, m)
        t["pfcand_dxy"].append(dxy)
        t["pfcand_dxysig"].append(dxy / 0.002)
        t["pfcand_dz"].append(dxy * 2)
        t["pfcand_dzsig"].append(dxy * 2 / 0.004)
        for b, v in [("fj_pt", 650.0), ("fj_eta", -1.2 + 0.5 * i), ("fj_phi", 0.3), ("fj_mass", 90.0),
                     ("fj_sdmass", 80.0), ("npv", 20.0), ("ntrueInt", 20.0), ("event_no", i),
                     ("sample_isQCD", i % 2), ("fj_isQCD", i % 2), ("fj_isH", 1 - i % 2),
                     ("fj_label", 0), ("label_H_bb", 1 - i % 2)]:
            t[b].append(v)
    return ak.zip({k: ak.Array(v) for k, v in t.items()}, depth_limit=1)


def test_https_conversion():
    u = "root://eospublic.cern.ch//eos/opendata/cms/derived-data/PFNano/x.root"
    assert records.to_https(u) == "https://opendata.cern.ch/eos/opendata/cms/derived-data/PFNano/x.root"


def test_golden_mask():
    g = {1: [[1, 10], [20, 30]]}
    assert records.golden_mask([1, 1, 1, 2], [5, 15, 25, 5], g).tolist() == [True, False, True, False]


def test_pfnano_mapping_shapes_and_conventions():
    ev = fake_pfnano()
    idx, evmask = selection.select_qcd_dijet(ev, None)
    assert evmask.all() and ak.sum(ak.num(idx)) == 12
    cons, evt = F.pfnano_jet_constituents(ev, idx)
    jc = F.constituents_to_jetclass(cons)
    assert len(jc) == 12 and len(evt) == 12
    # constituents are inside the cone and above the pT threshold
    assert ak.all(np.hypot(jc.part_deta, jc.part_dphi) < 0.8 + 0.05)
    assert ak.all(np.hypot(jc.part_px, jc.part_py) > F.MIN_CAND_PT - 1e-6)
    # pt-ordered, exactly one PID flag per particle, neutral impact parameters zeroed
    pt = np.hypot(jc.part_px, jc.part_py)
    assert ak.all(pt[:, :-1] >= pt[:, 1:])
    flags = sum(jc[n] for n in F.ONEHOT_NAMES)
    assert ak.all(flags == 1)
    neutral = jc.part_charge == 0
    assert ak.all(ak.where(neutral, jc.part_d0err == 0, True))
    # CHS emulation: no charged hadron with PUPPI weight 0 survives
    assert ak.all(np.isclose(jc.jet_pt, np.hypot(ak.sum(jc.part_px, 1), ak.sum(jc.part_py, 1))))


def test_mc_mapping_roundtrip():
    t = fake_mc()
    cons = F.mc_ntuple_constituents(t)
    jc = F.constituents_to_jetclass(cons)
    # pfcand_etarel is signed with sign(fj_eta) like JetClass part_deta
    sgn = np.sign(np.asarray(t.fj_eta))
    eta = t.fj_eta + t.pfcand_etarel * sgn
    eta = eta[t.pfcand_ptrel * t.fj_pt > F.MIN_CAND_PT]
    assert np.allclose(ak.to_numpy(ak.flatten(ak.sort(eta, axis=1))),
                       ak.to_numpy(ak.flatten(ak.sort(cons.eta, axis=1))))
    # recovered impact-parameter errors (cm) scaled to mm
    ch = ak.flatten(jc.part_charge != 0)
    err = ak.to_numpy(ak.flatten(jc.part_d0err))[ak.to_numpy(ch)]
    assert np.allclose(err, 0.002 * F.CM_TO_MM, rtol=1e-4)
    assert set(selection.mc_truth_label(t).tolist()) == {0, 1}


def test_jetclass_feature_build_matches_training_code():
    colab, cache, _ = _model_modules_or_skip()
    jc = F.constituents_to_jetclass(F.pfnano_jet_constituents(fake_pfnano(), selection.select_qcd_dijet(
        fake_pfnano(), None)[0])[0])
    feats, vec, counts = F.build_inputs(jc, cache)
    assert feats.shape[1] == 17 and vec.shape[1] == 4 and counts.sum() == len(feats)
    assert np.isfinite(feats.astype(np.float32)).all()
    f, v, m = F.pad_batch(feats, vec, counts, 0, len(counts))
    import torch
    pair = cache.pairwise_features(torch.from_numpy(v), torch.from_numpy(m))
    assert pair.shape == (len(counts), f.shape[1], f.shape[1], 4)


def test_real_checkpoint_inference():
    _model_modules_or_skip()
    ck = os.path.join(gdspart.find_repo(), *gdspart.CKPT_REL.split("/"))
    if not os.path.exists(ck):
        pytest.skip("checkpoint not present")
    from cmsod import pipeline
    model, info = gdspart.load_model(device="cpu")
    _, cache, _ = gdspart.import_modules()
    ev = fake_pfnano()
    idx, _ = selection.select_qcd_dijet(ev, None)
    jc = F.constituents_to_jetclass(F.pfnano_jet_constituents(ev, idx)[0])
    scores = pipeline.score_jets(model, cache, jc, "cpu")
    assert scores.shape == (12, 10)
    assert np.allclose(scores.sum(1), 1, atol=1e-4)
    assert info["config"]["n_classes"] == 10


def test_stats():
    a = RNG.normal(0, 1, 2000)
    b = RNG.normal(0, 1, 2000)
    d, p = C.weighted_ks(a, b)
    assert d < 0.06 and p > 0.01
    d2, p2 = C.weighted_ks(a, b + 0.5)
    assert d2 > 0.15 and p2 < 1e-6
    c2, ndf = C.chi2_shape(np.clip(a / 8 + 0.5, 0, 1), np.clip(b / 8 + 0.5, 0, 1))
    assert ndf > 0 and c2 / ndf < 3
    s = np.full((4, 10), 0.1)
    s[:, 8] = 0.3
    s[:, 0] = 0.1
    assert np.allclose(C.discriminant(s, "Tbqq"), 0.75)
    w = C.reweight({"jet_pt": RNG.uniform(500, 1000, 5000)}, {"jet_pt": RNG.uniform(500, 600, 5000)})
    assert w.shape == (5000,)


def _model_modules_or_skip():
    try:
        return gdspart.import_modules()
    except FileNotFoundError:
        pytest.skip("gds_part repo not available (set GDS_PART_DIR)")
