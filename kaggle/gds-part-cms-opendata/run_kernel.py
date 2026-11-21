# Kaggle kernel: GDS-ParT on CMS Open Data (data vs simulation).
# Clones github.com/Avinashistoocool/GDS-ParT-CMS-OpenData, downloads the model
# code + checkpoint at a pinned commit, streams CMS Open Data over HTTPS and
# writes scores, plots and a summary to /kaggle/working/results.
# Sizes are set by env vars (defaults = full-size 12 h GPU session); the four
# sources are read in parallel because reading is network bound.
import glob
import os
import socket
import subprocess
import sys
import time

T0 = time.time()
CFG = {  # full-size defaults (v4 on CPU did 7 JetHT + 60 SingleMuon files in 2.3 h)
    "BUDGET_H": 10.5, "N_JETHT_FILES": 40, "MAX_EVENTS": 200000, "N_SMU_FILES": 200,
    "N_MC_FILES": 4, "MAX_MC_JETS": 0, "JC_JETS": 50000,
}
for k in CFG:
    if k in os.environ:
        CFG[k] = type(CFG[k])(os.environ[k])
print("config:", CFG, flush=True)

WORK = "/kaggle/working"
OUT = f"{WORK}/results"
REPO = os.environ.get("CMSOD_REPO", f"{WORK}/GDS-ParT-CMS-OpenData")
LOGS = f"{OUT}/logs"


def sh(cmd):
    print("+", cmd, flush=True)
    return subprocess.run(cmd, shell=True).returncode


try:
    socket.getaddrinfo("opendata.cern.ch", 443)
except OSError as e:
    raise SystemExit(
        f"No internet in this Kaggle session ({e}). CMS Open Data is streamed from opendata.cern.ch, "
        "so the kernel needs internet: verify the Kaggle account by phone and keep "
        "'enable_internet': true in kernel-metadata.json.")

sh("pip install -q 'uproot>=5' awkward scikit-learn aiohttp requests")
if not os.path.exists(REPO):
    sh(f"git clone --depth 1 https://github.com/Avinashistoocool/GDS-ParT-CMS-OpenData.git {REPO}")
sh(f"git -C {REPO} log -1 --oneline")
sh("nvidia-smi --query-gpu=name,memory.total --format=csv")
os.makedirs(LOGS, exist_ok=True)
# fetch model code + checkpoint once, before the parallel jobs start
sys.path.insert(0, f"{REPO}/src")
from cmsod import gdspart  # noqa: E402
gdspart.import_modules(download_to=f"{WORK}/gds_part")
os.environ["GDS_PART_DIR"] = f"{WORK}/gds_part"
os.environ["CMSOD_DEADLINE"] = str(T0 + CFG["BUDGET_H"] * 3600)

RUN = f"python -u {REPO}/src/cmsod/run.py --out {OUT}"
jobs = {}
jc = sorted(glob.glob("/kaggle/input/**/ZJetsToNuNu_12*.root", recursive=True))[:1] + \
     sorted(glob.glob("/kaggle/input/**/HToBB_12*.root", recursive=True))[:1] + \
     sorted(glob.glob("/kaggle/input/**/TTBar_12*.root", recursive=True))[:1] + \
     sorted(glob.glob("/kaggle/input/**/WToQQ_12*.root", recursive=True))[:1]
print("JetClass files:", jc, flush=True)
if jc:
    jobs["jetclass"] = f"{RUN} --source jetclass --max-jets {CFG['JC_JETS']} --jetclass-files " + " ".join(jc)
mc_cap = f" --max-jets {CFG['MAX_MC_JETS']}" if CFG["MAX_MC_JETS"] else ""
jobs["mc_qcd_hbb"] = f"{RUN} --source mc_qcd_hbb --files {CFG['N_MC_FILES']}{mc_cap}"
jobs["jetht"] = f"{RUN} --source jetht --files {CFG['N_JETHT_FILES']} --max-events {CFG['MAX_EVENTS']}"
jobs["singlemuon"] = f"{RUN} --source singlemuon --files {CFG['N_SMU_FILES']}"

procs = {}
for name, cmd in jobs.items():
    print("+", cmd, flush=True)
    procs[name] = subprocess.Popen(cmd, shell=True, stdout=open(f"{LOGS}/{name}.log", "w"),
                                   stderr=subprocess.STDOUT)
while procs:
    time.sleep(120)
    for name in list(procs):
        rc = procs[name].poll()
        if rc is not None:
            print(f"[{(time.time() - T0) / 3600:.2f} h] {name} finished rc={rc}", flush=True)
            del procs[name]
    for name in procs:
        tail = open(f"{LOGS}/{name}.log").read().strip().splitlines()[-1:]
        print(f"[{(time.time() - T0) / 3600:.2f} h] {name}: {tail}", flush=True)

for name in jobs:
    print(f"==== {name}.log (tail)")
    print("\n".join(open(f"{LOGS}/{name}.log").read().splitlines()[-8:]))
sh(f"python {REPO}/src/cmsod/analyze.py --in {OUT} --out {OUT}/report")
sh(f"cd {WORK} && tar czf results.tgz results")
print(f"done in {(time.time() - T0) / 3600:.2f} h")
