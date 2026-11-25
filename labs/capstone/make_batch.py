# /// script
# requires-python = ">=3.11"
# dependencies = ["tzdata>=2025.1"]
# ///
"""Write one capstone batch of the charging network, and its key, from a seed.

The assessor runs it on the day with a seed of their own choice, gives the participant the batch
folder and keeps the key. From labs/:

    uv run python capstone/make_batch.py --seed 1 --label P --out capstone/practice --key capstone/practice_key.json

The seed is the assessor's secret: the scenario, the encoding and the ids are all drawn from it at
random, so nothing in the batch reveals it. Hand the batch over by its letter (--label), not by
the seed. Use a large seed of your own (eight digits or more, never 1 to 100): participants hold this
script and could generate small seeds in advance and match the files. Every kind of batch comes up across a few seeds; read the scenario in each key and draw
another seed if the group lacks one.

The batch folder holds three files:

  stations.csv              the station register; its encoding is drawn at random (UTF-8 with a
                            byte order mark, or the legacy Arabic code page cp1256)
  sessions.jsonl            nested session records as the platform API returns them; how many and
                            which defects are drawn at random (none, a few, a changed field,
                            or too many)
  vendor_b_sessions.csv     a charger log with local CET times and no offset, around a clock
                            change in most batches

The key holds the expected decision for sessions.jsonl, every seeded defect, the register's
encoding and the expected UTC times of the vendor log.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chargekit as U  # noqa: E402

UTC = timezone.utc
SCENARIOS = ["clean", "few_defects", "schema_break", "too_many"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--label", default="A", help="the letter the batch is handed over by")
    ap.add_argument("--out", required=True)
    ap.add_argument("--key", required=True, help="where to write the key; keep it away from the participant")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    scenario = rng.choice(SCENARIOS)
    enc = rng.choice(["cp1256", "utf-8-sig"])
    around_change = rng.random() < 2 / 3
    id_block = rng.randrange(30)
    vendor_tag = rng.randrange(10, 100)
    key: dict = {"label": a.label, "seed": a.seed, "scenario": scenario}

    # the register, in one of two encodings
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n" if enc == "cp1256" else "\n")
    w.writerow(["station_id", "name_ar", "sector", "connectors"])
    for s in U.stations():
        w.writerow([s["station_id"], s["name_ar"], s["sector"], s["connectors"]])
    (out / "stations.csv").write_bytes(buf.getvalue().encode(enc))
    key["register_encoding"] = enc

    # the sessions, with defects by scenario
    n = 300
    recs = U.make_api_records(n, seed=9000 + a.seed, first_id=60001 + id_block * 1000)
    defects: list[list[str]] = []
    idx = rng.sample(range(n), 40)
    if scenario == "few_defects":
        r = recs[idx[0]]; del r["amount"]; defects.append([r["session_id"], "missing_field"])
        r = recs[idx[1]]; r["energy_kwh"] = -1.5; defects.append([r["session_id"], "out_of_range"])
        r = recs[idx[2]]; r["station"]["id"] = "ST5" + str(rng.randint(1, 9)); defects.append([r["session_id"], "unknown_station"])
        r = recs[idx[3]]; r["ended_at"] = r["ended_at"][:19]; defects.append([r["session_id"], "no_offset"])
        decision = "load"
    elif scenario == "schema_break":
        for r in recs:
            r["started"] = r.pop("started_at")
        defects.append(["*", "schema_break:started_at"])
        decision = "reject"
    elif scenario == "too_many":
        for i in idx[:24]:  # 8% of the batch
            recs[i]["energy_kwh"] = str(recs[i]["energy_kwh"]).replace(".", ",")
            defects.append([recs[i]["session_id"], "wrong_type"])
        decision = "reject"
    else:
        decision = "load"
    U.write_jsonl(out / "sessions.jsonl", recs)
    key["sessions"] = {"records": n, "decision": decision, "defects": sorted(defects)}

    # the vendor log: local CET times, no offset, seq in start order
    cet = ZoneInfo(U.VENDOR_B_ZONE)
    base = datetime(2026, 10, 24, 12, tzinfo=UTC) if around_change else datetime(2026, 11, 3, 6, tzinfo=UTC)
    starts = sorted(base + timedelta(minutes=rng.randrange(0, 30 * 60)) for _ in range(24))
    if around_change:
        starts = sorted(starts[:20] + [datetime(2026, 10, 25, 0, 20, tzinfo=UTC), datetime(2026, 10, 25, 1, 10, tzinfo=UTC),
                                       datetime(2026, 10, 25, 0, 45, tzinfo=UTC), datetime(2026, 10, 25, 1, 35, tzinfo=UTC)])
    rows, expected = [], {}
    for k, st in enumerate(starts, 1):
        en = st + timedelta(minutes=rng.randint(10, 50))
        sid = f"CS-V{vendor_tag:02d}{k:02d}"
        rows.append([k, sid, f"ST{rng.randint(29, 40)}", st.astimezone(cet).strftime("%Y-%m-%d %H:%M"), en.astimezone(cet).strftime("%Y-%m-%d %H:%M")])
        expected[sid] = [st.strftime("%Y-%m-%dT%H:%M:%SZ"), en.strftime("%Y-%m-%dT%H:%M:%SZ")]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["seq", "session_id", "station_id", "started", "ended"])
    w.writerows(rows)
    (out / "vendor_b_sessions.csv").write_text(buf.getvalue(), encoding="utf-8", newline="")
    key["vendor_b"] = {"rows": len(rows), "crosses_clock_change": around_change, "utc": expected}

    Path(a.key).write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"batch {a.label} written to {out.name}/ (scenario kept in the key)")


if __name__ == "__main__":
    main()
