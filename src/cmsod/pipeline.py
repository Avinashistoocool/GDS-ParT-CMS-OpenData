"""Streaming pipeline: ROOT files -> selected jets -> GDS-ParT scores.

Output per source is an .npz with one row per jet:
    scores (J,10) softmax outputs in JetClass class order, plus jet observables
    (pt, eta, mass, msd, n_constituents, npv, category/label, event id).
"""
import time

import numpy as np

from . import features as F
from . import selection as S

CLASS_LIST = ["QCD", "Hbb", "Hcc", "Hgg", "H4q", "Hqql", "Zqq", "Wqq", "Tbqq", "Tbl"]


def open_tree(url, treename, timeout=180):
    import uproot
    opts = {"timeout": timeout}
    if url.startswith("http"):
        try:
            import aiohttp  # noqa: F401  (fsspec HTTP backend; robust against multipart issues)
        except ImportError:
            opts["handler"] = uproot.source.http.HTTPSource
    return uproot.open(url, **opts)[treename]


class RetryTree:
    """Wraps an uproot TTree read over HTTP: a dropped connection (e.g. aiohttp
    ClientPayloadError, which can surface as a TypeError inside fsspec) reopens
    the file and retries the same entry range instead of losing the whole file."""

    def __init__(self, url, treename, tries=4, wait=20):
        self.url, self.treename, self.tries, self.wait = url, treename, tries, wait
        self.tree = open_tree(url, treename)
        self.num_entries = self.tree.num_entries

    def arrays(self, *args, **kw):
        for i in range(self.tries):
            try:
                return self.tree.arrays(*args, **kw)
            except Exception as e:
                if i == self.tries - 1:
                    raise
                print(f"  read error ({type(e).__name__}: {e}); retry {i + 1}/{self.tries - 1}", flush=True)
                time.sleep(self.wait * (i + 1))
                try:
                    self.tree = open_tree(self.url, self.treename)
                except Exception as e2:
                    print(f"  reopen failed: {type(e2).__name__}: {e2}", flush=True)


PART_SAMPLE_PER_CHUNK = 5000


def past_deadline():
    """CMSOD_DEADLINE (unix time) lets a batch job stop reading cleanly and keep what it has."""
    import os
    d = os.environ.get("CMSOD_DEADLINE")
    return bool(d) and time.time() > float(d)


def score_jets(model, cache_mod, jc, device="cpu", batch_size=256, max_particles=128,
               return_feats=False):
    """jc: JetClass-named awkward record array -> softmax scores (J, 10).
    With return_feats also returns a sample of the normalized particle features
    actually fed to the network (for input-level data/MC comparisons)."""
    import torch
    feats, vectors, counts = F.build_inputs(jc, cache_mod, max_particles)
    out = []
    use_amp = device == "cuda"
    with torch.no_grad():
        for s in range(0, len(counts), batch_size):
            f, v, m = F.pad_batch(feats, vectors, counts, s, min(s + batch_size, len(counts)))
            f, v, m = (torch.from_numpy(x).to(device) for x in (f, v, m))
            with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                logits = model(f, cache_mod.pairwise_features(v, m), mask=m)
            out.append(torch.softmax(logits.float(), dim=-1).cpu().numpy())
    scores = np.concatenate(out) if out else np.zeros((0, 10), np.float32)
    if return_feats:
        return scores, np.asarray(feats[:PART_SAMPLE_PER_CHUNK], dtype=np.float16)
    return scores


def _jet_table(jc, extra):
    import awkward as ak
    tab = {"jet_pt": ak.to_numpy(jc.jet_pt), "jet_eta": ak.to_numpy(jc.jet_eta),
           "jet_mass": ak.to_numpy(jc.jet_mass),
           "n_constituents": ak.to_numpy(jc.jet_nparticles)}
    tab.update({k: np.asarray(v) for k, v in extra.items()})
    return tab


def _kin_mask(jc, pt_min, pt_max, eta_max):
    import awkward as ak
    pt, eta = ak.to_numpy(jc.jet_pt), ak.to_numpy(jc.jet_eta)
    return (pt > pt_min) & (pt < pt_max) & (np.abs(eta) < eta_max)


def process_pfnano(url, region, model, cache_mod, golden=None, device="cpu", max_events=None,
                   step=2000, pt_range=(S.PT_MIN, S.PT_MAX), eta_max=S.ABS_ETA_MAX,
                   chs_like=True, log=print):
    import awkward as ak
    tree = RetryTree(url, "Events")
    if region == "qcd_dijet":
        branches, select = S.JETHT_EVENT_BRANCHES, S.select_qcd_dijet
    elif region == "ttbar_mujets":
        branches, select = S.SINGLEMU_EVENT_BRANCHES, S.select_ttbar_mujets
    else:
        raise ValueError(region)
    stop = min(tree.num_entries, max_events) if max_events else tree.num_entries
    tables, n_ev, t0 = [], 0, time.time()
    # two passes per chunk: light event-level branches first, and the heavy PF-candidate
    # branches only for the entry range that contains selected events (most chunks of
    # SingleMuon have none)
    for start in range(0, stop, step):
        if past_deadline():
            log("  deadline reached, stopping")
            break
        end = min(start + step, stop)
        evl = tree.arrays(branches, entry_start=start, entry_stop=end, library="ak")
        # loose preselection on the stored jet pT; final cut on the constituent jet
        idx, evmask = select(evl, golden, pt_min=0.8 * pt_range[0], pt_max=1.2 * pt_range[1],
                             eta_max=eta_max + 0.2)
        n_ev += end - start
        sel = np.nonzero(ak.to_numpy(ak.num(idx)) > 0)[0]
        if len(sel) == 0:
            continue
        lo, hi = int(sel[0]), int(sel[-1]) + 1
        cands = tree.arrays(F.PFNANO_CAND_BRANCHES, entry_start=start + lo, entry_stop=start + hi,
                            library="ak")
        ev = evl[lo:hi]
        for b in F.PFNANO_CAND_BRANCHES:
            ev = ak.with_field(ev, cands[b], b)
        idx = idx[lo:hi]
        cons, evt = F.pfnano_jet_constituents(ev, idx, chs_like=chs_like)
        jc = F.constituents_to_jetclass(cons)
        msd = ak.to_numpy(ak.flatten(ev.FatJet_msoftdrop[idx]))
        extra = {"msd": msd, "npv": ak.to_numpy(ev.PV_npvsGood)[evt],
                 "run": ak.to_numpy(ev.run)[evt], "jet_pt_nano": ak.to_numpy(ak.flatten(ev.FatJet_pt[idx])),
                 "category": S.ttbar_category(msd) if region == "ttbar_mujets" else np.zeros(len(msd), int)}
        keep = _kin_mask(jc, *pt_range, eta_max) & (ak.to_numpy(jc.jet_nparticles) >= 2)
        if not keep.any():
            continue
        jc = jc[keep]
        tab = _jet_table(jc, {k: v[keep] for k, v in extra.items()})
        tab["scores"], tab["part_feats"] = score_jets(model, cache_mod, jc, device, return_feats=True)
        tables.append(tab)
        log(f"  {n_ev}/{stop} events, {sum(len(t['jet_pt']) for t in tables)} jets "
            f"({time.time() - t0:.0f}s)")
    return _concat(tables), n_ev


def process_mc(url, model, cache_mod, device="cpu", max_jets=None, step=5000,
               pt_range=(S.PT_MIN, S.PT_MAX), eta_max=S.ABS_ETA_MAX, log=print):
    import awkward as ak
    tree = RetryTree(url, "deepntuplizer/tree")
    stop = min(tree.num_entries, max_jets) if max_jets else tree.num_entries
    tables, t0 = [], time.time()
    for start in range(0, stop, step):
        if past_deadline():
            log("  deadline reached, stopping")
            break
        t = tree.arrays(F.MC_BRANCHES, entry_start=start, entry_stop=min(start + step, stop), library="ak")
        pre = S.select_mc(t, 0.8 * pt_range[0], 1.2 * pt_range[1], eta_max + 0.2)
        t = t[pre]
        jc = F.constituents_to_jetclass(F.mc_ntuple_constituents(t))
        keep = _kin_mask(jc, *pt_range, eta_max) & (ak.to_numpy(jc.jet_nparticles) >= 2)
        t, jc = t[keep], jc[keep]
        if len(jc) == 0:
            continue
        tab = _jet_table(jc, {"msd": ak.to_numpy(t.fj_sdmass), "npv": ak.to_numpy(t.npv),
                              "label": S.mc_truth_label(t), "jet_pt_nano": ak.to_numpy(t.fj_pt),
                              "category": np.zeros(len(t), int)})
        tab["scores"], tab["part_feats"] = score_jets(model, cache_mod, jc, device, return_feats=True)
        tables.append(tab)
        log(f"  {sum(len(x['jet_pt']) for x in tables)} jets ({time.time() - t0:.0f}s)")
    return _concat(tables)


def process_jetclass(path, model, cache_mod, device="cpu", max_jets=None, step=5000,
                     pt_range=(S.PT_MIN, S.PT_MAX), eta_max=S.ABS_ETA_MAX, log=print):
    """Delphes reference: the training-domain inputs, built by the same code path."""
    import awkward as ak
    tree = open_tree(path, "tree")
    stop = min(tree.num_entries, max_jets) if max_jets else tree.num_entries
    br = cache_mod.BRANCHES + ["jet_eta", "jet_sdmass", "jet_nparticles"]
    tables = []
    for a in tree.iterate(br, entry_stop=stop, step_size=step, library="ak"):
        pt, eta = ak.to_numpy(a.jet_pt), ak.to_numpy(a.jet_eta)
        keep = (pt > pt_range[0]) & (pt < pt_range[1]) & (np.abs(eta) < eta_max)
        a = a[keep]
        p2 = ak.sum(a.part_px, axis=1) ** 2 + ak.sum(a.part_py, axis=1) ** 2 + ak.sum(a.part_pz, axis=1) ** 2
        mass = np.sqrt(np.maximum(ak.to_numpy(a.jet_energy) ** 2 - ak.to_numpy(p2), 0))
        tab = {"jet_pt": ak.to_numpy(a.jet_pt), "jet_eta": ak.to_numpy(a.jet_eta), "jet_mass": mass,
               "n_constituents": ak.to_numpy(a.jet_nparticles), "msd": ak.to_numpy(a.jet_sdmass),
               "npv": np.zeros(len(a)), "category": np.zeros(len(a), int)}
        tab["scores"], tab["part_feats"] = score_jets(model, cache_mod, a, device, return_feats=True)
        tables.append(tab)
    log(f"  {sum(len(x['jet_pt']) for x in tables)} jets from {path}")
    return _concat(tables)


def _concat(tables):
    if not tables:
        return {}
    return {k: np.concatenate([t[k] for t in tables]) for k in tables[0]}
