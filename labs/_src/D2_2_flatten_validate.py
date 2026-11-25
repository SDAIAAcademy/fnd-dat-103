# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "pyarrow>=17", "pandera>=0.22", "jsonschema>=4.23"]
# ///
# %% [markdown]
# # Lab 2.2 · Flatten, write, validate
#
# Day 2 · Session 2 (Schema and validation) · 90 min.
#
# The charging network's finance controller reads charging sessions from typed tables, never from
# the API's nested JSON. You turn the raw responses of a clean pull into two typed tables
# (sessions and their meter readings), write them as Parquet partitioned by day, and prove that
# the written schema is the declared one. Then you put checks at the boundary: a JSON Schema for
# each record and table checks with Pandera, run five batches (one clean, four with seeded
# defects) and decide for each: load it, load it and quarantine some rows, or reject it whole.
#
# **AI policy: AI-tutor.**
#
# **Reference state.** The lab starts from `data/raw_api/` (12 raw pages of a clean pull, the same
# shape lab 2.1 saves), `data/batches/`, `data/stations.csv` and `schema/session.schema.json`.
# It needs no earlier lab. Outputs go to `out/lab2_2/`.
#
# **Tasks**
# - [ ] 1 · Check every raw record against the JSON Schema (15')
# - [ ] 2 · Flatten into sessions and readings tables (20')
# - [ ] 3 · Write day-partitioned Parquet with the declared schema; check it (15')
# - [ ] 4 · Declare the table checks with Pandera (15')
# - [ ] 5 · Validate five batches and write the report (20')
# - [ ] 6 · Read the quarantine file as its owner (5')
# - [ ] ✱ Stretch · Add an optional field (schema version 2) without breaking version 1

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

import json
import shutil

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

import chargekit as U

OUTDIR = U.out_dir("lab2_2")
shutil.rmtree(OUTDIR)
OUTDIR.mkdir(parents=True)
pages = sorted((U.DATA / "raw_api").glob("page-*.json"))
records = [rec for p in pages for rec in json.loads(p.read_text(encoding="utf-8"))["body"]["data"]]
print(len(pages), "raw pages,", len(records), "records")
U.check(len(records) == 1200, "the raw pages hold 1,200 records")

# %% [markdown]
# ## 1 · Each record against the declared JSON Schema (15')
#
# `schema/session.schema.json` is the declared shape of one record: required fields, types,
# patterns (a time must carry its offset), allowed values. Open it and read it before running
# the cell.
#
# ✏️ **Exercise** · Write `record_rule(validator, rec)`: `None` when the record is valid, otherwise
# the rule of its first error (sorted by path): `missing_field` for a `required` error,
# `wrong_type` for a `type` error, `no_offset` for a `pattern` error on `started_at`, `ended_at` or
# `at`, and `invalid` for anything else.

# %%
validator = U.record_validator()

def record_rule(validator, rec):
    # BEGIN SOLUTION
    errors = sorted(validator.iter_errors(rec), key=lambda e: list(e.absolute_path))
    if not errors:
        return None
    e = errors[0]
    if e.validator == "required":
        return "missing_field"
    if e.validator == "type":
        return "wrong_type"
    if e.validator == "pattern" and e.absolute_path and str(list(e.absolute_path)[-1]) in ("started_at", "ended_at", "at"):
        return "no_offset"
    return "invalid"
    # END SOLUTION

# %%
try:
    rules = [record_rule(validator, r) for r in records]
    RULE = record_rule
except NotImplementedError:
    rules = [U.ref_record_rule(validator, r) for r in records]
    RULE = U.ref_record_rule
probe = json.loads(json.dumps(records[0]))
probe["started_at"] = probe["started_at"][:19]
U.check(rules.count(None) == 1200, "all 1,200 raw records match the declared schema")
U.check(RULE(validator, probe) == "no_offset", "a time without its offset is caught as no_offset")

# %% [markdown]
# ## 2 · Flatten: one table per grain (20')
#
# One session holds a station object, a tariff object and a list of readings. Objects that occur
# once per session become columns of the sessions table; the list becomes a second table, one row
# per reading, that carries `session_id` down so the two can be joined back.
#
# ✏️ **Exercise** · Write `flatten(records)` that returns `(sessions, readings)`:
# sessions with `session_id, station_id, sector, connector, started_at, ended_at, energy_kwh,
# tariff_code, per_kwh, amount, account, status, day`; readings with `session_id, seq, at, kwh,
# kw`. Parse the times as UTC (`pd.to_datetime(..., utc=True, format="ISO8601")`); `day` is the
# UTC date of `started_at` as text ("2026-10-21").

# %%
def flatten(records):
    # BEGIN SOLUTION
    s_rows, r_rows = [], []
    for rec in records:
        s_rows.append({
            "session_id": rec["session_id"], "station_id": rec["station"]["id"], "sector": rec["station"]["sector"],
            "connector": rec["station"]["connector"], "started_at": rec["started_at"], "ended_at": rec["ended_at"],
            "energy_kwh": rec["energy_kwh"], "tariff_code": rec["tariff"]["code"], "per_kwh": rec["tariff"]["per_kwh"],
            "amount": rec["amount"], "account": rec["account"], "status": rec["status"],
        })
        for rd in rec["readings"]:
            r_rows.append({"session_id": rec["session_id"], "seq": rd["seq"], "at": rd["at"], "kwh": rd["kwh"], "kw": rd["kw"]})
    s, r = pd.DataFrame(s_rows), pd.DataFrame(r_rows)
    for col in ("started_at", "ended_at"):
        s[col] = pd.to_datetime(s[col], utc=True, format="ISO8601")
    r["at"] = pd.to_datetime(r["at"], utc=True, format="ISO8601")
    s["day"] = s["started_at"].dt.strftime("%Y-%m-%d")
    return s, r
    # END SOLUTION

# %%
try:
    sessions, readings = flatten(records)
    FLAT = flatten
except NotImplementedError:
    sessions, readings = U.ref_flatten(records)
    FLAT = U.ref_flatten
n_readings = sum(len(r["readings"]) for r in records)
print(sessions.shape, readings.shape)
print(sessions.head(2).T)
U.check(len(sessions) == 1200 and sessions["session_id"].is_unique, "one row per session")
U.check(len(readings) == n_readings and set(readings["session_id"]) == set(sessions["session_id"]), f"{n_readings} readings, each joined to its session")

# %% [markdown]
# ## 3 · Declared types, partitioned Parquet, and a check of what was written (15')
#
# The declared table schemas are in `chargekit` (`U.sessions_schema()`, `U.readings_schema()`):
# names, types, time zone, and no missing values. Cast to them (a cast that cannot be done raises
# here, not in the finance report), write each table as Parquet partitioned by `day` for sessions,
# then read back the schema of the files that were written and compare.

# %%
S_SCHEMA, R_SCHEMA = U.sessions_schema(), U.readings_schema()
print(S_SCHEMA)

def write_partitioned(sessions, readings, folder):
    # BEGIN SOLUTION
    folder = Path(folder)
    s_tab = pa.Table.from_pandas(sessions, schema=S_SCHEMA, preserve_index=False)
    r_tab = pa.Table.from_pandas(readings, schema=R_SCHEMA, preserve_index=False)
    ds.write_dataset(s_tab, folder / "sessions", format="parquet", partitioning=["day"], partitioning_flavor="hive",
                     existing_data_behavior="delete_matching")
    pq.write_table(r_tab, folder / "readings.parquet", compression="zstd")
    return folder / "sessions", folder / "readings.parquet"
    # END SOLUTION

# %%
try:
    s_dir, r_file = write_partitioned(sessions, readings, OUTDIR / "tables")
except NotImplementedError:
    s_dir, r_file = OUTDIR / "tables" / "sessions", OUTDIR / "tables" / "readings.parquet"
    ds.write_dataset(pa.Table.from_pandas(sessions, schema=S_SCHEMA, preserve_index=False), s_dir, format="parquet",
                     partitioning=["day"], partitioning_flavor="hive", existing_data_behavior="delete_matching")
    pq.write_table(pa.Table.from_pandas(readings, schema=R_SCHEMA, preserve_index=False), r_file)
parts = sorted(p.name for p in s_dir.iterdir())
one_file = next(s_dir.rglob("*.parquet"))
written = pq.read_schema(one_file).remove_metadata()
declared_in_file = S_SCHEMA.remove(S_SCHEMA.get_field_index("day"))  # the partition column lives in the folder name
print(len(parts), "day partitions, e.g.", parts[:3])
U.check(written.equals(declared_in_file), "the written session files have exactly the declared schema")
U.check(pq.read_schema(r_file).remove_metadata().equals(R_SCHEMA), "the written readings file has exactly the declared schema")
back = ds.dataset(s_dir, format="parquet", partitioning="hive").to_table()
U.check(back.num_rows == 1200, "reading the partitioned folder back gives all 1,200 sessions")

# %% [markdown]
# ## 4 · Table checks with Pandera (15')
#
# Some rules need the whole table or a second source: a key that must be unique in the batch, a
# range, one column compared with another, a value that must exist in the station register.
#
# ✏️ **Exercise** · Write `table_checks(register_ids)` returning a `pandera.pandas.DataFrameSchema`
# with four named checks: `duplicate_key` (no `session_id` twice, flagging every copy),
# `out_of_range` (`energy_kwh` between 0 and 350), `unknown_station` (`station_id` in the register)
# and, at table level, `end_before_start` (`ended_at` after `started_at`). Give each check its rule
# name with `name=`: the report uses it.

# %%
import pandera.pandas as pda
import pandera.errors as pe

register = pd.read_csv(U.DATA / "stations.csv", dtype=str)["station_id"].tolist()

def table_checks(register_ids):
    # BEGIN SOLUTION
    ids = set(register_ids)
    return pda.DataFrameSchema(
        {
            "session_id": pda.Column(None, pda.Check(lambda s: ~s.duplicated(keep=False), name="duplicate_key")),
            "station_id": pda.Column(None, pda.Check(lambda s: s.isin(ids), name="unknown_station")),
            "energy_kwh": pda.Column(None, pda.Check(lambda s: s.between(0, 350), name="out_of_range")),
        },
        checks=[pda.Check(lambda df: df["ended_at"] > df["started_at"], name="end_before_start")],
    )
    # END SOLUTION

# %%
try:
    CHECKS = table_checks(register)
except NotImplementedError:
    CHECKS = U.ref_table_checks(register)
CHECKS.validate(sessions, lazy=True)
bad = sessions.copy()
bad.loc[0, "energy_kwh"] = -1.0
try:
    CHECKS.validate(bad, lazy=True)
    caught = []
except pe.SchemaErrors as err:
    caught = sorted(set(err.failure_cases["check"]))
U.check(caught == ["out_of_range"], "the clean table passes and a negative energy fails as out_of_range")

# %% [markdown]
# ## 5 · Five batches: load, quarantine or reject (20')
#
# The network's own rules for a batch, in this order:
#
# 1. a required field missing from 90% or more of the records is a changed interface, not bad
#    rows: **reject** the batch and report `schema_break:<field>`;
# 2. each record that breaks the JSON Schema is **quarantined** with its rule;
# 3. the table checks run on the rest; each failing row is **quarantined** with its rules;
# 4. if more than 5% of the batch is quarantined, **reject** the batch whole; otherwise **load**
#    the good rows.
#
# ✏️ **Exercise** · Write `validate_batch(records)` returning `(decision, defects, good, quarantined)`:
# `defects` the sorted, de-duplicated `(session_id, rule)` pairs (`("*", "schema_break:...")` for
# rule 1), `good` the records to load (none when rejected), `quarantined` `(record, rule)` pairs.

# %%
def validate_batch(records):
    # BEGIN SOLUTION
    n = len(records)
    for field in validator.schema["required"]:
        if n and sum(field not in r for r in records) / n >= U.SCHEMA_BREAK_SHARE:
            return "reject", [("*", f"schema_break:{field}")], [], []
    defects, good, quarantined = [], [], []
    for rec in records:
        rule = RULE(validator, rec)
        if rule:
            defects.append((rec.get("session_id", "?"), rule))
            quarantined.append((rec, rule))
        else:
            good.append(rec)
    if good:
        table, _ = FLAT(good)
        try:
            CHECKS.validate(table, lazy=True)
        except pe.SchemaErrors as err:
            failed = {}
            for _, row in err.failure_cases.dropna(subset=["index"]).iterrows():
                failed.setdefault(int(row["index"]), set()).add(str(row["check"]))
            keep = []
            for i, rec in enumerate(good):
                if i in failed:
                    defects += [(rec["session_id"], rule) for rule in failed[i]]
                    quarantined.append((rec, ",".join(sorted(failed[i]))))
                else:
                    keep.append(rec)
            good = keep
    decision = "reject" if len(quarantined) / n > U.MAX_QUARANTINE_SHARE else "load"
    return decision, sorted(set(defects)), (good if decision == "load" else []), quarantined
    # END SOLUTION

# %%
fp = U.reference("batch_fingerprints")
report_rows, results = [], {}
for path in sorted((U.DATA / "batches").glob("batch_*.jsonl")):
    b = path.stem
    batch = U.load_jsonl(path)
    try:
        decision, defects, good, quarantined = validate_batch(batch)
    except NotImplementedError:
        decision, defects, good, quarantined = U.ref_validate_batch(batch, validator, CHECKS)
    results[b] = (decision, defects, good, quarantined)
    caught_all = U.digest([f"{sid}:{rule}" for sid, rule in defects]) == fp[b]["defects"]
    right_call = U.digest([f"{b}:{decision}"]) == fp[b]["decision"]
    report_rows.append({"batch": b, "records": len(batch), "decision": decision, "loaded": len(good),
                        "quarantined": len(quarantined), "defects": len(defects), "every_defect_caught": caught_all, "right_decision": right_call})
report = pd.DataFrame(report_rows)
print(report.to_string(index=False))
report.to_csv(OUTDIR / "batch_report.csv", index=False)
U.check(report["every_defect_caught"].all() and report["right_decision"].all(), "every seeded defect caught and every batch decided right")
U.check(report.loc[report["batch"] == "batch_01", "loaded"].item() == 200, "the clean batch passes whole")

# %%
# Load what passed: the good rows of each loaded batch, appended as partitions of one dataset
LOADED = OUTDIR / "loaded_sessions"
for b, (decision, defects, good, quarantined) in results.items():
    if decision == "load" and good:
        table, _ = FLAT(good)
        ds.write_dataset(pa.Table.from_pandas(table, schema=S_SCHEMA, preserve_index=False), LOADED, format="parquet",
                         partitioning=["day"], partitioning_flavor="hive", basename_template=f"{b}-{{i}}.parquet",
                         existing_data_behavior="overwrite_or_ignore")
loaded_rows = ds.dataset(LOADED, format="parquet", partitioning="hive").count_rows()
print("rows loaded:", loaded_rows)
U.check(loaded_rows == int(report.loc[report["decision"] == "load", "loaded"].sum()), "only the rows of loaded batches reached the tables")

# %% [markdown]
# ## 6 · The quarantine file, as its owner reads it (5')
#
# Quarantined rows are not deleted: they go to the people who own them, with the reason, so they
# can correct the source. The loader does not edit them and does not release them; the station
# team corrects and sends them again, and a second person reviews the release. Write one file per
# batch and read it as a station owner would.

# %%
Q = OUTDIR / "quarantine"
Q.mkdir(exist_ok=True)
for b, (decision, defects, good, quarantined) in results.items():
    with open(Q / f"{b}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        if decision == "reject" and not quarantined:
            f.write(json.dumps({"batch": b, "decision": "reject", "reason": defects[0][1], "action": "the sender fixes the interface and sends the batch again"}) + "\n")
        for rec, rule in quarantined:
            f.write(json.dumps({"batch": b, "session_id": rec.get("session_id"), "station_id": rec.get("station", {}).get("id"),
                                "rule": rule, "meaning": "; ".join(U.RULES.get(r, r) for r in rule.split(",")), "record": rec}, ensure_ascii=False) + "\n")
for line in (Q / "batch_03.jsonl").read_text(encoding="utf-8").splitlines()[:3]:
    row = json.loads(line)
    print(row["session_id"], row["station_id"], "|", row["rule"], "|", row["meaning"])
U.check(sum(1 for _ in open(Q / "batch_05.jsonl", encoding="utf-8")) == 20, "the rejected batch's 20 rows are in its quarantine file with their reason")

# %% [markdown]
# ### Check yourself
#
# 1. Why is batch 4 rejected whole, when each record could be quarantined on its own?
#    <details><summary>Answer</summary>Every record lacks the same field: the sender changed the interface. Quarantining 200 rows would hide one fault behind 200 reports; rejecting names it once.</details>
# 2. Batch 5 has 20 bad rows of 200. Why reject rather than load 180?
#    <details><summary>Answer</summary>Above the 5% rule a batch is too broken to trust the rest: the same vendor fault may hide in rows that passed. The rule is the network's own choice; write it down so it is applied the same way every time.</details>
# 3. Why does `day` live in the folder name and not in the written files' schema?
#    <details><summary>Answer</summary>Hive partitioning stores the partition value in the path (`day=2026-10-21`); readers add it back as a column, and a query on one day opens only that folder.</details>
#
# **Carry forward.** The capstone script runs these checks on a batch the assessor generates.

# %% [markdown]
# ## ✱ Stretch · A version 2 that does not break version 1
#
# Copy the schema, add an optional `idle_min` field (an integer, not in `required`), and check
# that the five batches get the same decisions. Then make it required and see what happens to a
# version-1 sender. Data contracts, with versions and service levels, follow in DEV-DAT-204.
