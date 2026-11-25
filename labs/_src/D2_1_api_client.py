# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "fastapi>=0.115"]
# ///
# %% [markdown]
# # Lab 2.1 · Every record, exactly once
#
# Day 2 · Session 1 (Interfaces) · 100 min.
#
# The charging network's operations analyst needs every charging session from the charge-point
# platform's API, and the API misbehaves: it limits the rate, fails now and then, and a run can
# stop half-way. You read the API's terms, write a client that follows the cursor, retries the
# right errors with backoff, keeps every raw response and a checkpoint, resume it after an
# interruption, and prove from the run log that every record arrived exactly once. Then you see
# why offset paging loses and repeats records, and pull a public open-data API after reading its
# licence.
#
# **AI policy: AI-tutor.** An assistant may explain status codes or an error; write the client yourself.
#
# **Reference state.** The mock API runs inside this notebook (`mockapi.py`, a FastAPI app with a
# fixed fault schedule) on `data/api/`; no server, port or earlier lab is needed. The token comes
# from the environment or `labs/.env` (copy `.env.example`). The last task needs the internet;
# without it, it says so and the rest of the lab stands. Outputs go to `out/lab2_1/`.
#
# **Tasks**
# - [ ] 1 · Read the API’s terms; load the token from the environment (10')
# - [ ] 2 · Fetch one page by hand (10')
# - [ ] 3 · Write fetch_all: cursor, raw pages, checkpoint (25')
# - [ ] 4 · Add retries for 429 and 5xx; stop on other errors (20')
# - [ ] 5 · Interrupt, resume, prove exactly once (10')
# - [ ] 6 · Find what offset paging repeats and misses (10')
# - [ ] 7 · Read a public API’s licence, then pull every page politely (15')
# - [ ] ✱ Stretch · Make the public pull resumable

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
import random
import shutil

import chargekit as U
import mockapi

OUTDIR = U.out_dir("lab2_1")
shutil.rmtree(OUTDIR)  # every run of this lab starts clean
OUTDIR.mkdir(parents=True)
EXPECTED = len(U.load_jsonl("api/sessions.jsonl"))  # what the platform holds: the trainer's truth
print("sessions on the platform:", EXPECTED)

# %% [markdown]
# ## 1 · Terms first, and a token that stays out of the code (10')
#
# Before the first pull, read what the API allows. Then load the token from the environment: a
# token pasted into a notebook ends up in its history, its outputs and every copy of it.

# %%
TOKEN = U.load_token()
api = mockapi.client(token=TOKEN, faults={})
terms = api.get("/v1/terms").json()
for k, v in terms.items():
    print(f"{k:>10}: {v}")
U.check("60 requests per minute" in terms["rate_limit"], "the rate limit is read before pulling")
U.check(mockapi.client(token="wrong", faults={}).get("/v1/terms").status_code == 401, "a wrong token gets 401, not data")

# %% [markdown]
# ## 2 · One page by hand (10')
#
# Ask for the first page of 100 sessions. Look at the status, the number of records, the first
# record (it is nested: `station`, `tariff` and a list of `readings`) and `next_cursor`, an opaque
# string you hand back to get the next page.

# %%
r = api.get("/v1/sessions", params={"limit": 100})
page = r.json()
print("status", r.status_code, "| records", len(page["data"]), "| next_cursor", page["next_cursor"])
print(json.dumps(page["data"][0], ensure_ascii=False, indent=1)[:600])
U.check(r.status_code == 200 and len(page["data"]) == 100 and page["next_cursor"], "a full first page with a cursor")

# %% [markdown]
# ## 3 · `fetch_all`: cursor, raw pages, checkpoint (25')
#
# ✏️ **Exercise** · Write `fetch_all(client, folder, get_page, crash_after=None)`:
#
# - read `folder/checkpoint.json` if it exists (`next_cursor`, `pages`, `done`), and the ids
#   already in `folder/records.jsonl`;
# - until done: build the params (`limit` 100, and `cursor` when there is one), call
#   `get_page(client, params)`, save the raw response as `folder/raw/page-NNNN.json` (the request's
#   path and params, the status, the body; never the headers, which hold the token);
# - append each record whose `session_id` is new to `records.jsonl`; count the ones dropped as
#   duplicates;
# - if `crash_after` equals the number of pages fetched in this run, raise `U.Interrupted` now:
#   the records are written but the checkpoint is not (the worst moment to stop);
# - write the checkpoint;
# - return `{"pages": ..., "new": ..., "dropped_duplicates": ...}` for this run.

# %%
def fetch_all(client, folder, get_page, crash_after=None, limit=100):
    # BEGIN SOLUTION
    folder = Path(folder)
    raw = folder / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    ckpt_path, rec_path = folder / "checkpoint.json", folder / "records.jsonl"
    if ckpt_path.exists():
        ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
    else:
        ckpt = {"next_cursor": None, "pages": 0, "done": False}
    seen = set()
    if rec_path.exists():
        seen = {json.loads(line)["session_id"] for line in rec_path.read_text(encoding="utf-8").splitlines()}
    stats = {"pages": 0, "new": 0, "dropped_duplicates": 0}
    while not ckpt["done"]:
        params = {"limit": limit}
        if ckpt["next_cursor"]:
            params["cursor"] = ckpt["next_cursor"]
        r = get_page(client, params)
        body = r.json()
        n = ckpt["pages"] + 1
        doc = {"request": {"path": "/v1/sessions", "params": params}, "status": r.status_code, "body": body}
        (raw / f"page-{n:04d}.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
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
            raise U.Interrupted(f"stopped after page {n}, before its checkpoint was written")
        ckpt = {"next_cursor": body["next_cursor"], "pages": n, "done": body["next_cursor"] is None}
        ckpt_path.write_text(json.dumps(ckpt), encoding="utf-8")
    return stats
    # END SOLUTION

# %%
# Check on a well-behaved mock first, with a plain get and no retries
plain = lambda c, params: c.get("/v1/sessions", params=params)
try:
    stats = fetch_all(mockapi.client(token=TOKEN, faults={}), OUTDIR / "clean_run", plain)
    FETCH = fetch_all
except NotImplementedError:
    stats = U.ref_fetch_all(mockapi.client(token=TOKEN, faults={}), OUTDIR / "clean_run", plain)
    FETCH = U.ref_fetch_all
print(stats)
U.check(stats["new"] == EXPECTED and stats["pages"] == 12, f"all {EXPECTED} sessions in 12 pages from a well-behaved API")

# %% [markdown]
# **Look at** what the same plain client does against the real schedule of faults: the third
# request answers 429.

# %%
try:
    FETCH(mockapi.client(token=TOKEN), OUTDIR / "naive_run", plain)
except Exception as e:
    print("the plain client stopped:", type(e).__name__, str(e)[:120])
print("records it kept:", sum(1 for _ in open(OUTDIR / "naive_run" / "records.jsonl", encoding="utf-8")))

# %% [markdown]
# ## 4 · Retries that respect the server (20')
#
# ✏️ **Exercise** · Write `get_with_retries(client, path, params, sleep, log, max_tries=6)`:
#
# - 200: return the response;
# - 429: wait the seconds in `Retry-After`, then try again;
# - 500 to 599: wait `0.5 × 2^(attempt−1)` seconds, at most 30, plus a random jitter of up to
#   0.25 s, then try again;
# - any other status: raise (`r.raise_for_status()`): a 401 or a 404 will not get better;
# - append one dict per attempt to `log`: path, cursor, attempt, status, seconds waited;
# - call `sleep(seconds)` to wait, never `time.sleep` directly: the lab passes a fake clock that
#   records the waits instead of waiting.

# %%
def get_with_retries(client, path, params, sleep, log, max_tries=6, seed=7):
    # BEGIN SOLUTION
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
    # END SOLUTION

# %%
try:
    get_with_retries(mockapi.client(token=TOKEN, faults={}), "/v1/terms", {}, U.FakeClock().sleep, [])
    GET = get_with_retries
except NotImplementedError:
    GET = U.ref_get_with_retries
clock, run_log = U.FakeClock(), []
retrying = lambda c, params: GET(c, "/v1/sessions", params, clock.sleep, run_log)
stats = FETCH(mockapi.client(token=TOKEN), OUTDIR / "faulty_run", retrying)
statuses = [e["status"] for e in run_log]
print(stats, "| requests", len(run_log), "| statuses", sorted(set(statuses)), "| waited", clock.total, "s (on the fake clock)")
U.check(stats["new"] == EXPECTED and {429, 500, 503} <= set(statuses), "every session through 429, 500 and 503 answers")
try:
    GET(mockapi.client(token="wrong", faults={}), "/v1/sessions", {"limit": 100}, clock.sleep, [])
    stopped = False
except Exception:
    stopped = True
U.check(stopped, "a 401 is raised at once, not retried")

# %% [markdown]
# ## 5 · Interrupt, resume, and prove exactly once (10')
#
# Run against the faulty mock again, stopping after page 7 at the worst moment: its records are
# written, its checkpoint is not. Then run again from the same folder. The rerun fetches page 7 a
# second time; the ids already kept stop its records from being written twice. Write the run log
# and its summary: that is the evidence of the outcome.

# %%
RUN = OUTDIR / "resumed_run"
clock, run_log = U.FakeClock(), []
api_faulty = mockapi.client(token=TOKEN)
try:
    FETCH(api_faulty, RUN, retrying, crash_after=7)
except U.Interrupted as e:
    print("first run:", e)
second = FETCH(api_faulty, RUN, retrying)
ids = [json.loads(line)["session_id"] for line in open(RUN / "records.jsonl", encoding="utf-8")]
truth = {r["session_id"] for r in U.load_jsonl("api/sessions.jsonl")}
summary = {"records": len(ids), "unique": len(set(ids)), "expected": EXPECTED, "missing": len(truth - set(ids)),
           "dropped_on_resume": second["dropped_duplicates"], "requests": len(run_log), "waited_s": clock.total}
with open(RUN / "run_log.jsonl", "w", encoding="utf-8", newline="\n") as f:
    for e in run_log:
        f.write(json.dumps(e) + "\n")
    f.write(json.dumps({"summary": summary}) + "\n")
print(summary)
U.check(summary["records"] == summary["unique"] == EXPECTED and summary["missing"] == 0, "every record retrieved exactly once, across an interruption")
U.check(summary["dropped_on_resume"] == 100, "the page fetched twice added nothing")
U.check(not any("Authorization" in p.read_text(encoding="utf-8") or TOKEN in p.read_text(encoding="utf-8") for p in RUN.rglob("*.json*")), "no raw page, record or log line holds the token")

# %% [markdown]
# ## 6 · Offset paging under live inserts (10')
#
# The platform also offers `/v1/sessions-by-offset?offset=&limit=`. Page through it to the end.
# While you page, 20 new sessions arrive at the top of the list (the mock adds them before the
# third page). Count the ids you received twice, and the new sessions you never saw.

# %%
api_offset = mockapi.client(token=TOKEN, faults={})
got, offset, total = [], 0, None
while total is None or offset < total:
    body = api_offset.get("/v1/sessions-by-offset", params={"limit": 100, "offset": offset}).json()
    total = body["total"]
    got += [r["session_id"] for r in body["data"]]
    offset += 100
arrived = {r["session_id"] for r in U.load_jsonl("api/arrivals.jsonl")}
repeated = len(got) - len(set(got))
missed = len(arrived - set(got))
print(f"received {len(got)} ids: {repeated} repeated; of the {len(arrived)} new sessions, {missed} never seen")
U.check(repeated == 20 and missed == 20, "offset paging repeated 20 ids and missed the 20 that arrived")

# %% [markdown]
# ## 7 · A public open-data API, politely (15')
#
# Public bodies publish open data in machine-readable formats with a licence (the Open Data
# Policy's principles 2 and 7). Here the example is the World Bank Indicators API: no key, page
# numbers (`page`, `per_page`), and a licence recorded for each series. Before pulling, read the
# series' licence from its metadata and stop if it is not an open licence you can use. The API
# publishes no rate limit, so the course sets its own rule: one request a second, and a short
# timeout. Nothing from this pull is saved into the course.

# %%
import time
import httpx

BASE = "https://api.worldbank.org/v2"
SERIES = "EG.ELC.ACCS.ZS"  # access to electricity, % of population
try:
    with httpx.Client(timeout=30) as web:
        meta = web.get(f"{BASE}/sources/2/series/{SERIES}/metadata", params={"format": "json"}).json()
        fields = {v["id"]: v["value"] for v in meta["source"][0]["concept"][0]["variable"][0]["metatype"]}
        licence = fields.get("License_Type")
        print("licence of the series:", licence, "|", fields.get("License_URL"))
        U.check(licence == "CC BY-4.0", "the series is under CC BY 4.0: attribute the source when you reuse it")
        rows, page, pages, total = [], 1, None, None
        while pages is None or page <= pages:
            head, data = web.get(f"{BASE}/country/all/indicator/{SERIES}", params={"date": "2023", "format": "json", "per_page": 50, "page": page}).json()
            pages, total = int(head["pages"]), int(head["total"])
            rows += data or []
            page += 1
            time.sleep(1)  # the course's own pacing rule
    keys = {(r["country"]["id"], r["date"]) for r in rows}
    print(f"{len(rows)} rows in {pages} pages; the API reports {total}; with a value: {sum(r['value'] is not None for r in rows)}")
    U.check(len(rows) == total == len(keys), "every row of the public series pulled once, by the API's own count")
except (httpx.HTTPError, OSError, ValueError, KeyError) as e:
    print("The public API did not answer here:", type(e).__name__, "| tasks 1 to 6 stand; try this cell again later.")

# %% [markdown]
# ### Check yourself
#
# 1. Why retry a 503 but not a 401?
#    <details><summary>Answer</summary>A 503 says the server is briefly unable; the same request can succeed later. A 401 says the request itself is not allowed: repeating it only adds load and may lock the token.</details>
# 2. The run stopped after writing page 7's records but before its checkpoint. What saved you from duplicates?
#    <details><summary>Answer</summary>The write is keyed by `session_id`: records already kept are skipped, so fetching a page twice changes nothing (an idempotent load).</details>
# 3. Why did the cursor endpoint not repeat records when new sessions arrived?
#    <details><summary>Answer</summary>The cursor names the last record seen, not a position: new records at the top do not shift what comes after it. They are picked up by the next run.</details>
#
# **Carry forward.** Lab 2.2 starts from the raw pages of a clean pull, supplied in `data/raw_api/`.

# %% [markdown]
# ## ✱ Stretch · A resumable public pull
#
# Give the public pull a checkpoint file (the last page done) and a folder of raw pages, so a
# second run after an interruption fetches only what is missing. Keep the one-request-a-second rule.
