"""Score jets from CMS Open Data (collision data + simulation) and JetClass with GDS-ParT.

    python -m cmsod.run --source jetht      --files 1 --max-events 20000 --out results/local
    python -m cmsod.run --source singlemuon --files 2 --out results/run
    python -m cmsod.run --source mc_qcd_hbb --files 1 --max-jets 50000 --out results/run
    python -m cmsod.run --source jetclass --jetclass-files "D:/JetClass/val/ZJetsToNuNu_120.root" --out ...

Each call writes <out>/<source>.npz (+ <source>.meta.json).
"""
import argparse
import glob
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cmsod import gdspart, pipeline, records  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True,
                    choices=["jetht", "singlemuon", "mc_qcd_hbb", "jetclass"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--files", type=int, default=1, help="number of files of the record to read")
    ap.add_argument("--file-offset", type=int, default=0)
    ap.add_argument("--urls", nargs="*", help="explicit file URLs (override the record file list)")
    ap.add_argument("--max-events", type=int, default=None, help="per file, PFNano data")
    ap.add_argument("--max-jets", type=int, default=None, help="per file, simulation / JetClass")
    ap.add_argument("--jetclass-files", nargs="*", default=[])
    ap.add_argument("--no-golden", action="store_true", help="do not apply the 2016 golden JSON")
    ap.add_argument("--no-chs", action="store_true",
                    help="keep charged PF candidates with PUPPI weight 0 in data")
    ap.add_argument("--gds-part-dir", default=None)
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--download-to", default=None,
                    help="download model code + checkpoint here if no local repo is found")
    ap.add_argument("--device", default="cuda" if _cuda() else "cpu")
    ap.add_argument("--tag", default=None, help="output file stem (default: source)")
    args = ap.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    model, info = gdspart.load_model(args.ckpt, args.gds_part_dir, args.download_to, args.device)
    _, cache_mod, _ = gdspart.import_modules(args.gds_part_dir, args.download_to)
    print(f"[run] model {info['ckpt']} (epoch {info['epoch']}, JetClass val acc {info['val_acc']})")

    if args.source == "jetclass":
        urls = sorted(f for p in args.jetclass_files for f in glob.glob(p)) or args.jetclass_files
    elif args.urls:
        urls = args.urls
    else:
        urls = records.list_files(args.source, limit=args.file_offset + args.files)[args.file_offset:]
    golden = None
    if args.source in ("jetht", "singlemuon") and not args.no_golden:
        golden = records.load_golden_json()

    tables, n_events, t0, done = [], 0, time.time(), []
    for u in urls:
        if pipeline.past_deadline():
            print("[run] deadline reached, not opening more files")
            break
        print(f"[run] {args.source}: {u}", flush=True)
        try:
            if args.source == "jetht":
                tab, n = pipeline.process_pfnano(u, "qcd_dijet", model, cache_mod, golden, args.device,
                                                 args.max_events, chs_like=not args.no_chs)
                n_events += n
            elif args.source == "singlemuon":
                tab, n = pipeline.process_pfnano(u, "ttbar_mujets", model, cache_mod, golden,
                                                 args.device, args.max_events, chs_like=not args.no_chs)
                n_events += n
            elif args.source == "mc_qcd_hbb":
                tab = pipeline.process_mc(u, model, cache_mod, args.device, args.max_jets)
            else:
                tab = pipeline.process_jetclass(u, model, cache_mod, args.device, args.max_jets)
                tab["label"] = np.full(len(tab.get("jet_pt", [])), _jetclass_label(u))
        except Exception as e:  # e.g. a dropped HTTP connection: keep the other files
            print(f"[run] ERROR on {u}: {type(e).__name__}: {e}", flush=True)
            continue
        done.append(u)
        if tab:
            tables.append(tab)
        # written after every file so a timed-out job still leaves usable output
        _save(args, pipeline._concat(tables), done, n_events, golden, info, t0)
    _save(args, pipeline._concat(tables), done, n_events, golden, info, t0, final=True)


def _save(args, res, urls, n_events, golden, info, t0, final=False):
    stem = args.tag or args.source
    np.savez_compressed(os.path.join(args.out, f"{stem}.npz"), **res)
    meta = {"source": args.source, "files": urls, "n_events_read": n_events,
            "n_jets": int(len(res.get("jet_pt", []))), "golden_json": golden is not None,
            "chs_like": not args.no_chs, "model": info, "seconds": round(time.time() - t0, 1),
            "record": records.RECORDS.get(args.source, {}).get("recid")}
    with open(os.path.join(args.out, f"{stem}.meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[run] {'wrote' if final else 'checkpoint'} {stem}.npz: {meta['n_jets']} jets, "
          f"{n_events} events, {meta['seconds']} s", flush=True)


def _jetclass_label(path):
    base = os.path.basename(path)
    for i, pre in enumerate(["ZJetsToNuNu", "HToBB", "HToCC", "HToGG", "HToWW4Q", "HToWW2Q1L",
                             "ZToQQ", "WToQQ", "TTBarLep", "TTBar"]):
        if base.startswith(pre + "_"):
            return [0, 1, 2, 3, 4, 5, 6, 7, 9, 8][i]
    return -1


def _cuda():
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


if __name__ == "__main__":
    main()
