# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "pyarrow>=17", "duckdb>=1.1", "httpx>=0.27", "fastapi>=0.115", "pandera>=0.22", "jsonschema>=4.23", "tzdata>=2025.1"]
# ///
# %% [markdown]
# # Setup check
#
# Run this notebook once before Day 1. It imports every library the labs use, reads one data
# file, calls the mock API once and checks that the time-zone database knows the zone of Vendor
# B's chargers. Every line it prints says what is ready; the last line says whether you are set.
# No lab of this course calls a language model, so no model key is needed.

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/fnd-dat-103.git"
    if not Path("/content/fnd-dat-103").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/fnd-dat-103"], check=True)
    os.chdir("/content/fnd-dat-103/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("chargekit.py").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")
sys.path.insert(0, os.getcwd())

import importlib.metadata as md

missing = []
for pkg in ["pandas", "pyarrow", "duckdb", "httpx", "fastapi", "pandera", "jsonschema", "tzdata"]:
    try:
        print(f"{pkg:>10} {md.version(pkg)}")
    except md.PackageNotFoundError:
        missing.append(pkg)
        print(f"{pkg:>10} MISSING")

import chargekit as U
import mockapi
from zoneinfo import ZoneInfo
from datetime import datetime

stations = U.stations()
print("data ready:", len(stations), "stations;", len(list((U.DATA / "damaged").iterdir())), "damaged files")
r = mockapi.client(token=U.load_token(), faults={}).get("/v1/terms")
print("mock API answers:", r.status_code)
z = ZoneInfo(U.VENDOR_B_ZONE)
print("time-zone database:", U.VENDOR_B_ZONE, datetime(2026, 10, 25, 2, 30, tzinfo=z, fold=0).utcoffset(), "then", datetime(2026, 10, 25, 2, 30, tzinfo=z, fold=1).utcoffset())
U.check(not missing and r.status_code == 200 and len(stations) == 40, "ready for the labs")
