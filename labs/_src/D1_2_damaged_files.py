# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "tzdata>=2025.1"]
# ///
# %% [markdown]
# # Lab 1.2 · Six damaged files
#
# Day 1 · Session 2 (Text and time) · 90 min.
#
# Six files reached the charging network's data team this week: four from the station team's old
# systems and two charger logs from Vendor A and Vendor B. Each one is damaged in a different way.
# You look at the bytes, write a diagnosis for each file before repairing anything, then repair
# the four text files and the two sets of timestamps, check the repairs against the clean
# register and the platform's own UTC times, and write a repair log.
#
# **AI policy: AI-off for task 2** (the diagnosis sheet is your own reading of the evidence), AI-tutor
# for the rest.
#
# **Reference state.** The lab starts from `data/damaged/` (six files), `data/stations.csv` and
# `data/platform_sessions.csv`. It needs no earlier lab.
#
# **Tasks**
# - [ ] 1 · Run the setup cell and look at the six files as bytes (10')
# - [ ] 2 · Write the diagnosis sheet, without an assistant (20')
# - [ ] 3 · Repair the four text files (25')
# - [ ] 4 · Convert Vendor A's times to UTC (10')
# - [ ] 5 · Convert Vendor B's times to UTC across the clock change (15')
# - [ ] 6 · Check against the platform and write the repair log (10')
# - [ ] ✱ Stretch · Guess the code page of a file without being told

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
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import chargekit as U
import pandas as pd

DMG = U.DATA / "damaged"
FILES = sorted(p.name for p in DMG.iterdir())
print(FILES)
U.check(len(FILES) == 6, "six damaged files are in place")

# %% [markdown]
# ## 1 · Look at the bytes (10')
#
# Before any reader guesses for you, look at what is actually in each file: the first bytes in
# hexadecimal and what a UTF-8 decoder makes of them. Note anything odd: a byte order mark
# (`ef bb bf`, `ff fe`), a zero byte after every letter, replacement characters (`�`), Arabic
# that reads as a different alphabet, line endings (`0d 0a`).

# %%
for name in FILES:
    U.peek(DMG / name, 40)

# %% [markdown]
# The two charger logs look clean as text. Their fault is in what the times mean. Compare a few
# of their sessions with the platform's own record of the same sessions, which keeps UTC.

# %%
platform = pd.read_csv(U.DATA / "platform_sessions.csv", dtype=str)
vend_a = pd.read_csv(DMG / "vendor_a_sessions.csv", dtype=str)
vend_b = pd.read_csv(DMG / "vendor_b_sessions.csv", dtype=str)
for name, v in (("Vendor A", vend_a), ("Vendor B", vend_b)):
    m = v.merge(platform, on="session_id")
    gap = (pd.to_datetime(m["started"]) - pd.to_datetime(m["started_utc"]).dt.tz_localize(None)).dt.total_seconds() / 60
    print(name, "| minutes between the log and the platform:", sorted(int(g) for g in gap.unique()))
print(vend_b.iloc[5:14].to_string(index=False))

# %% [markdown]
# ## 2 · The diagnosis sheet (20', AI-off)
#
# For each file, write the code of the fault and one line of evidence from what you saw.
#
# | Code | Fault |
# |---|---|
# | A | Arabic text in a legacy code page (Windows-1256), read as UTF-8 |
# | B | A UTF-8 byte order mark at the start of the file |
# | C | Double encoding: UTF-8 bytes once decoded as Windows-1256 and saved again as UTF-8 |
# | D | UTF-16 text (two bytes per character) |
# | E | Local times without an offset, from a clock on a fixed offset |
# | F | Local times without an offset, from a clock in a zone with daylight saving |
#
# ✏️ **Exercise** · Fill `DIAGNOSIS` with one code per file and `EVIDENCE` with one line each.
# The check tells you how many codes are right, not which.

# %%
def diagnosis_sheet():
    # BEGIN SOLUTION
    codes = {
        "station_register_legacy.csv": "A",
        "tariffs.csv": "B",
        "station_notes.csv": "C",
        "maintenance_log.txt": "D",
        "vendor_a_sessions.csv": "E",
        "vendor_b_sessions.csv": "F",
    }
    evidence = {
        "station_register_legacy.csv": "UTF-8 cannot decode the single high bytes (e3 c8 e4 ...) where the Arabic names should be; CRLF line endings of an old export",
        "tariffs.csv": "starts with ef bb bf; the first column name is read with an invisible character",
        "station_notes.csv": "valid UTF-8, but the Arabic reads as long runs of two-letter pairs starting with the same letters",
        "maintenance_log.txt": "starts with ff fe and every ASCII letter is followed by 00",
        "vendor_a_sessions.csv": "a constant 180 minutes ahead of the platform's UTC times",
        "vendor_b_sessions.csv": "120 minutes ahead before 25 October and 60 after; seq 9 and 10 end before they start; seq 11 starts before seq 10",
    }
    return codes, evidence
    # END SOLUTION

# %%
try:
    DIAGNOSIS, EVIDENCE = diagnosis_sheet()
except NotImplementedError:
    DIAGNOSIS, EVIDENCE = {}, {}
fp = U.reference("diagnosis_fingerprints")
right = sum(U.digest([f"{f}:{DIAGNOSIS.get(f, '')}"]) == fp[f] for f in FILES)
print(f"diagnosis: {right} of 6 right")
if right == 0:
    print("Write the diagnosis sheet first: the repairs below still run, but they will not tell you why.")
else:
    U.check(right >= 5, "the diagnosis is right on at least five of six files (the outcome's evidence)")

# %% [markdown]
# ## 3 · Repair the four text files (25')
#
# ✏️ **Exercise** · Write `read_text_file(path)` that returns the file as a DataFrame of text
# columns (`dtype=str`), decoded correctly. One branch per file is fine: the point is the right
# decoding for each fault. For double encoding, undo the wrong step: encode the text back to the
# bytes the wrong decoder saw, then decode those bytes as UTF-8.

# %%
import io

def read_text_file(path):
    # BEGIN SOLUTION
    name = Path(path).name
    if name == "station_register_legacy.csv":
        return pd.read_csv(path, encoding="cp1256", dtype=str)
    if name == "tariffs.csv":
        return pd.read_csv(path, encoding="utf-8-sig", dtype=str)  # the -sig codec drops the mark
    if name == "station_notes.csv":
        text = Path(path).read_text(encoding="utf-8").encode("cp1256").decode("utf-8")
        return pd.read_csv(io.StringIO(text), dtype=str)
    if name == "maintenance_log.txt":
        return pd.read_csv(path, encoding="utf-16", sep="\t", dtype=str)  # the mark tells the byte order
    raise ValueError(f"not a text file of this lab: {name}")
    # END SOLUTION

# %%
TEXT_FILES = ["station_register_legacy.csv", "tariffs.csv", "station_notes.csv", "maintenance_log.txt"]
repaired = {}
for name in TEXT_FILES:
    try:
        repaired[name] = read_text_file(DMG / name)
    except NotImplementedError:
        repaired[name] = U.ref_read_text_file(DMG / name)
clean = pd.read_csv(U.DATA / "stations.csv", dtype=str)
reg = repaired["station_register_legacy.csv"]
U.check(reg["name_ar"].tolist() == clean["name_ar"].tolist(), "the legacy register's 40 Arabic names match the clean register")
U.check(repaired["tariffs.csv"].columns[0] == "tariff_code", "the tariff table's first column is 'tariff_code', with no mark in front")
U.check(repaired["station_notes.csv"]["note_ar"].str.contains("ملاحظات").any(), "the station notes read as Arabic again")
U.check(repaired["maintenance_log.txt"].shape == (16, 3), "the maintenance log has 16 rows and 3 columns")
print(repaired["station_notes.csv"].head(4).to_string(index=False))

# %% [markdown]
# ## 4 · Vendor A's times to UTC (10')
#
# Vendor A's chargers write the network's local time, a fixed UTC+03:00, with no offset. Make the
# times aware of that offset, then convert them to UTC.
#
# ✏️ **Exercise** · Write `to_utc_fixed(df)` that returns a copy with `started` and `ended` as
# UTC times. `U.LOCAL` is the fixed offset.

# %%
def to_utc_fixed(df):
    # BEGIN SOLUTION
    out = df.copy()
    for col in ("started", "ended"):
        out[col] = pd.to_datetime(df[col]).dt.tz_localize(U.LOCAL).dt.tz_convert("UTC")
    return out
    # END SOLUTION

# %%
try:
    a_utc = to_utc_fixed(vend_a)
except NotImplementedError:
    a_utc = U.ref_to_utc_fixed(vend_a)
truth = platform.set_index("session_id")
Z = "%Y-%m-%dT%H:%M:%SZ"  # compare as UTC text: no doubt about units or zones

def same_as_platform(frame, col):
    mine = frame.set_index("session_id")[col].dt.strftime(Z)
    return mine.eq(truth.loc[mine.index, col + "_utc"]).all()

ok_a = same_as_platform(a_utc, "started") and same_as_platform(a_utc, "ended")
U.check(ok_a, "Vendor A's 30 sessions equal the platform's UTC times")

# %% [markdown]
# ## 5 · Vendor B's times to UTC, across the clock change (15')
#
# Vendor B's chargers keep their factory zone, `CET`, which has daylight saving: on 25 October
# 2026 its clocks went back from 03:00 to 02:00, so every time from 02:00 to 02:59 that night
# happened twice. A time alone cannot say which pass it was. The log's `seq` column can: it counts
# sessions in the order they started.
#
# ✏️ **Exercise** · Write `to_utc_dst(df)`. For each start, in `seq` order, take the first pass
# (`fold=0`) unless that would put it before the previous session's start; then take the second
# pass (`fold=1`). Compare in UTC: Python compares two times of the same zone by their clock
# reading and ignores `fold`. For each end, take the first UTC reading after its start.

# %%
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def to_utc_dst(df):
    # BEGIN SOLUTION
    zone = ZoneInfo(U.VENDOR_B_ZONE)
    out = df.sort_values("seq", key=lambda s: s.astype(int)).copy()
    starts, ends, last = [], [], None
    for _, r in out.iterrows():
        naive = datetime.fromisoformat(r["started"])
        first = naive.replace(tzinfo=zone, fold=0).astimezone(timezone.utc)
        second = naive.replace(tzinfo=zone, fold=1).astimezone(timezone.utc)
        s = first if last is None or first >= last else second
        last = s
        e_naive = datetime.fromisoformat(r["ended"])
        options = sorted({e_naive.replace(tzinfo=zone, fold=f).astimezone(timezone.utc) for f in (0, 1)})
        ends.append(next(t for t in options if t > s))
        starts.append(s)
    out["started"] = pd.to_datetime(starts, utc=True)
    out["ended"] = pd.to_datetime(ends, utc=True)
    return out
    # END SOLUTION

# %%
try:
    b_utc = to_utc_dst(vend_b)
except NotImplementedError:
    b_utc = U.ref_to_utc_dst(vend_b)
U.check(bool(same_as_platform(b_utc, "started") and same_as_platform(b_utc, "ended")), "Vendor B's 30 sessions equal the platform's UTC times, the repeated hour included")
naive_minutes = (pd.to_datetime(vend_b["ended"]) - pd.to_datetime(vend_b["started"])).dt.total_seconds() / 60
print("negative durations before the repair:", int((naive_minutes < 0).sum()), "| after:", int(((b_utc["ended"] - b_utc["started"]).dt.total_seconds() < 0).sum()))

# %% [markdown]
# ## 6 · The repair log (10')
#
# A repair nobody can see is a new fault. Write one line per file: the symptom, the cause, the
# repair, and the rows it touched. Save it beside the repaired files.

# %%
OUTDIR = U.out_dir("lab1_2")
log = pd.DataFrame([
    {"file": f, "code": DIAGNOSIS.get(f, "?"), "evidence": EVIDENCE.get(f, ""),
     "rows": len(repaired[f]) if f in repaired else len(a_utc if f.startswith("vendor_a") else b_utc)}
    for f in FILES
])
log["repair"] = log["file"].map({
    "station_register_legacy.csv": "decoded as cp1256, saved as UTF-8",
    "tariffs.csv": "decoded as utf-8-sig, saved as UTF-8 without a mark",
    "station_notes.csv": "encoded back to cp1256 bytes, decoded as UTF-8",
    "maintenance_log.txt": "decoded as UTF-16, tab-separated, saved as UTF-8 CSV",
    "vendor_a_sessions.csv": "localised to +03:00, converted to UTC",
    "vendor_b_sessions.csv": "localised to CET with fold chosen by seq order, converted to UTC",
})
for f, frame in repaired.items():
    frame.to_csv(OUTDIR / (Path(f).stem + ".utf8.csv"), index=False, encoding="utf-8")
a_utc.to_csv(OUTDIR / "vendor_a_sessions.utc.csv", index=False)
b_utc.to_csv(OUTDIR / "vendor_b_sessions.utc.csv", index=False)
log.to_csv(OUTDIR / "repair_log.csv", index=False, encoding="utf-8")
print(log[["file", "code", "rows", "repair"]].to_string(index=False))
U.check(len(log) == 6 and log["repair"].notna().all(), "the repair log has one line per file")

# %% [markdown]
# ### Check yourself
#
# 1. Why is "the file opened without an error" not proof that it was decoded right?
#    <details><summary>Answer</summary>Windows-1256 maps every byte to some character, so a wrong decoding never fails: it returns the wrong letters. Confirm with a word you know should be there.</details>
# 2. Vendor B's log is 120 minutes off on some days and 60 on others. What does that tell you?
#    <details><summary>Answer</summary>The clock follows a zone with daylight saving; a fixed shift would be the same every day, as Vendor A's is.</details>
# 3. Which single change at the source would have prevented both timestamp faults?
#    <details><summary>Answer</summary>Writing times with their offset (ISO 8601 with "+03:00" or "Z"), or in UTC.</details>
#
# **Carry forward.** Lab 2.2 rejects any timestamp that arrives without an offset.

# %% [markdown]
# ## ✱ Stretch · Guess the code page
#
# Write `guess(raw)` that tries `utf-8`, `cp1256`, `iso-8859-6` and `utf-16` and keeps the one
# whose text has the largest share of Arabic letters and digits and no replacement characters.
# Run it on the four text files. Which file fools it, and why?
