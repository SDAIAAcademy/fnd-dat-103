# Capstone: a checked ingestion script

**The task.** Write one script, `ingest.py`, that takes a batch folder of the charging network and
an output folder, and moves the batch into typed tables without losing or corrupting anything,
or refuses it for a stated reason. On the capstone day you run it live on a batch the assessor
generates in front of you, and explain what it did.

A batch folder holds three files, as in `practice/`:

| File | What can be wrong with it |
|---|---|
| `stations.csv` | The register: UTF-8 with a byte order mark, or the legacy Arabic code page (cp1256) |
| `sessions.jsonl` | Nested session records as the platform API returns them: none, a few, or many defects, or a changed field |
| `vendor_b_sessions.csv` | Local CET times without an offset, sometimes across the autumn clock change |

**What the script must do**

1. Read the register in its real encoding, and prove it (the Arabic names must read as Arabic).
2. Convert the vendor log to UTC, the repeated hour included.
3. Check each session record against `../schema/session.schema.json` and the table rules of lab 2.2,
   and decide with the network's rules: reject on a changed interface; quarantine bad rows; reject
   the batch when more than 5% is quarantined; otherwise load.
4. Write the loaded sessions as Parquet partitioned by day, with the declared schema
   (`chargekit.sessions_schema()`), the readings beside them, a quarantine file with a reason
   per row, and `report.json` with the decision, the counts, every defect and a log of each repair.
5. Rerun cleanly: a second run on the same batch gives the same files.

**What you hand in.** A public GitHub repository link, within two weeks of the workshop (the
tracked follow-up task): the script, the declared schemas, a README that states your rules and
how to run the script, and the report of a run on the practice batch. No token, key or `.env`
file in the repository.

**Practice.** `practice/` is the batch of seed 1 and `practice_key.json` its key. Generate more
with `uv run python capstone/make_batch.py --seed <n> --out <folder> --key <file>` (from `labs/`)
and check your script against their keys. On the day the assessor picks a seed you have not seen
and keeps its key.

**AI policy: AI-full.** Use any assistant to write and test the script. In the live run you
explain every decision it makes; "the assistant wrote it" is not an explanation.
