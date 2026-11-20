"""Map CMS particle-flow candidates onto the JetClass input format of GDS-ParT.

Strategy: every source (CMS collision data in PFNano format, CMS full-simulation
ntuples, JetClass itself) is first converted into a common per-jet record of
constituents in *JetClass branch names* (part_px, part_deta, part_isPhoton, ...).
The 17 normalized particle features are then produced by the *unchanged*
`_process_chunk` of gds_part/data/jetclass_cache.py, and the 4 pairwise features
by its `pairwise_features`, i.e. the very code used to train the model.

Feature mapping (JetClass/Delphes <- CMS PF candidate), see docs/FEATURES.md:
    part_px/py/pz/energy  <- pt, eta, phi, mass of the PF candidate     exact
    part_deta             <- (eta - jet_eta) * sign(jet_eta)             exact (JetClass convention, verified)
    part_dphi             <- phi - jet_phi wrapped to [-pi, pi]          exact
    part_charge           <- charge                                     exact
    part_is*              <- |pdgId| 211/130/22/11/13 (1->NH, 2->photon) exact (HF cands 1/2 approximated)
    part_d0val, part_dzval<- d0 / dz [cm] x 10  (Delphes uses mm)        approximated: definition and
    part_d0err, part_dzerr<- d0Err / dzErr [cm] x 10                       resolution differ from Delphes
    neutral / no-track    <- 0 for all four (CMS default is -1)          as in JetClass
    jet_pt, jet_energy    <- |sum p_T|, sum E of the selected constituents (as in JetClass)
"""
import numpy as np

JET_R = 0.8
MIN_CAND_PT = 0.95          # GeV; the CMS MC ntuple (rec. 12102) only stores PF candidates above this
CM_TO_MM = 10.0

# |pdgId| -> (isChargedHadron, isNeutralHadron, isPhoton, isElectron, isMuon)
PDG_ONEHOT = {211: 0, 130: 1, 22: 2, 11: 3, 13: 4, 1: 1, 2: 2}
ONEHOT_NAMES = ["part_isChargedHadron", "part_isNeutralHadron", "part_isPhoton",
                "part_isElectron", "part_isMuon"]
FEATURE_NAMES = ["pt_log", "e_log", "logptrel", "logerel", "deltaR", "deta", "dphi", "charge",
                 "isChargedHadron", "isNeutralHadron", "isPhoton", "isElectron", "isMuon",
                 "tanh_d0", "d0err", "tanh_dz", "dzerr"]


def wrap_phi(x):
    return (x + np.pi) % (2 * np.pi) - np.pi


def _sort_desc(rec, key="pt"):
    import awkward as ak
    order = ak.argsort(rec[key], axis=-1, ascending=False)
    return rec[order]


def constituents_to_jetclass(c, d0_scale=CM_TO_MM):
    """c: awkward array (n_jets, var) of records with fields
        pt, eta, phi, mass, charge, onehot (int 0-4 or -1), d0, d0err, dz, dzerr
       (CMS units: GeV, cm; track fields < 0 or NaN where undefined).
    Returns an awkward record array of JetClass-named branches, pt-sorted,
    ready for jetclass_cache._process_chunk."""
    import awkward as ak
    c = _sort_desc(c)
    pt, eta, phi, m = c.pt, c.eta, c.phi, c.mass
    px, py, pz = pt * np.cos(phi), pt * np.sin(phi), pt * np.sinh(eta)
    e = np.sqrt(px ** 2 + py ** 2 + pz ** 2 + np.maximum(m, 0) ** 2)
    jpx, jpy, jpz, je = (ak.sum(v, axis=1) for v in (px, py, pz, e))
    jpt = np.hypot(jpx, jpy)
    jeta = np.arcsinh(jpz / np.maximum(jpt, 1e-9))
    jphi = np.arctan2(jpy, jpx)

    has_trk = (c.charge != 0) & (c.d0err > 0)
    z = lambda v: ak.where(has_trk, v * d0_scale, 0.0)
    out = {
        "part_px": px, "part_py": py, "part_pz": pz, "part_energy": e,
        "part_deta": (eta - jeta) * np.sign(jeta),
        "part_dphi": wrap_phi(phi - jphi),
        "part_charge": ak.values_astype(c.charge, np.float32),
        "part_d0val": z(c.d0), "part_d0err": z(c.d0err),
        "part_dzval": z(c.dz), "part_dzerr": z(c.dzerr),
        "jet_pt": jpt, "jet_eta": jeta, "jet_phi": jphi, "jet_energy": je,
        "jet_mass": np.sqrt(np.maximum(je ** 2 - jpx ** 2 - jpy ** 2 - jpz ** 2, 0)),
        "jet_nparticles": ak.num(pt, axis=1),
    }
    for k, name in enumerate(ONEHOT_NAMES):
        out[name] = ak.values_astype(c.onehot == k, np.float32)
    return ak.zip(out, depth_limit=1)


# ----------------------------------------------------------------------------
# CMS collision data: NanoAOD + PFCands (records 31300-31316)
# ----------------------------------------------------------------------------
PFNANO_CAND_BRANCHES = ["PFCands_pt", "PFCands_eta", "PFCands_phi", "PFCands_mass", "PFCands_charge",
                        "PFCands_pdgId", "PFCands_d0", "PFCands_d0Err", "PFCands_dz", "PFCands_dzErr",
                        "PFCands_puppiWeight"]


def pfnano_onehot(pdg):
    import awkward as ak
    a = abs(pdg)
    out = ak.full_like(a, -1)
    for p, k in PDG_ONEHOT.items():
        out = ak.where(a == p, k, out)
    return out


def pfnano_jet_constituents(ev, jet_idx, chs_like=True):
    """Associate PF candidates to selected AK8 jets by a fixed cone.

    PFNano stores *all* PF candidates of the event but no jet->candidate links,
    so constituents are PF candidates with pT > 0.95 GeV within dR < 0.8 of the
    FatJet (AK8 PUPPI) axis. With chs_like=True charged hadrons with PUPPI
    weight 0 (not associated to the primary vertex) are dropped, emulating the
    charged-hadron subtraction of the CHS jets in the simulation ntuple.

    ev: awkward events with FatJet_eta/phi and PFNANO_CAND_BRANCHES
    jet_idx: awkward (n_events, var) indices of the selected FatJets
    Returns (constituents (n_jets, var), event index per jet)."""
    import awkward as ak
    jeta = ev.FatJet_eta[jet_idx]
    jphi = ev.FatJet_phi[jet_idx]
    evt = ak.broadcast_arrays(ak.local_index(ev.FatJet_eta, axis=0), jet_idx)[0]
    cand = ak.zip({
        "pt": ev.PFCands_pt, "eta": ev.PFCands_eta, "phi": ev.PFCands_phi,
        "mass": ev.PFCands_mass, "charge": ev.PFCands_charge,
        "onehot": pfnano_onehot(ev.PFCands_pdgId),
        "d0": ev.PFCands_d0, "d0err": ev.PFCands_d0Err,
        "dz": ev.PFCands_dz, "dzerr": ev.PFCands_dzErr,
        "puppi": ev.PFCands_puppiWeight,
    })
    keep = cand.pt > MIN_CAND_PT
    if chs_like:
        is_lep = (cand.onehot == 3) | (cand.onehot == 4)
        keep = keep & ((cand.charge == 0) | is_lep | (cand.puppi > 0))
    cand = cand[keep]
    # (event, jet, cand) cone matching
    pairs_j, pairs_c = ak.unzip(ak.cartesian([ak.zip({"eta": jeta, "phi": jphi}), cand],
                                             axis=1, nested=True))
    dr2 = (pairs_c.eta - pairs_j.eta) ** 2 + wrap_phi(pairs_c.phi - pairs_j.phi) ** 2
    cons = pairs_c[dr2 < JET_R ** 2]
    cons = ak.flatten(cons, axis=1)                       # (n_jets, var)
    evt = ak.to_numpy(ak.flatten(evt, axis=1))
    return cons, evt


# ----------------------------------------------------------------------------
# CMS full simulation: HiggsToBBNTuple (record 12102), AK8 CHS jets
# ----------------------------------------------------------------------------
MC_BRANCHES = ["fj_pt", "fj_eta", "fj_phi", "fj_mass", "fj_sdmass", "npv", "ntrueInt", "event_no",
               "sample_isQCD", "fj_isQCD", "fj_isH", "fj_label", "label_H_bb",
               "pfcand_ptrel", "pfcand_etarel", "pfcand_phirel", "pfcand_mass", "pfcand_charge",
               "pfcand_isChargedHad", "pfcand_isNeutralHad", "pfcand_isGamma", "pfcand_isEl", "pfcand_isMu",
               "pfcand_dxy", "pfcand_dxysig", "pfcand_dz", "pfcand_dzsig"]


def mc_ntuple_constituents(t):
    """t: awkward array of MC_BRANCHES (one entry per AK8 jet).
    In this ntuple pfcand_ptrel = pt/fj_pt and pfcand_etarel is signed like
    JetClass: (eta - fj_eta) * sign(fj_eta) (verified by reconstructing the jet
    and the stored pfcand_erel to 1e-7). Impact parameter errors are not stored
    and are recovered as |dxy / dxysig|, |dz / dzsig|."""
    import awkward as ak
    sgn = np.where(np.asarray(t.fj_eta) >= 0, 1.0, -1.0)
    pt = t.pfcand_ptrel * t.fj_pt
    eta = t.fj_eta + t.pfcand_etarel * sgn
    phi = wrap_phi(t.fj_phi + t.pfcand_phirel)
    onehot = ak.full_like(t.pfcand_charge, -1, dtype=np.int64)
    for k, b in enumerate(["pfcand_isChargedHad", "pfcand_isNeutralHad", "pfcand_isGamma",
                           "pfcand_isEl", "pfcand_isMu"]):
        onehot = ak.where(t[b] > 0.5, k, onehot)

    def err(v, sig):
        good = (sig != 0) & (abs(sig) < 1999)       # dxysig is clipped at +-2000 when undefined
        return ak.where(good, abs(v / ak.where(sig == 0, 1, sig)), -1.0)

    cons = ak.zip({
        "pt": pt, "eta": eta, "phi": phi, "mass": ak.where(t.pfcand_mass > 0, t.pfcand_mass, 0.0),
        "charge": ak.values_astype(t.pfcand_charge, np.int64), "onehot": onehot,
        "d0": t.pfcand_dxy, "d0err": err(t.pfcand_dxy, t.pfcand_dxysig),
        "dz": t.pfcand_dz, "dzerr": err(t.pfcand_dz, t.pfcand_dzsig),
    })
    return cons[cons.pt > MIN_CAND_PT]


def build_inputs(jc, cache_mod, max_particles=128):
    """JetClass-named record array -> (feats float16 (P,17), vectors (P,4), counts (J,))
    using the training preprocessing of gds_part."""
    return cache_mod._process_chunk(jc, max_particles)


def pad_batch(feats, vectors, counts, start, stop):
    """Pad jets [start, stop) of ragged arrays to the longest jet in the slice."""
    off = np.zeros(len(counts) + 1, dtype=np.int64)
    np.cumsum(counts, out=off[1:])
    cnt = counts[start:stop]
    n = max(int(cnt.max()) if len(cnt) else 2, 2)
    mask = np.arange(n)[None, :] < cnt[:, None]
    rows = (off[start:stop, None] + np.arange(n)[None, :])[mask]
    f = np.zeros((len(cnt), n, 17), dtype=np.float32)
    v = np.zeros((len(cnt), n, 4), dtype=np.float32)
    f[mask] = feats[rows]
    v[mask] = vectors[rows]
    return f, v, mask
