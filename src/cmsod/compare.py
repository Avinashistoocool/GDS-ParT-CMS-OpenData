"""Data/simulation comparison of tagger outputs: histograms with ratio panels,
chi2 and Kolmogorov-Smirnov tests, kinematic reweighting and slicing."""
import json
import os

import numpy as np

CLASS_LIST = ["QCD", "Hbb", "Hcc", "Hgg", "H4q", "Hqql", "Zqq", "Wqq", "Tbqq", "Tbl"]
DISCRIMINANTS = {"TvsQCD": "Tbqq", "WvsQCD": "Wqq", "ZvsQCD": "Zqq", "HbbvsQCD": "Hbb"}
SLICES = {
    "jet_pt": [500, 600, 700, 800, 1000],
    "abs_eta": [0.0, 0.5, 1.0, 1.5, 2.0],
    "n_constituents": [0, 30, 45, 60, 80, 200],
    "npv": [0, 10, 20, 30, 80],
}


def discriminant(scores, sig):
    """s_sig / (s_sig + s_QCD), the usual ParT-style binary discriminant."""
    s = scores[:, CLASS_LIST.index(sig)]
    b = scores[:, 0]
    return s / np.clip(s + b, 1e-12, None)


def observables(tab):
    """Dict of 1D arrays to compare: per-class softmax + binary discriminants."""
    sc = tab["scores"]
    out = {f"score_{c}": sc[:, i] for i, c in enumerate(CLASS_LIST)}
    out.update({d: discriminant(sc, s) for d, s in DISCRIMINANTS.items()})
    return out


def slice_var(tab, name):
    return np.abs(tab["jet_eta"]) if name == "abs_eta" else tab[name]


def reweight(src, tgt, var="jet_pt", bins=np.linspace(500, 1000, 26)):
    """Per-jet weights that make the src distribution of `var` match tgt."""
    hs, _ = np.histogram(src[var], bins)
    ht, _ = np.histogram(tgt[var], bins)
    hs = hs / max(hs.sum(), 1)
    ht = ht / max(ht.sum(), 1)
    r = np.divide(ht, hs, out=np.zeros_like(ht, dtype=float), where=hs > 0)
    i = np.clip(np.digitize(src[var], bins) - 1, 0, len(bins) - 2)
    return r[i]


def weighted_ks(x1, x2, w1=None, w2=None):
    """Two-sample KS statistic with weights, and an asymptotic p-value using
    Kish effective sample sizes."""
    w1 = np.ones(len(x1)) if w1 is None else np.asarray(w1, float)
    w2 = np.ones(len(x2)) if w2 is None else np.asarray(w2, float)
    o1, o2 = np.argsort(x1), np.argsort(x2)
    x1, w1, x2, w2 = x1[o1], w1[o1], x2[o2], w2[o2]
    allx = np.concatenate([x1, x2])
    c1 = np.concatenate([[0], np.cumsum(w1)])[np.searchsorted(x1, allx, side="right")] / w1.sum()
    c2 = np.concatenate([[0], np.cumsum(w2)])[np.searchsorted(x2, allx, side="right")] / w2.sum()
    d = float(np.max(np.abs(c1 - c2)))
    n1 = w1.sum() ** 2 / (w1 ** 2).sum()
    n2 = w2.sum() ** 2 / (w2 ** 2).sum()
    en = np.sqrt(n1 * n2 / (n1 + n2))
    from scipy.special import kolmogorov
    p = float(kolmogorov((en + 0.12 + 0.11 / en) * d))
    return d, p


def chi2_shape(x1, x2, w1=None, w2=None, bins=20, rng=(0, 1)):
    """Shape chi2 between two (normalized) weighted histograms, using sum-of-
    weights-squared errors. Bins with no entries in both are skipped."""
    w1 = np.ones(len(x1)) if w1 is None else w1
    w2 = np.ones(len(x2)) if w2 is None else w2
    h1, e = np.histogram(x1, bins, rng, weights=w1)
    v1, _ = np.histogram(x1, bins, rng, weights=w1 ** 2)
    h2, _ = np.histogram(x2, bins, rng, weights=w2)
    v2, _ = np.histogram(x2, bins, rng, weights=w2 ** 2)
    n1, n2 = h1.sum(), h2.sum()
    if n1 <= 0 or n2 <= 0:
        return np.nan, 0
    h1, v1, h2, v2 = h1 / n1, v1 / n1 ** 2, h2 / n2, v2 / n2 ** 2
    ok = (v1 + v2) > 0
    chi2 = float(np.sum((h1[ok] - h2[ok]) ** 2 / (v1[ok] + v2[ok])))
    return chi2, int(ok.sum() - 1)


def compare(a, b, wa=None, wb=None, bins=20):
    from scipy.stats import chi2 as chi2dist
    ks, p_ks = weighted_ks(a, b, wa, wb)
    c2, ndf = chi2_shape(a, b, wa, wb, bins)
    wa_ = np.ones(len(a)) if wa is None else wa
    wb_ = np.ones(len(b)) if wb is None else wb
    return {"n_a": int(len(a)), "n_b": int(len(b)),
            "mean_a": float(np.average(a, weights=wa_)) if len(a) else np.nan,
            "mean_b": float(np.average(b, weights=wb_)) if len(b) else np.nan,
            "ks": ks, "p_ks": p_ks, "chi2": c2, "ndf": ndf,
            "p_chi2": float(chi2dist.sf(c2, ndf)) if ndf > 0 else np.nan}


def compare_tables(ta, tb, wb=None, keys=None, slices=SLICES, min_jets=50):
    """Global and sliced comparison of all observables between table A (e.g.
    data) and table B (e.g. simulation, optionally weighted)."""
    oa, ob = observables(ta), observables(tb)
    keys = keys or list(oa)
    res = {"global": {k: compare(oa[k], ob[k], None, wb) for k in keys}, "slices": {}}
    for var, edges in slices.items():
        if var not in ta or var not in tb:
            if var != "abs_eta":
                continue
        va, vb = slice_var(ta, var), slice_var(tb, var)
        if var == "npv" and (np.all(va == 0) or np.all(vb == 0)):
            continue
        rows = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            sa, sb = (va >= lo) & (va < hi), (vb >= lo) & (vb < hi)
            if sa.sum() < min_jets or sb.sum() < min_jets:
                continue
            row = {"lo": lo, "hi": hi}
            for k in keys:
                row[k] = compare(oa[k][sa], ob[k][sb], None, None if wb is None else wb[sb])
            rows.append(row)
        res["slices"][var] = rows
    return res


def plot_compare(arrs, labels, weights=None, bins=25, rng=(0, 1), title="", xlabel="",
                 path=None, logy=True, ref=1):
    """Normalized histograms of several samples; ratio panel of each sample to
    arrs[ref] (simulation by convention) with statistical error bars."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    weights = weights or [None] * len(arrs)
    edges = np.linspace(*rng, bins + 1)
    ctr = 0.5 * (edges[1:] + edges[:-1])
    fig, (ax, rx) = plt.subplots(2, 1, figsize=(6, 5.5), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})
    hs = []
    for i, (x, lab, w) in enumerate(zip(arrs, labels, weights)):
        w = np.ones(len(x)) if w is None else w
        h, _ = np.histogram(x, edges, weights=w)
        v, _ = np.histogram(x, edges, weights=w ** 2)
        n = max(h.sum(), 1e-12)
        h, err = h / n / np.diff(edges), np.sqrt(v) / n / np.diff(edges)
        hs.append((h, err))
        if i == 0:
            ax.errorbar(ctr, h, err, fmt="ko", ms=3, label=f"{lab} ({len(x):,})")
        else:
            ax.step(edges, np.append(h, h[-1]), where="post", label=f"{lab} ({len(x):,})")
    hr, er = hs[ref]
    for i, (h, err) in enumerate(hs):
        if i == ref:
            rel = np.divide(er, hr, out=np.zeros_like(hr), where=hr > 0)
            rx.fill_between(edges, np.append(1 - rel, 1 - rel[-1]), np.append(1 + rel, 1 + rel[-1]),
                            step="post", color="grey", alpha=0.3)
            continue
        r = np.divide(h, hr, out=np.full_like(h, np.nan), where=hr > 0)
        re = np.divide(err, hr, out=np.full_like(h, np.nan), where=hr > 0)
        rx.errorbar(ctr, r, re, fmt="o" if i == 0 else "s", ms=3,
                    color="k" if i == 0 else None, label=labels[i])
    rx.axhline(1, color="grey", lw=0.8)
    rx.set_ylim(0, 2)
    rx.set_ylabel(f"/ {labels[ref]}", fontsize=8)
    rx.set_xlabel(xlabel)
    ax.set_ylabel("normalized")
    if logy:
        ax.set_yscale("log")
    ax.legend(fontsize=8)
    ax.set_title(title, fontsize=10)
    if path:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def roc_auc(sig, bkg):
    from sklearn.metrics import roc_auc_score
    y = np.r_[np.ones(len(sig)), np.zeros(len(bkg))]
    return float(roc_auc_score(y, np.r_[sig, bkg]))


def save_json(obj, path):
    def default(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=default)


def markdown_summary(res, title, keys=("score_QCD", "TvsQCD", "WvsQCD", "HbbvsQCD")):
    lines = [f"### {title}", "", "| observable | mean A | mean B | KS D | p(KS) | chi2/ndf |",
             "|---|---|---|---|---|---|"]
    for k in keys:
        g = res["global"][k]
        lines.append(f"| {k} | {g['mean_a']:.4f} | {g['mean_b']:.4f} | {g['ks']:.3f} | "
                     f"{g['p_ks']:.2g} | {g['chi2']:.1f}/{g['ndf']} |")
    for var, rows in res["slices"].items():
        lines += ["", f"KS D of `TvsQCD` / `score_QCD` in slices of **{var}**:", "",
                  "| slice | n A | n B | KS D (TvsQCD) | KS D (score_QCD) | mean QCD A | mean QCD B |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows:
            t, q = r["TvsQCD"], r["score_QCD"]
            lines.append(f"| [{r['lo']}, {r['hi']}) | {t['n_a']} | {t['n_b']} | {t['ks']:.3f} | "
                         f"{q['ks']:.3f} | {q['mean_a']:.3f} | {q['mean_b']:.3f} |")
    return "\n".join(lines) + "\n"
