# Kaggle kernel: GDS-ParT on CMS Open Data (data vs simulation).
# Clones github.com/Avinashistoocool/GDS-ParT-CMS-OpenData, downloads the model
# code + checkpoint at a pinned commit, streams CMS Open Data over HTTPS and
# writes scores, plots and a summary to /kaggle/working/results.
import glob
import os
import subprocess
import sys
import time


def sh(cmd):
    print("+", cmd, flush=True)
    r = subprocess.run(cmd, shell=True)
    return r.returncode


T0 = time.time()
BUDGET_S = float(os.environ.get("CMSOD_BUDGET_S", 10.5 * 3600))
WORK = "/kaggle/working"
OUT = f"{WORK}/results"
REPO = f"{WORK}/GDS-ParT-CMS-OpenData"

sh("pip install -q 'uproot>=5' awkward scikit-learn")
if not os.path.exists(REPO):
    sh(f"git clone --depth 1 https://github.com/Avinashistoocool/GDS-ParT-CMS-OpenData.git {REPO}")
sys.path.insert(0, f"{REPO}/src")
os.makedirs(OUT, exist_ok=True)
RUN = f"python {REPO}/src/cmsod/run.py --out {OUT} --download-to {WORK}/gds_part"

# Configuration (sizes chosen to fit the 12 h GPU session; reading is network bound)
N_JETHT_FILES = int(os.environ.get("N_JETHT_FILES", 3))
N_SMU_FILES = int(os.environ.get("N_SMU_FILES", 6))
N_MC_FILES = int(os.environ.get("N_MC_FILES", 2))
MAX_EVENTS = int(os.environ.get("MAX_EVENTS", 150000))

# 1. JetClass reference (Delphes, training domain) from the attached Kaggle dataset
jc = sorted(glob.glob("/kaggle/input/**/ZJetsToNuNu_12*.root", recursive=True))[:1] + \
     sorted(glob.glob("/kaggle/input/**/HToBB_12*.root", recursive=True))[:1] + \
     sorted(glob.glob("/kaggle/input/**/TTBar_12*.root", recursive=True))[:1]
print("JetClass files:", jc)
if jc:
    sh(f"{RUN} --source jetclass --max-jets 50000 --jetclass-files " + " ".join(jc))

# 2. CMS full simulation (QCD + H->bb AK8 jets, rec. 12102)
sh(f"{RUN} --source mc_qcd_hbb --files {N_MC_FILES}")
# 3. CMS collision data, QCD dijet control region (JetHT, rec. 31308)
sh(f"{RUN} --source jetht --files {N_JETHT_FILES} --max-events {MAX_EVENTS}")
# 4. CMS collision data, ttbar mu+jets control region (SingleMuon, rec. 31313)
if time.time() - T0 < BUDGET_S * 0.6:
    sh(f"{RUN} --source singlemuon --files {N_SMU_FILES}")

# 5. comparison + plots
sh(f"python {REPO}/src/cmsod/analyze.py --in {OUT} --out {OUT}/report")
sh(f"cd {WORK} && tar czf results.tgz results")
print(f"done in {(time.time() - T0) / 3600:.2f} h")
