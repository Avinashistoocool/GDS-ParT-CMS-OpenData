"""Compare tagger outputs between samples written by cmsod.run and make plots.

    python -m cmsod.analyze --in results/run --out results/run/report

Comparisons (each only if both inputs exist):
  * JetHT data (QCD dijet CR) vs CMS simulation QCD jets (rec. 12102), simulation
    reweighted to the data jet pT spectrum
  * CMS simulation QCD jets vs JetClass QCD (Delphes): pure simulation-domain shift
  * SingleMuon ttbar CR (top-like / W-like soft-drop mass) score distributions
  * CMS simulation: H->bb vs QCD ROC AUC (truth available) vs the same on JetClass
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cmsod import compare as C  # noqa: E402
from cmsod.features import FEATURE_NAMES  # noqa: E402


def load(d, stem):
    p = os.path.join(d, f"{stem}.npz")
    if not os.path.exists(p):
        return None
    z = np.load(p)
    t = {k: z[k] for k in z.files}
    return t if len(t.get("jet_pt", [])) else None


def sub(t, m):
    return {k: (v[m] if (len(v) == len(m) and k != "part_feats") else v) for k, v in t.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    data = load(args.inp, "jetht")
    smu = load(args.inp, "singlemuon")
    mc = load(args.inp, "mc_qcd_hbb")
    jc = load(args.inp, "jetclass")
    summary, md = {}, ["# GDS-ParT on CMS Open Data: data vs simulation\n"]

    mc_qcd = sub(mc, mc["label"] == 0) if mc else None
    mc_hbb = sub(mc, mc["label"] == 1) if mc else None
    jc_qcd = sub(jc, jc["label"] == 0) if jc else None

    pairs = []
    if data and mc_qcd:
        w = C.reweight(mc_qcd, data)
        pairs.append(("data_JetHT_vs_CMSsim_QCD", data, mc_qcd, w, "JetHT data", "CMS sim QCD"))
    if mc_qcd and jc_qcd:
        w = C.reweight(jc_qcd, mc_qcd)
        pairs.append(("CMSsim_QCD_vs_JetClass_QCD", mc_qcd, jc_qcd, w, "CMS sim QCD", "JetClass QCD"))

    for name, a, b, wb, la, lb in pairs:
        res = C.compare_tables(a, b, wb)
        summary[name] = res
        md.append(C.markdown_summary(res, f"{name} (A = {la}, B = {lb}, B reweighted to A in jet pT)"))
        oa, ob = C.observables(a), C.observables(b)
        for k in ["score_QCD", "TvsQCD", "WvsQCD", "ZvsQCD", "HbbvsQCD", "score_Tbqq", "score_Hbb"]:
            C.plot_compare([oa[k], ob[k]], [la, lb], [None, wb], title=name, xlabel=k,
                           path=os.path.join(args.out, f"{name}_{k}.png"))
        for k, rng in [("jet_pt", (500, 1000)), ("jet_mass", (0, 300)), ("n_constituents", (0, 150)),
                       ("msd", (0, 300))]:
            C.plot_compare([a[k], b[k]], [la, lb], [None, wb], rng=rng, title=name, xlabel=k,
                           path=os.path.join(args.out, f"{name}_{k}.png"), logy=False)
        if "part_feats" in a and "part_feats" in b:
            fa, fb = a["part_feats"].astype(np.float32), b["part_feats"].astype(np.float32)
            feat_ks = {}
            for i, fn in enumerate(FEATURE_NAMES):
                feat_ks[fn] = C.weighted_ks(fa[:, i], fb[:, i])[0]
                lo, hi = np.percentile(np.r_[fa[:, i], fb[:, i]], [0.5, 99.5])
                if hi > lo:
                    C.plot_compare([fa[:, i], fb[:, i]], [la, lb], rng=(lo, hi), title=f"{name} input",
                                   xlabel=fn, path=os.path.join(args.out, f"{name}_input_{fn}.png"))
            summary[name]["input_feature_ks"] = feat_ks
            md.append("Input-feature KS D (particle level, normalized as fed to the network): " +
                      ", ".join(f"{k}={v:.3f}" for k, v in feat_ks.items()) + "\n")

    if smu:
        cats = {1: "W-like msd 65-105", 2: "top-like msd 105-210"}
        o = C.observables(smu)
        arrs, labs = [], []
        for c, lab in cats.items():
            m = smu["category"] == c
            if m.sum():
                arrs.append(o["TvsQCD"][m])
                labs.append(f"SingleMuon {lab}")
        if data:
            arrs.append(C.observables(data)["TvsQCD"])
            labs.append("JetHT dijet")
        if len(arrs) >= 2:
            C.plot_compare(arrs, labs, title="ttbar mu+jets control region (data)", xlabel="TvsQCD",
                           path=os.path.join(args.out, "ttbar_CR_TvsQCD.png"), ref=len(arrs) - 1)
        summary["ttbar_CR"] = {lab: {"n": int(len(x)), "mean_TvsQCD": float(np.mean(x)),
                                     "frac_TvsQCD_gt_0.5": float(np.mean(x > 0.5))}
                               for x, lab in zip(arrs, labs)}
        md.append("### ttbar mu+jets control region\n\n" + "\n".join(
            f"- {k}: n={v['n']}, mean TvsQCD={v['mean_TvsQCD']:.3f}, frac(TvsQCD>0.5)={v['frac_TvsQCD_gt_0.5']:.3f}"
            for k, v in summary["ttbar_CR"].items()) + "\n")

    if mc_qcd and mc_hbb and len(mc_hbb["jet_pt"]) > 20:
        auc = C.roc_auc(C.observables(mc_hbb)["HbbvsQCD"], C.observables(mc_qcd)["HbbvsQCD"])
        summary["auc_HbbvsQCD_CMSsim"] = auc
        md.append(f"- HbbvsQCD ROC AUC on CMS full simulation (truth labels): {auc:.4f}\n")
    if jc is not None:
        hbb = sub(jc, jc["label"] == 1)
        if jc_qcd and len(hbb["jet_pt"]) > 20:
            auc = C.roc_auc(C.observables(hbb)["HbbvsQCD"], C.observables(jc_qcd)["HbbvsQCD"])
            summary["auc_HbbvsQCD_JetClass"] = auc
            md.append(f"- HbbvsQCD ROC AUC on JetClass (same pT/eta window): {auc:.4f}\n")

    C.save_json(summary, os.path.join(args.out, "summary.json"))
    with open(os.path.join(args.out, "SUMMARY.md"), "w") as f:
        f.write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
