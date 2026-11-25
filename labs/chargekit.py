"""Shared helpers for the FND-DAT-103 labs (imported as U).

The case: the charging network, a fictional operator of public fast-charging stations in one
unnamed city. Every record is synthetic and generated with a fixed seed. Identifiers are
letter-prefixed codes (stations ST01 to ST40, sessions CS-..., accounts AC-K...); no file holds
a telephone, identity, account or card number.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import random
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Print Arabic and arrows safely when output goes to a file or a console on a legacy code page.
for _stream in (sys.stdout, sys.stderr):
    try:
        if (getattr(_stream, "encoding", "") or "").lower().replace("-", "") != "utf8":
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

LABS = Path(__file__).resolve().parent
DATA = LABS / "data"
OUT = Path(os.environ.get("FDT103_OUT", LABS / "out"))
QUICK = os.environ.get("FDT103_QUICK", "") not in ("", "0")

LOCAL = timezone(timedelta(hours=3), "+03:00")  # the network's local time: UTC+03:00, no daylight saving
VENDOR_B_ZONE = "CET"  # Vendor B chargers keep their factory zone, which has daylight saving

SECTORS = [("North", "الشمال"), ("South", "الجنوب"), ("East", "الشرق"), ("West", "الغرب"), ("Central", "الوسط")]
SITE_KINDS = [("car park", "موقف عام"), ("shopping centre", "مركز تجاري"), ("fuel station", "محطة وقود"), ("office building", "مبنى إداري")]
STATUSES = ["completed", "stopped_by_user", "fault"]


def pick(full, quick):
    """The full value normally, the small one when FDT103_QUICK=1."""
    return quick if QUICK else full


def check(cond: bool, what: str) -> None:
    """Print a passed check, or stop with what failed."""
    if not cond:
        raise AssertionError(f"check failed: {what}")
    print(f"PASS · {what}")


def out_dir(name: str) -> Path:
    p = OUT / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def reference(name: str):
    return json.loads((DATA / "reference" / f"{name}.json").read_text(encoding="utf-8"))


def load_jsonl(path) -> list[dict]:
    path = Path(path)
    if not path.is_absolute():
        path = DATA / path
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def digest(lines) -> str:
    """A short fingerprint of a set of answer lines, so a key can be checked without being shown."""
    text = "\n".join(sorted(lines))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def median_seconds(fn, repeat: int = 5) -> float:
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return round(statistics.median(times), 4)


class FakeClock:
    """Stands in for time.sleep: records every wait instead of waiting, so a lab that backs off
    for minutes runs in seconds. Pass `clock.sleep` wherever a client would call time.sleep."""

    def __init__(self):
        self.waits: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.waits.append(round(float(seconds), 3))

    @property
    def total(self) -> float:
        return round(sum(self.waits), 3)


# ---------------------------------------------------------------- the stations

def stations() -> list[dict]:
    """The 40 stations of the network, the same on every call."""
    rng = random.Random(103)
    rows = []
    for i in range(1, 41):
        sec_en, sec_ar = SECTORS[(i - 1) % 5]
        kind_en, kind_ar = SITE_KINDS[rng.randrange(len(SITE_KINDS))]
        rows.append({
            "station_id": f"ST{i:02d}",
            "sector": sec_en,
            "name_en": f"{sec_en} {kind_en} {i:02d}",
            "name_ar": f"{kind_ar} {sec_ar} {i:02d}",
            "connectors": rng.choice([2, 2, 4, 4, 6]),
            "vendor": "A" if i <= 28 else "B",
        })
    return rows


# ---------------------------------------------------------------- lab 1.1: one flat dataset

NOTES_AR = [
    'تأخر بدء الشحن، "الموصل 2" لا يستجيب',
    "توقف الشحن بطلب من المستخدم",
    "انقطاع قصير، أعيد التشغيل",
    'رسالة "خطأ في القابس"، تم الإبلاغ',
]


def make_sessions(n: int, seed: int = 103):
    """The flat sessions table used to compare formats in lab 1.1 (pandas DataFrame)."""
    import pandas as pd

    rng = random.Random(seed)
    st = stations()
    start0 = datetime(2026, 10, 19, 0, 0, tzinfo=LOCAL)
    rows = []
    for i in range(1, n + 1):
        s = st[rng.randrange(len(st))]
        start = start0 + timedelta(minutes=rng.randrange(0, 13 * 24 * 60))
        dur = rng.randint(8, 95)
        kwh = round(rng.uniform(4, 0.95 * dur), 3)
        status = rng.choices(STATUSES, weights=[86, 11, 3])[0]
        idle = rng.randint(0, 40) if rng.random() < 0.7 else None
        note = rng.choice(NOTES_AR) if rng.random() < 0.06 else None
        rows.append({
            "session_id": f"CS-{i:06d}",
            "station_id": s["station_id"],
            "connector": f"{rng.randint(1, s['connectors']):02d}",
            "started_at": start.astimezone(timezone.utc),
            "duration_min": dur,
            "energy_kwh": kwh,
            "amount": round(kwh * 1.15, 2),
            "account": f"AC-K{rng.randint(1, 4000):04d}",
            "status": status,
            "idle_min": idle,
            "note_ar": note,
        })
    df = pd.DataFrame(rows)
    df["started_at"] = pd.to_datetime(df["started_at"], utc=True).astype("datetime64[us, UTC]")
    df["idle_min"] = df["idle_min"].astype("Int64")
    df["status"] = df["status"].astype("category")
    return df


# ---------------------------------------------------------------- labs 2.1 and 2.2: nested records

def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def make_api_record(i: int, rng: random.Random, st: list[dict], start0: datetime) -> dict:
    s = st[rng.randrange(len(st))]
    start = start0 + timedelta(minutes=rng.randrange(0, 13 * 24 * 60), seconds=rng.choice([0, 15, 30, 45]))
    dur = rng.randint(10, 90)
    end = start + timedelta(minutes=dur)
    kwh = round(rng.uniform(5, 0.9 * dur), 3)
    n_read = rng.randint(2, 5)
    readings = []
    for k in range(1, n_read + 1):
        at = start + timedelta(minutes=round(dur * k / n_read))
        readings.append({"seq": k, "at": iso(at), "kwh": round(kwh * k / n_read, 3), "kw": round(rng.uniform(20, 120), 1)})
    tariff = rng.choice([("T1", 0.95), ("T2", 1.15), ("T3", 1.35)])
    return {
        "session_id": f"CS-{i:05d}",
        "station": {"id": s["station_id"], "sector": s["sector"], "connector": f"{rng.randint(1, s['connectors']):02d}"},
        "started_at": iso(start),
        "ended_at": iso(end),
        "energy_kwh": kwh,
        "tariff": {"code": tariff[0], "per_kwh": tariff[1]},
        "amount": round(kwh * tariff[1], 2),
        "account": f"AC-K{rng.randint(1, 4000):04d}",
        "status": rng.choices(STATUSES, weights=[86, 11, 3])[0],
        "readings": readings,
    }


def make_api_records(n: int = 1200, seed: int = 2103, first_id: int = 1) -> list[dict]:
    rng = random.Random(seed)
    st = stations()
    start0 = datetime(2026, 10, 19, 0, 0, tzinfo=LOCAL)
    return [make_api_record(i, rng, st, start0) for i in range(first_id, first_id + n)]


# ---------------------------------------------------------------- reference versions for the safety nets
# A lab cell calls one of these only when the exercise before it raised NotImplementedError, so
# that every later cell still runs. They are the plain answers; the solution notebooks hold the
# same code with comments.

def ref_write_three(df, folder: Path) -> dict:
    import pyarrow as pa
    import pyarrow.parquet as pq

    folder = Path(folder)
    paths = {"csv": folder / "sessions.csv", "jsonl": folder / "sessions.jsonl", "parquet": folder / "sessions.parquet"}
    df.to_csv(paths["csv"], index=False, encoding="utf-8")
    df.to_json(paths["jsonl"], orient="records", lines=True, date_format="iso", force_ascii=False)
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), paths["parquet"], compression="zstd")
    return paths


def ref_read_back(fmt: str, path):
    import pandas as pd

    if fmt == "csv":
        return pd.read_csv(path, encoding="utf-8")
    if fmt == "jsonl":
        return pd.read_json(path, lines=True)
    return pd.read_parquet(path)


def ref_fidelity(original, back) -> dict:
    out = {}
    for col in original.columns:
        same_type = col in back.columns and str(back[col].dtype) == str(original[col].dtype)
        try:
            same_values = col in back.columns and back[col].astype(original[col].dtype).equals(original[col])
        except Exception:
            same_values = False
        out[col] = bool(same_type and same_values)
    return out


# ---------------------------------------------------------------- lab 1.2 helpers

def peek(path, n: int = 40) -> None:
    """Print the first bytes of a file in hex, then what UTF-8 makes of them."""
    raw = Path(path).read_bytes()[:n]
    print(Path(path).name)
    print("  bytes:", raw.hex(" "))
    print("  as UTF-8:", repr(raw.decode("utf-8", errors="replace")))


def ref_read_text_file(path):
    import pandas as pd

    name = Path(path).name
    if name == "station_register_legacy.csv":
        return pd.read_csv(path, encoding="cp1256", dtype=str)
    if name == "tariffs.csv":
        return pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    if name == "station_notes.csv":
        text = Path(path).read_text(encoding="utf-8").encode("cp1256").decode("utf-8")
        return pd.read_csv(io.StringIO(text), dtype=str)
    if name == "maintenance_log.txt":
        return pd.read_csv(path, encoding="utf-16", sep="\t", dtype=str)
    raise ValueError(name)


def ref_to_utc_fixed(df):
    import pandas as pd

    out = df.copy()
    for col in ("started", "ended"):
        out[col] = pd.to_datetime(df[col]).dt.tz_localize(LOCAL).dt.tz_convert("UTC")
    return out


def ref_to_utc_dst(df):
    import pandas as pd
    from zoneinfo import ZoneInfo

    zone = ZoneInfo(VENDOR_B_ZONE)
    out = df.sort_values("seq", key=lambda s: s.astype(int)).copy()  # seq may arrive as text: sort as numbers
    starts, ends, last = [], [], None
    for _, r in out.iterrows():
        naive = datetime.fromisoformat(r["started"])
        s0 = naive.replace(tzinfo=zone, fold=0).astimezone(timezone.utc)  # first pass of a repeated hour
        s1 = naive.replace(tzinfo=zone, fold=1).astimezone(timezone.utc)  # second pass
        s = s0 if last is None or s0 >= last else s1  # times only move forward in seq order
        last = s
        e_naive = datetime.fromisoformat(r["ended"])
        cands = sorted({e_naive.replace(tzinfo=zone, fold=f).astimezone(timezone.utc) for f in (0, 1)})
        e = next(c for c in cands if c > s)
        starts.append(s)
        ends.append(e)
    out["started"] = pd.to_datetime(starts, utc=True)
    out["ended"] = pd.to_datetime(ends, utc=True)
    return out


# ---------------------------------------------------------------- lab 2.1 helpers

def load_token(name: str = "FDT103_API_TOKEN") -> str:
    """The API token from the environment, else from labs/.env, else the mock's example token from
    labs/.env.example (with a note). The token is never printed and never written to a file."""
    if os.environ.get(name):
        return os.environ[name]
    for fname in (".env", ".env.example"):
        p = LABS / fname
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith(name + "="):
                    if fname == ".env.example":
                        print(f"{name} is not set: using the mock's example token from .env.example")
                    return line.split("=", 1)[1].strip()
    raise RuntimeError(f"set {name} in the environment or in labs/.env")


def ref_get_with_retries(client, path, params, sleep, log, max_tries=6, seed=7):
    rng = random.Random(seed)
    for attempt in range(1, max_tries + 1):
        r = client.get(path, params=params)
        entry = {"path": path, "cursor": (params or {}).get("cursor"), "attempt": attempt, "status": r.status_code, "waited_s": 0.0}
        log.append(entry)
        if r.status_code == 200:
            return r
        if r.status_code == 429:
            wait = float(r.headers.get("Retry-After", "1"))
        elif r.status_code >= 500:
            wait = round(min(30.0, 0.5 * 2 ** (attempt - 1)) + rng.uniform(0, 0.25), 3)
        else:
            r.raise_for_status()
        entry["waited_s"] = wait
        sleep(wait)
    raise RuntimeError(f"gave up after {max_tries} tries: {path}")


class Interrupted(Exception):
    """Raised on purpose to simulate a run that stops half-way."""


def ref_fetch_all(client, folder, get_page, crash_after=None, limit=100):
    folder = Path(folder)
    raw = folder / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    ckpt_path, rec_path = folder / "checkpoint.json", folder / "records.jsonl"
    ckpt = json.loads(ckpt_path.read_text(encoding="utf-8")) if ckpt_path.exists() else {"next_cursor": None, "pages": 0, "done": False}
    seen = {json.loads(l)["session_id"] for l in rec_path.read_text(encoding="utf-8").splitlines()} if rec_path.exists() else set()
    stats = {"pages": 0, "new": 0, "dropped_duplicates": 0}
    while not ckpt["done"]:
        params = {"limit": limit} | ({"cursor": ckpt["next_cursor"]} if ckpt["next_cursor"] else {})
        r = get_page(client, params)
        body = r.json()
        n = ckpt["pages"] + 1
        (raw / f"page-{n:04d}.json").write_text(json.dumps({"request": {"path": "/v1/sessions", "params": params}, "status": r.status_code, "body": body}, ensure_ascii=False), encoding="utf-8")
        with open(rec_path, "a", encoding="utf-8", newline="\n") as f:
            for rec in body["data"]:
                if rec["session_id"] in seen:
                    stats["dropped_duplicates"] += 1
                    continue
                seen.add(rec["session_id"])
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                stats["new"] += 1
        stats["pages"] += 1
        if crash_after and stats["pages"] == crash_after:
            raise Interrupted(f"stopped after page {n}, before its checkpoint was written")
        ckpt = {"next_cursor": body["next_cursor"], "pages": n, "done": body["next_cursor"] is None}
        ckpt_path.write_text(json.dumps(ckpt), encoding="utf-8")
    return stats


# ---------------------------------------------------------------- lab 2.2: the declared schema and checks

RULES = {
    "missing_field": "a required field is absent",
    "wrong_type": "a field has the wrong JSON type",
    "no_offset": "a time has no UTC offset",
    "invalid": "another breach of the record schema",
    "duplicate_key": "the same session_id twice in the batch",
    "out_of_range": "energy_kwh outside 0 to 350",
    "end_before_start": "ended_at is not after started_at",
    "unknown_station": "station_id is not in the register",
}
MAX_QUARANTINE_SHARE = 0.05  # the network's own rule: above 5% of a batch, reject the whole batch
SCHEMA_BREAK_SHARE = 0.9     # a required field missing from 90% of records is a changed interface, not bad rows


def sessions_schema():
    import pyarrow as pa

    ts = pa.timestamp("us", tz="UTC")
    return pa.schema([
        pa.field("session_id", pa.string(), nullable=False),
        pa.field("station_id", pa.string(), nullable=False),
        pa.field("sector", pa.string(), nullable=False),
        pa.field("connector", pa.string(), nullable=False),
        pa.field("started_at", ts, nullable=False),
        pa.field("ended_at", ts, nullable=False),
        pa.field("energy_kwh", pa.float64(), nullable=False),
        pa.field("tariff_code", pa.string(), nullable=False),
        pa.field("per_kwh", pa.float64(), nullable=False),
        pa.field("amount", pa.float64(), nullable=False),
        pa.field("account", pa.string(), nullable=False),
        pa.field("status", pa.string(), nullable=False),
        pa.field("day", pa.string(), nullable=False),
    ])


def readings_schema():
    import pyarrow as pa

    return pa.schema([
        pa.field("session_id", pa.string(), nullable=False),
        pa.field("seq", pa.int16(), nullable=False),
        pa.field("at", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("kwh", pa.float64(), nullable=False),
        pa.field("kw", pa.float64(), nullable=False),
    ])


def record_validator():
    from jsonschema import Draft202012Validator

    schema = json.loads((LABS / "schema" / "session.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def ref_record_rule(validator, rec):
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


def ref_flatten(records):
    import pandas as pd

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


def ref_table_checks(register_ids):
    import pandera.pandas as pa

    return pa.DataFrameSchema(
        {
            "session_id": pa.Column(None, pa.Check(lambda s: ~s.duplicated(keep=False), name="duplicate_key")),
            "station_id": pa.Column(None, pa.Check(lambda s: s.isin(set(register_ids)), name="unknown_station")),
            "energy_kwh": pa.Column(None, pa.Check(lambda s: s.between(0, 350), name="out_of_range")),
        },
        checks=[pa.Check(lambda df: df["ended_at"] > df["started_at"], name="end_before_start")],
    )


def ref_validate_batch(records, validator, table_checks):
    """Returns (decision, defects, good_records, quarantined): defects are (session_id, rule) pairs."""
    import pandera.errors as pe

    n = len(records)
    required = validator.schema["required"]
    for field in required:
        missing = sum(field not in r for r in records)
        if n and missing / n >= SCHEMA_BREAK_SHARE:
            return "reject", [("*", f"schema_break:{field}")], [], []
    defects, good, quarantined = [], [], []
    for rec in records:
        rule = ref_record_rule(validator, rec)
        if rule:
            defects.append((rec.get("session_id", "?"), rule))
            quarantined.append((rec, rule))
        else:
            good.append(rec)
    if good:
        sessions, _ = ref_flatten(good)
        try:
            table_checks.validate(sessions, lazy=True)
        except pe.SchemaErrors as err:
            fc = err.failure_cases
            bad_rows = {}
            for _, row in fc.iterrows():
                if row["index"] is None or str(row["index"]) == "nan":
                    continue
                bad_rows.setdefault(int(row["index"]), set()).add(str(row["check"]))
            keep = []
            for i, rec in enumerate(good):
                if i in bad_rows:
                    for rule in sorted(bad_rows[i]):
                        defects.append((rec["session_id"], rule))
                    quarantined.append((rec, ",".join(sorted(bad_rows[i]))))
                else:
                    keep.append(rec)
            good = keep
    share = len(quarantined) / n if n else 0
    decision = "reject" if share > MAX_QUARANTINE_SHARE else "load"
    return decision, sorted(set(defects)), (good if decision == "load" else []), quarantined
