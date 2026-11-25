# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi>=0.115", "httpx>=0.27", "tzdata>=2025.1"]
# ///
"""Write the synthetic data of the charging network into labs/data/. Fixed seeds: the same
bytes on every run. From labs/:

    uv run python prepare_data.py

What it writes, and which lab uses it:

  data/stations.csv                 the clean station register (UTF-8)            labs 1.2, 2.2
  data/platform_sessions.csv        the platform's own UTC times for 60 sessions  lab 1.2
  data/damaged/*                    six damaged files, byte-exact                 lab 1.2
  data/api/sessions.jsonl           1,200 nested sessions the mock API serves     lab 2.1
  data/api/arrivals.jsonl           20 sessions that arrive during paging         lab 2.1
  data/raw_api/page-*.json          a clean pull of the mock, one file per page   lab 2.2 (its start)
  data/batches/batch_0*.jsonl       five batches, four with seeded defects        lab 2.2
  data/reference/*.json             reference results for the safety nets, and fingerprints
                                    of the answers (the answers are in solutions/answer_key.md)

Every planted fault is listed in labs/solutions/answer_key.md with the lab that finds it.
"""
from __future__ import annotations

import csv
import io
import json
import random
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import chargekit as U
import mockapi

D = U.DATA
UTC = timezone.utc


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def csv_text(header, rows, delimiter=",", newline="\n") -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delimiter, lineterminator=newline)
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def z(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    st = U.stations()

    # ---------------------------------------------------------------- the clean register
    write_bytes(D / "stations.csv", csv_text(["station_id", "sector", "name_ar", "name_en", "connectors", "vendor"],
                                             [[s["station_id"], s["sector"], s["name_ar"], s["name_en"], s["connectors"], s["vendor"]] for s in st]).encode("utf-8"))

    # ---------------------------------------------------------------- six damaged files (lab 1.2)
    dmg = D / "damaged"
    if dmg.exists():
        shutil.rmtree(dmg)
    # F1: the legacy station register, exported by an old asset system in the Arabic Windows code page
    reg = csv_text(["station_id", "name_ar", "sector", "connectors"], [[s["station_id"], s["name_ar"], s["sector"], s["connectors"]] for s in st], newline="\r\n")
    write_bytes(dmg / "station_register_legacy.csv", reg.encode("cp1256"))
    # F2: the tariff table, saved as UTF-8 with a byte order mark
    tar = csv_text(["tariff_code", "per_kwh", "label_ar"], [["T1", "0.95", "تعرفة الليل"], ["T2", "1.15", "التعرفة العادية"], ["T3", "1.35", "تعرفة الذروة"]])
    write_bytes(dmg / "tariffs.csv", tar.encode("utf-8-sig"))
    # F3: station notes, UTF-8 that was once read as cp1256 and saved again as UTF-8 (double encoding)
    rng = random.Random(31)
    notes_rows = [[s["station_id"], rng.choice(U.NOTES_AR[1:]).replace(",", "") if i % 2 else "لا ملاحظات"] for i, s in enumerate(st[:12])]
    good = csv_text(["station_id", "note_ar"], notes_rows)
    write_bytes(dmg / "station_notes.csv", good.encode("utf-8").decode("cp1256").encode("utf-8"))
    # F4: the maintenance log, exported as tab-separated UTF-16 text
    work = ["تغيير كابل الشحن", "فحص دوري", "تحديث البرنامج الثابت", "تنظيف المنافذ"]
    mrows = [[s["station_id"], f"2026-10-{20 + i % 9:02d}", work[i % 4]] for i, s in enumerate(st[:16])]
    write_bytes(dmg / "maintenance_log.txt", csv_text(["station_id", "done_on", "work_ar"], mrows, delimiter="\t", newline="\r\n").encode("utf-16"))

    # F5 and F6: charger logs with times and no offset; the platform keeps the true UTC times
    plat = []
    rng = random.Random(56)
    a_rows = []
    vend_a = [s for s in st if s["vendor"] == "A"]
    for i in range(1, 31):
        s = vend_a[rng.randrange(len(vend_a))]
        start = datetime(2026, 10, 20, tzinfo=UTC) + timedelta(minutes=rng.randrange(0, 6 * 24 * 60))
        end = start + timedelta(minutes=rng.randint(12, 80))
        sid = f"CS-A{i:03d}"
        a_rows.append([sid, s["station_id"], start.astimezone(U.LOCAL).strftime("%Y-%m-%d %H:%M"), end.astimezone(U.LOCAL).strftime("%Y-%m-%d %H:%M")])
        plat.append([sid, s["station_id"], z(start), z(end)])
    write_bytes(dmg / "vendor_a_sessions.csv", csv_text(["session_id", "station_id", "started", "ended"], a_rows).encode("utf-8"))

    cet = ZoneInfo(U.VENDOR_B_ZONE)
    vend_b = [s for s in st if s["vendor"] == "B"]
    starts = []
    for _ in range(22):  # spread over the days around the change
        starts.append(datetime(2026, 10, 23, tzinfo=UTC) + timedelta(minutes=rng.randrange(0, 5 * 24 * 60)))
    # sessions inside the repeated hour: 02:00 to 03:00 local happens twice on 25 October 2026
    for m in (8, 22, 41, 52):
        starts.append(datetime(2026, 10, 25, 0, m, tzinfo=UTC))  # still summer time: 02:mm local, first pass
    for m in (6, 19, 35, 47):
        starts.append(datetime(2026, 10, 25, 1, m, tzinfo=UTC))  # winter time: 02:mm local, second pass
    starts.sort()
    b_rows = []
    for k, start in enumerate(starts, 1):
        s = vend_b[rng.randrange(len(vend_b))]
        dur = 25 if start == datetime(2026, 10, 25, 0, 52, tzinfo=UTC) else rng.randint(12, 55 if start.date() == datetime(2026, 10, 25).date() and start.hour < 2 else 70)  # one session crosses the change; the others in the repeated hour stay under an hour, so each end has one reading after its start
        end = start + timedelta(minutes=dur)
        sid = f"CS-B{k:03d}"
        loc = lambda t: t.astimezone(cet).strftime("%Y-%m-%d %H:%M")
        b_rows.append([k, sid, s["station_id"], loc(start), loc(end)])
        plat.append([sid, s["station_id"], z(start), z(end)])
    write_bytes(dmg / "vendor_b_sessions.csv", csv_text(["seq", "session_id", "station_id", "started", "ended"], b_rows).encode("utf-8"))
    write_bytes(D / "platform_sessions.csv", csv_text(["session_id", "station_id", "started_utc", "ended_utc"], plat).encode("utf-8"))

    # ---------------------------------------------------------------- the mock API's data (lab 2.1)
    api = D / "api"
    api.mkdir(parents=True, exist_ok=True)
    records = U.make_api_records(1200, seed=2103, first_id=1)
    U.write_jsonl(api / "sessions.jsonl", records)
    U.write_jsonl(api / "arrivals.jsonl", U.make_api_records(20, seed=2104, first_id=1201))

    # ---------------------------------------------------------------- a clean pull, kept raw (lab 2.2 starts here)
    raw = D / "raw_api"
    if raw.exists():
        shutil.rmtree(raw)
    raw.mkdir(parents=True)
    c = mockapi.client(faults={})
    cursor, page = None, 0
    while True:
        params = {"limit": 100} | ({"cursor": cursor} if cursor else {})
        r = c.get("/v1/sessions", params=params)
        page += 1
        body = r.json()
        doc = {"request": {"path": "/v1/sessions", "params": params}, "status": r.status_code, "body": body}
        (raw / f"page-{page:04d}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        cursor = body["next_cursor"]
        if not cursor:
            break

    # ---------------------------------------------------------------- five batches with seeded defects (lab 2.2)
    bdir = D / "batches"
    if bdir.exists():
        shutil.rmtree(bdir)
    bdir.mkdir(parents=True)
    key = {}

    def batch(k):
        return U.make_api_records(200, seed=3100 + k, first_id=k * 10000 + 1)

    # batch_01: clean
    b1 = batch(1)
    key["batch_01"] = {"decision": "load", "defects": []}
    # batch_02: three record-level defects
    b2 = batch(2)
    del b2[17]["energy_kwh"]
    b2[64]["energy_kwh"] = "12,5"
    b2[150]["started_at"] = b2[150]["started_at"][:19]
    key["batch_02"] = {"decision": "load", "defects": [[b2[17]["session_id"], "missing_field"], [b2[64]["session_id"], "wrong_type"], [b2[150]["session_id"], "no_offset"]]}
    # batch_03: table-level defects: a duplicated key, two out-of-range values, an end before its start, an unknown station
    b3 = batch(3)
    dup = json.loads(json.dumps(b3[40]))
    b3[120] = dup | {"amount": dup["amount"]}  # the same session delivered twice
    b3[77]["energy_kwh"] = -3.2
    b3[88]["energy_kwh"] = 912.0
    s99 = b3[99]
    s99["ended_at"], s99["started_at"] = s99["started_at"], s99["ended_at"]
    b3[133]["station"]["id"] = "ST47"
    key["batch_03"] = {"decision": "load", "defects": [[b3[40]["session_id"], "duplicate_key"], [b3[77]["session_id"], "out_of_range"], [b3[88]["session_id"], "out_of_range"], [s99["session_id"], "end_before_start"], [b3[133]["session_id"], "unknown_station"]]}
    # batch_04: a structural break: every record renames energy_kwh to energy
    b4 = batch(4)
    for r in b4:
        r["energy"] = r.pop("energy_kwh")
    key["batch_04"] = {"decision": "reject", "defects": [["*", "schema_break:energy_kwh"]]}
    # batch_05: a vendor sends local times without offsets for 20 sessions: 10% of the batch
    b5 = batch(5)
    rng = random.Random(55)
    bad = sorted(rng.sample(range(200), 20))
    for i in bad:
        b5[i]["started_at"] = b5[i]["started_at"][:19]
    key["batch_05"] = {"decision": "reject", "defects": [[b5[i]["session_id"], "no_offset"] for i in bad]}
    for name, rows in (("batch_01", b1), ("batch_02", b2), ("batch_03", b3), ("batch_04", b4), ("batch_05", b5)):
        U.write_jsonl(bdir / f"{name}.jsonl", rows)

    # ---------------------------------------------------------------- reference files
    ref = D / "reference"
    ref.mkdir(parents=True, exist_ok=True)

    def dump(name, obj):
        (ref / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")

    diagnosis = {"station_register_legacy.csv": "A", "tariffs.csv": "B", "station_notes.csv": "C", "maintenance_log.txt": "D", "vendor_a_sessions.csv": "E", "vendor_b_sessions.csv": "F"}
    dump("diagnosis_fingerprints", {f: U.digest([f"{f}:{code}"]) for f, code in diagnosis.items()})
    dump("batch_fingerprints", {b: {"decision": U.digest([f"{b}:{v['decision']}"]), "defects": U.digest([f"{sid}:{rule}" for sid, rule in v["defects"]]), "count": len(v["defects"])} for b, v in key.items()})
    (U.LABS / "solutions").mkdir(exist_ok=True)
    (U.LABS / "solutions" / "batch_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("stations:", len(st), "| platform sessions:", len(plat), "| api records:", len(records), "| raw pages:", page)
    print("batches:", {b: (v["decision"], len(v["defects"])) for b, v in key.items()})


if __name__ == "__main__":
    main()
