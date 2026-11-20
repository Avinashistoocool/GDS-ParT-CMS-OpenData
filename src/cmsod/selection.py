"""Event / jet selections for the three kinds of input.

Common phase space (all sources): AK8 jets with 500 < pT < 1000 GeV and
|eta| < 2.0 -- the JetClass training range -- unless overridden.

Control regions in collision data (no truth labels; jet content known from the
selection):
  * qcd_dijet (JetHT): HLT_PFJet450 || HLT_AK8PFJet450, two leading AK8 jets
    with tight jet ID. Dominantly light-quark/gluon jets -> tagger should say QCD.
  * ttbar_mujets (SingleMuon): one tight isolated muon (pT>55), MET>50, a b-tagged
    AK4 jet near the muon (leptonic top side), and the leading AK8 jet in the
    opposite hemisphere (hadronic top side). Split by soft-drop mass into
    top-like (105-210 GeV) and W-like (65-105 GeV) categories.
"""
import numpy as np

PT_MIN, PT_MAX, ABS_ETA_MAX = 500.0, 1000.0, 2.0
BTAG_DEEPJET_MEDIUM_2016POST = 0.2489   # UL2016 postVFP (Run2016G) DeepJet medium WP

JETHT_EVENT_BRANCHES = ["run", "luminosityBlock", "PV_npvsGood", "HLT_PFJet450", "HLT_AK8PFJet450",
                        "FatJet_pt", "FatJet_eta", "FatJet_phi", "FatJet_msoftdrop", "FatJet_jetId",
                        "FatJet_nConstituents"]
SINGLEMU_EVENT_BRANCHES = ["run", "luminosityBlock", "PV_npvsGood",
                           "HLT_IsoMu24", "HLT_IsoTkMu24", "HLT_Mu50", "HLT_TkMu50",
                           "Muon_pt", "Muon_eta", "Muon_phi", "Muon_tightId", "Muon_pfRelIso04_all",
                           "MET_pt", "Jet_pt", "Jet_eta", "Jet_phi", "Jet_jetId", "Jet_btagDeepFlavB",
                           "FatJet_pt", "FatJet_eta", "FatJet_phi", "FatJet_msoftdrop", "FatJet_jetId",
                           "FatJet_nConstituents"]


def _dphi(a, b):
    return (a - b + np.pi) % (2 * np.pi) - np.pi


def _kin(pt, eta, pt_min, pt_max, eta_max):
    return (pt > pt_min) & (pt < pt_max) & (abs(eta) < eta_max)


def select_qcd_dijet(ev, golden=None, pt_min=PT_MIN, pt_max=PT_MAX, eta_max=ABS_ETA_MAX):
    """Returns awkward (n_events, var) indices of selected FatJets + event mask."""
    import awkward as ak
    from .records import golden_mask
    evmask = ak.to_numpy(ev.HLT_PFJet450 | ev.HLT_AK8PFJet450)
    if golden is not None:
        evmask &= golden_mask(ak.to_numpy(ev.run), ak.to_numpy(ev.luminosityBlock), golden)
    idx = ak.local_index(ev.FatJet_pt, axis=1)
    jet_ok = (idx < 2) & ((ev.FatJet_jetId & 2) > 0) & \
        _kin(ev.FatJet_pt, ev.FatJet_eta, pt_min, pt_max, eta_max)
    jet_ok = jet_ok & evmask
    return idx[jet_ok], evmask


def select_ttbar_mujets(ev, golden=None, pt_min=PT_MIN, pt_max=PT_MAX, eta_max=ABS_ETA_MAX):
    import awkward as ak
    from .records import golden_mask
    trig = ev.HLT_IsoMu24 | ev.HLT_IsoTkMu24 | ev.HLT_Mu50 | ev.HLT_TkMu50
    good_mu = (ev.Muon_pt > 55) & (abs(ev.Muon_eta) < 2.4) & ev.Muon_tightId & \
        (ev.Muon_pfRelIso04_all < 0.15)
    one_mu = ak.sum(good_mu, axis=1) == 1
    evmask = ak.to_numpy(trig & one_mu & (ev.MET_pt > 50))
    if golden is not None:
        evmask &= golden_mask(ak.to_numpy(ev.run), ak.to_numpy(ev.luminosityBlock), golden)
    mu = ak.firsts(ev.Muon_phi[good_mu]), ak.firsts(ev.Muon_eta[good_mu])
    mu_phi = ak.fill_none(mu[0], 0.0)
    mu_eta = ak.fill_none(mu[1], 0.0)
    dr_b = np.hypot(ev.Jet_eta - mu_eta, _dphi(ev.Jet_phi, mu_phi))
    bjet = (ev.Jet_pt > 30) & (abs(ev.Jet_eta) < 2.4) & ((ev.Jet_jetId & 2) > 0) & \
        (ev.Jet_btagDeepFlavB > BTAG_DEEPJET_MEDIUM_2016POST) & (dr_b > 0.4) & (dr_b < 1.5)
    evmask &= ak.to_numpy(ak.any(bjet, axis=1))
    idx = ak.local_index(ev.FatJet_pt, axis=1)
    jet_ok = (idx == 0) & ((ev.FatJet_jetId & 2) > 0) & \
        _kin(ev.FatJet_pt, ev.FatJet_eta, pt_min, pt_max, eta_max) & \
        (abs(_dphi(ev.FatJet_phi, mu_phi)) > 2.0)
    jet_ok = jet_ok & evmask
    return idx[jet_ok], evmask


def ttbar_category(msd):
    """0 = other, 1 = W-like (65-105 GeV), 2 = top-like (105-210 GeV)."""
    msd = np.asarray(msd)
    return np.where((msd > 105) & (msd < 210), 2, np.where((msd > 65) & (msd <= 105), 1, 0))


def select_mc(t, pt_min=PT_MIN, pt_max=PT_MAX, eta_max=ABS_ETA_MAX):
    """Jet mask for the CMS simulation ntuple (one entry per jet)."""
    import awkward as ak
    return ak.to_numpy(_kin(t.fj_pt, t.fj_eta, pt_min, pt_max, eta_max))


def mc_truth_label(t):
    """0 = QCD jet from the QCD samples, 1 = H->bb jet from the graviton samples, -1 other."""
    import awkward as ak
    qcd = ak.to_numpy((t.sample_isQCD == 1) & (t.fj_isQCD == 1))
    hbb = ak.to_numpy((t.sample_isQCD == 0) & (t.label_H_bb == 1))
    return np.where(qcd, 0, np.where(hbb, 1, -1))
