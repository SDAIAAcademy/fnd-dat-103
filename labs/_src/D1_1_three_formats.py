# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "pyarrow>=17", "duckdb>=1.1", "tzdata>=2025.1"]
# ///
# %% [markdown]
# # Lab 1.1 · One dataset, three formats
#
# Day 1 · Session 1 (File formats) · 80 min.
#
# The charging network's data team lead must choose the format in which charging sessions are
# handed from the platform to the analysts. You write one table of sessions as CSV, as JSON Lines
# and as Parquet, measure the size and the read time of each, check column by column which types
# survive the round trip, query the Parquet file with DuckDB, and write a comparison table with a
# recommendation.
#
# **AI policy: AI-tutor.** An assistant may explain an error or a function; write the code yourself.
#
# **Reference state.** The table is generated in the first cell from a fixed seed
# (`chargekit.make_sessions`); the lab needs no file and no earlier lab. Outputs go to `out/lab1_1/`
# (set `FDT103_OUT` to write them elsewhere).
#
# **Tasks**
# - [ ] 1 · Run the setup cell and generate the sessions table (5')
# - [ ] 2 · Write CSV, JSON Lines and Parquet and compare their sizes (15')
# - [ ] 3 · Read each file back and time it (15')
# - [ ] 4 · Check type fidelity column by column (20')
# - [ ] 5 · Query the Parquet file with DuckDB, and hand it an Arrow table (10')
# - [ ] 6 · Write the comparison table and a recommendation (15')
# - [ ] ✱ Stretch · Write the Parquet partitioned by day and query one partition

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

# %% [markdown]
# ## 1 · Generate the sessions table (5')
#
# One row per charging session. Look at the types before anything is written: `connector` is
# text with a leading zero ("01"), `started_at` is a time in UTC, `idle_min` is a whole number
# that may be missing, `status` is a category, `note_ar` is free Arabic text that sometimes holds
# a comma or quotation marks.

# %%
N = U.pick(200_000, 20_000)
df = U.make_sessions(N)
print(len(df), "sessions")
print(df.dtypes)
print(df.head(3).T)
U.check(len(df) == N and df["connector"].str.len().eq(2).all(), f"{N} sessions with two-character connector codes")

# %% [markdown]
# ## 2 · Write the three files and compare sizes (15')
#
# ✏️ **Exercise** · Write `write_three(df, folder)`: save `df` as `sessions.csv` (UTF-8, no index),
# `sessions.jsonl` (one JSON object per line, times as ISO 8601 text, Arabic kept as Arabic), and
# `sessions.parquet` (through a pyarrow table, zstd compression). Return a dict `{"csv": path,
# "jsonl": path, "parquet": path}`.

# %%
FOLDER = U.out_dir("lab1_1")

def write_three(df, folder):
    # BEGIN SOLUTION
    import pyarrow as pa
    import pyarrow.parquet as pq

    folder = Path(folder)
    paths = {"csv": folder / "sessions.csv", "jsonl": folder / "sessions.jsonl", "parquet": folder / "sessions.parquet"}
    df.to_csv(paths["csv"], index=False, encoding="utf-8")
    df.to_json(paths["jsonl"], orient="records", lines=True, date_format="iso", force_ascii=False)
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), paths["parquet"], compression="zstd")
    return paths
    # END SOLUTION

# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    paths = write_three(df, FOLDER)
except NotImplementedError:
    paths = U.ref_write_three(df, FOLDER)
sizes = {f: round(p.stat().st_size / 1024) for f, p in paths.items()}
print("size in KB:", sizes)
U.check(sizes["parquet"] < sizes["csv"] < sizes["jsonl"], "Parquet is the smallest and JSON Lines the largest")

# %% [markdown]
# **Look at** one CSV line that carries an Arabic note. The note holds a comma and quotation
# marks: see how the writer protected them (the whole field in quotes, each inner quote doubled).
# That is the dialect; a reader that assumes another one splits the field.

# %%
with open(paths["csv"], encoding="utf-8") as f:
    quoted = next(line for line in f if '""' in line)
print(quoted.rstrip())

# %% [markdown]
# ## 3 · Read each file back and time it (15')
#
# ✏️ **Exercise** · Write `read_back(fmt, path)` that reads a file with the pandas reader of its
# format and its default settings: `read_csv`, `read_json(lines=True)`, `read_parquet`. Defaults
# on purpose: they are what a colleague will use.

# %%
def read_back(fmt, path):
    # BEGIN SOLUTION
    if fmt == "csv":
        return pd.read_csv(path, encoding="utf-8")
    if fmt == "jsonl":
        return pd.read_json(path, lines=True)
    return pd.read_parquet(path)
    # END SOLUTION

# %%
try:
    back = {f: read_back(f, p) for f, p in paths.items()}
    reader = read_back
except NotImplementedError:
    back = {f: U.ref_read_back(f, p) for f, p in paths.items()}
    reader = U.ref_read_back
times = {f: U.median_seconds(lambda f=f: reader(f, paths[f]), repeat=U.pick(5, 3)) for f in paths}
print("median read time in seconds:", times)
U.check(all(len(b) == N for b in back.values()), "every file reads back with all its rows")

# %% [markdown]
# Read times depend on this computer, the run and the file cache: take the median of several
# reads, compare formats on the same machine, and never quote one run as a property of a format.

# %% [markdown]
# ## 4 · Type fidelity, column by column (20')
#
# ✏️ **Exercise** · Write `fidelity(original, back)` that returns `{column: True/False}`: True
# when the column came back with the same type (compare `str(dtype)`) **and** the same values.
# Compare values after casting the column back to the original type, and treat a failed cast as
# False.

# %%
def fidelity(original, back):
    # BEGIN SOLUTION
    out = {}
    for col in original.columns:
        same_type = col in back.columns and str(back[col].dtype) == str(original[col].dtype)
        try:
            same_values = col in back.columns and back[col].astype(original[col].dtype).equals(original[col])
        except Exception:
            same_values = False
        out[col] = bool(same_type and same_values)
    return out
    # END SOLUTION

# %%
try:
    fid = {f: fidelity(df, b) for f, b in back.items()}
except NotImplementedError:
    fid = {f: U.ref_fidelity(df, b) for f, b in back.items()}
table = pd.DataFrame(fid)
print(table)
U.check(table["parquet"].all(), "Parquet keeps every column's type and values")
U.check(not table.loc["connector", "csv"] and not table.loc["connector", "jsonl"], "CSV and JSON Lines both lose the connector code's type")

# %% [markdown]
# **Look at** what each loss means for the network: connector "01" read back as the number 1;
# `idle_min` as a decimal number; `status` as plain text. One JSON Lines column changed in a way
# you cannot see by eye: compare the largest difference below with the three decimals the data
# was written with, then read the `precise_float` parameter of `pd.read_json`.

# %%
diff = (back["jsonl"]["energy_kwh"] - df["energy_kwh"]).abs()
print("JSON Lines energy_kwh: rows changed", int((diff > 0).sum()), "| largest change", diff.max())
print("CSV started_at comes back as", back["csv"]["started_at"].dtype, "e.g.", back["csv"]["started_at"].iloc[0])

# %% [markdown]
# ## 5 · Query the Parquet file, and hand DuckDB an Arrow table (10')
#
# DuckDB reads Parquet directly and reads only the columns a query names. It can also query an
# Arrow table already in memory without copying it: the same columns are shared between the two
# libraries. Run both queries and compare the answers.

# %%
import duckdb
import pyarrow.parquet as pq

q = "SELECT station_id, round(sum(energy_kwh), 1) AS kwh FROM {src} GROUP BY station_id ORDER BY kwh DESC LIMIT 5"
from_file = duckdb.sql(q.format(src=f"read_parquet('{paths['parquet'].as_posix()}')")).df()
arrow_table = pq.read_table(paths["parquet"], columns=["station_id", "energy_kwh"])
from_arrow = duckdb.sql(q.format(src="arrow_table")).df()
print(from_file)
U.check(from_file.equals(from_arrow), "the file and the in-memory Arrow table give the same top five stations")

# %% [markdown]
# ## 6 · The comparison table and a recommendation (15')
#
# Put the measurements side by side: size, median read time, columns that kept their type, and
# which were lost. Then write three sentences for the data team lead: which format for the
# hand-over to analysts, which for an append-only log from the chargers, and what the CSV
# would need (a schema written down beside it) if a partner insists on CSV.

# %%
comparison = pd.DataFrame({
    "size_KB": sizes,
    "read_s_median": times,
    "columns_kept": {f: f"{int(table[f].sum())} of {len(table)}" for f in table},
    "columns_lost": {f: ", ".join(table.index[~table[f]]) or "none" for f in table},
})
print(comparison.to_string())
(FOLDER / "comparison.md").write_text(comparison.to_string(), encoding="utf-8")
U.check(comparison.loc["parquet", "columns_lost"] == "none", "the comparison table is written")

# %% [markdown]
# ### Check yourself
#
# 1. Why is JSON Lines the largest of the three here?
#    <details><summary>Answer</summary>Every line repeats every key name, and numbers and times are written as text; Parquet stores each column once, typed and compressed.</details>
# 2. A partner can only send CSV. What do you ask for besides the file?
#    <details><summary>Answer</summary>The dialect (delimiter, quoting, encoding, line ending) and a written schema: the type of each column, so "01" is read as text and times with their offset.</details>
# 3. Your read times differ from your neighbour's. Is the table wrong?
#    <details><summary>Answer</summary>No: times depend on the machine and the cache. Compare formats on one machine with a median; sizes and type fidelity are the stable findings.</details>
#
# **Carry forward.** Lab 2.2 writes Parquet again, partitioned by day, from a declared schema.

# %% [markdown]
# ## ✱ Stretch · Partition by day
#
# Write the table as a Parquet dataset partitioned by the UTC day of `started_at`
# (`pyarrow.dataset.write_dataset` with `partitioning=["day"]`, `partitioning_flavor="hive"`),
# then ask DuckDB for one day only and look at how many files it opens.
