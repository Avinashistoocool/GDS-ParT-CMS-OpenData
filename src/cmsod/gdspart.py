"""Locate and load the GDS-ParT model code + checkpoint from the original repo.

Nothing from the model repo is copied here: the model class and the JetClass
preprocessing (`data/jetclass_cache.py`) are imported from it so that the
inputs fed to the network on CMS data are built by *exactly* the code used in
training. The repo is found via, in order:
    1. the `gds_part_dir` argument
    2. the GDS_PART_DIR environment variable
    3. a sibling checkout ../gds_part (local development)
    4. download of the three needed files from GitHub at a pinned commit
"""
import os
import sys
import urllib.request

REPO = "Avinashistoocool/Gated-Dual-Stream-Particle-Transformer"
COMMIT = "b38f1b7d7ad5d67d4f4933b2a2fbe646fed26da7"
CKPT_REL = "checkpoints/v2_shared_10M_10ep/best.pt"
FILES = ["gds_part_colab.py", "data/jetclass_cache.py", CKPT_REL]

_HERE = os.path.dirname(os.path.abspath(__file__))
_SIBLING = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "gds_part"))


def _download(dest):
    for rel in FILES:
        out = os.path.join(dest, *rel.split("/"))
        if os.path.exists(out):
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{rel}"
        print(f"[gdspart] downloading {url}")
        urllib.request.urlretrieve(url, out)
    open(os.path.join(dest, "data", "__init__.py"), "a").close()
    return dest


def find_repo(gds_part_dir=None, download_to=None):
    for cand in (gds_part_dir, os.environ.get("GDS_PART_DIR"), _SIBLING):
        if cand and os.path.exists(os.path.join(cand, "gds_part_colab.py")):
            return os.path.abspath(cand)
    if download_to:
        return _download(download_to)
    raise FileNotFoundError(
        "GDS-ParT repo not found: set GDS_PART_DIR, pass gds_part_dir, or pass download_to")


def import_modules(gds_part_dir=None, download_to=None):
    """Returns (gds_part_colab module, jetclass_cache module, repo dir)."""
    repo = find_repo(gds_part_dir, download_to)
    if repo not in sys.path:
        sys.path.insert(0, repo)
    import importlib
    colab = importlib.import_module("gds_part_colab")
    cache = importlib.import_module("data.jetclass_cache")
    return colab, cache, repo


def load_model(ckpt=None, gds_part_dir=None, download_to=None, device="cpu"):
    """Builds GDSParT from the config stored in the checkpoint and loads the
    evaluation weights (EMA weights when the run used EMA)."""
    import torch
    colab, _, repo = import_modules(gds_part_dir, download_to)
    ckpt = ckpt or os.environ.get("GDS_PART_CKPT") or os.path.join(repo, *CKPT_REL.split("/"))
    ck = torch.load(ckpt, map_location="cpu", weights_only=False)
    cfg = colab.GDSParTConfig(**ck["config"])
    model = colab.GDSParT(cfg)
    model.load_state_dict(ck["model_state"])
    model.to(device).eval()
    info = {"ckpt": os.path.abspath(ckpt), "epoch": ck.get("epoch"), "val_acc": ck.get("val_acc"),
            "config": ck["config"]}
    return model, info
