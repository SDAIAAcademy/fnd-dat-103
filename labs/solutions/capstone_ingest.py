# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "pyarrow>=17", "pandera>=0.22", "jsonschema>=4.23", "tzdata>=2025.1"]
# ///
"""A reference capstone script, for the trainer: one way to meet the brief, not the only one.

    uv run python solutions/capstone_ingest.py <batch folder> <output folder> [--key <key file>]

It reads the three files of a batch, normalises encodings and times, validates the sessions,
writes typed Parquet partitioned by day (or nothing, when the batch is rejected), a quarantine
file and a report. Run twice on the same batch, it writes the same files: the output folder is
rebuilt from the batch each time. With --key it compares its result with the assessor's key.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LABS))

import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.dataset as ds  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

import chargekit as U  # noqa: E402


def read_register(path: Path):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        enc = "utf-8-sig"
    else:
        try:
            raw.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            enc = "cp1256"  # the network's legacy exports; confirmed below by the Arabic it must contain
    df = pd.read_csv(path, encoding=enc, dtype=str)
    if not df["name_ar"].str.contains("[؀-ۿ]", regex=True).all():
        raise ValueError(f"register decoded as {enc} holds no Arabic: stop and ask the station team")
    return df, enc


def main() -> int:
    batch, out = Path(sys.argv[1]), Path(sys.argv[2])
    key = json.loads(Path(sys.argv[sys.argv.index("--key") + 1]).read_text(encoding="utf-8")) if "--key" in sys.argv else None
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    log = []

    register, enc = read_register(batch / "stations.csv")
    log.append(f"stations.csv: decoded as {enc}, {len(register)} stations")

    vend = pd.read_csv(batch / "vendor_b_sessions.csv", dtype=str)
    vend_utc = U.ref_to_utc_dst(vend)
    log.append(f"vendor_b_sessions.csv: {len(vend_utc)} sessions localised to {U.VENDOR_B_ZONE}, converted to UTC")
    vend_utc.to_csv(out / "vendor_b_sessions.utc.csv", index=False)

    records = U.load_jsonl((batch / "sessions.jsonl").resolve())
    validator = U.record_validator()
    checks = U.ref_table_checks(register["station_id"].tolist())
    decision, defects, good, quarantined = U.ref_validate_batch(records, validator, checks)
    if decision == "load" and good:
        table, readings = U.ref_flatten(good)
        ds.write_dataset(pa.Table.from_pandas(table, schema=U.sessions_schema(), preserve_index=False), out / "sessions",
                         format="parquet", partitioning=["day"], partitioning_flavor="hive", existing_data_behavior="delete_matching")
        pq.write_table(pa.Table.from_pandas(readings, schema=U.readings_schema(), preserve_index=False), out / "readings.parquet")
    with open(out / "quarantine.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for rec, rule in quarantined:
            f.write(json.dumps({"session_id": rec.get("session_id"), "rule": rule, "record": rec}, ensure_ascii=False) + "\n")
    report = {"sessions": {"records": len(records), "decision": decision, "loaded": len(good), "quarantined": len(quarantined),
                           "defects": [list(d) for d in defects]}, "log": log}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report["sessions"].items() if k != "defects"}), "|", len(defects), "defects")
    for line in log:
        print(" ", line)
    if key:
        same_decision = key["sessions"]["decision"] == decision
        same_defects = sorted(key["sessions"]["defects"]) == sorted([list(d) for d in defects])
        mine = {r.session_id: [r.started.strftime("%Y-%m-%dT%H:%M:%SZ"), r.ended.strftime("%Y-%m-%dT%H:%M:%SZ")] for r in vend_utc.itertuples()}
        same_times = mine == key["vendor_b"]["utc"]
        same_enc = key["register_encoding"] == enc or (key["register_encoding"] == "utf-8-sig" and enc == "utf-8-sig")
        print(f"against the key: decision {same_decision}, defects {same_defects}, vendor times {same_times}, encoding {same_enc}")
        return 0 if (same_decision and same_defects and same_times and same_enc) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
