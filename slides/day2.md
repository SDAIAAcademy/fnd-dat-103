---
course: "Data Formats, Interfaces and Quality Checks"
code: "FND-DAT-103"
version: "2027.1.0"
deck: "day2"
day: 2
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/fnd-dat-103/slides/day2.html"
---

# Data Formats, Interfaces and Quality Checks

## Day 2: Interfaces and the boundary

Pull every record exactly once, then let only a valid batch through

#### [day2#title] Interfaces and the boundary

*SDAIA Academy · Data Formats, Interfaces and Quality Checks*

Day 2: Pull every record exactly once, then let only a valid batch through

Data & AI Foundations Track · 2 teaching days + capstone day · 2 sessions · 2 labs · FND-DAT-103

#### [day2#agenda] Interfaces and the boundary

*Today*

- **Session 1 · Interfaces**: Status codes and errors, offset and cursor pagination, rate limits, retries with backoff, raw responses, checkpoints and tokens kept out of code
- **Session 2 · Schema and validation**: Nested JSON flattened to typed tables, declared types, ranges and keys, partitioned Parquet, and failing a load versus quarantining rows

#### [day2#review-day1] Which fault is this?

*Review of Day 1*

**Question:** A water utility's meter readings, logged without offsets, run exactly 240 minutes ahead of the billing system's UTC times on every day of the year. What is the fault?

- A. A clock in a zone that has daylight saving time
- B. A file saved in a legacy code page
- C. A CSV that lost the column's type
- D. A clock on a fixed offset, read as UTC

### Session 1: Interfaces

#### [day2#s1] Interfaces

*Session 1*

- Decide from a status code whether to retry, wait or stop
- Explain why cursor pagination survives inserts that offset pagination does not
- Build a rerunnable pull with raw responses, a checkpoint and idempotent writes

#### [day2#http-in-one] A request names what you want; the status says what happened

*HTTP in one slide*

- request: `GET /v1/stations?limit=50&cursor=Yz0x` with `Authorization: Bearer ...`
- status: `200 OK`
- headers: `Content-Type: application/json`
- body: `{"data": [...50 items...], "next_cursor": "Yz01MA"}`

Read the status before the body: a 429 or a 500 may carry an HTML page, not your JSON.

#### [day2#status-codes] Each status asks the client for a different action

*Status codes*

| Status | Means | The client |
| --- | --- | --- |
| `200` | Here is the data | Uses it |
| `400` `401` `403` `404` | The request is wrong or not allowed | Stops and reports: repeating will not help |
| `429` | Too many requests | Waits as long as `Retry-After` says, then repeats |
| `500` `502` `503` `504` | The server failed, often briefly | Waits longer each time, then repeats; gives up after a few tries |

#### [day2#offset-vs-cursor] An offset is a position; a cursor is a bookmark

*Pagination*

- **Offset: "skip 100, give me 100".** Newest first, five new items arrive after page 1. Every older item moves down five places, so page 2 starts with five items you already have, and the five new ones are never seen in this pull.
- **Cursor: "after the last one I saw".** The server returns an opaque token naming the last item. New items at the top do not move what comes after it; the next run picks them up.

> **What goes wrong.** Offset paging fails silently: no error, just repeats and gaps that a count by id would reveal.

#### [day2#backoff] Back off exponentially, add jitter, and stop after a few tries

*Retries*

| Item | Value |
| --- | --- |
| Try 1 | 0.5 s |
| Try 2 | 1 s |
| Try 3 | 2 s |
| Try 4 | 4 s |
| Try 5 | 8 s |

- **Wait** = base × 2try − 1, capped, plus a small random jitter.
- Jitter spreads clients that failed together, so they do not return together.
- A 429 with `Retry-After` overrides the formula.

#### [day2#keep-raw] Keep every raw response before you parse it

*Raw responses*

- **Replay.** Fix a parsing bug and rerun from the saved pages, without calling the API again.
- **Audit.** Show what the source said on the day, not what your code made of it.
- **Debug.** An odd value downstream can be traced to the page it came from.

> **Never the headers.** Save the path, the parameters, the status and the body. The request headers carry the token.

#### [day2#rerunnable] Write records by key, then the checkpoint: a crash anywhere is safe

*Rerunnable loads*

1. **1 · Fetch** the page after the saved cursor
2. **2 · Save raw** the page as it came
3. **3 · Write by id** skip ids already kept
4. **4 · Checkpoint** the next cursor

- A crash before step 4 means the page is fetched again; step 3 makes that harmless.
- "Exactly once" is proven by counting: records equal unique ids equal the source's count.

#### [day2#tokens-out] A token belongs to a person and the environment, never to the code

*Tokens*

```python
# file: client.py
import os

# set in the shell, or in .env (excluded by .gitignore)
token = os.environ["SOURCE_API_TOKEN"]
auth = {"Authorization": f"Bearer {token}"}
client = httpx.Client(headers=auth)
```

- Commit `.env.example` with a placeholder value; never `.env`.
- A token pasted in a notebook stays in its history and every copy.
- Tokens are issued per person by the data's owner, who can revoke them.

#### [day2#terms-first] Read the terms and limits before the first request

*Respectful collection*

- **Rate limits:** stay under them; honour `429` and `Retry-After`.
- **Licence:** what you may keep, share and publish, and how to credit the source.
- **Retention:** how long raw responses may be kept.
- **No published limit** is not permission: set your own pace, write it in the code, and say it is yours.

> **In the lab.** The public API task reads the series' licence from its metadata and stops unless it is open; it then paces itself at one request a second, the course's own rule.

#### [day2#open-data-policy] The Open Data Policy asks for machine-readable formats and a licence

*National reference*

- **Principle 2 · Open Format and Machine-Readable.** «المبدأ الثاني: الصيغة المفتوحة وإمكانية القراءة آلياً»: data is made available in a machine-readable format that allows automated processing, in widely used file formats such as CSV, XLS, JSON and XML.
- **Principle 7 · Open Data Licensing in KSA.** «المبدأ السابع: ترخيص البيانات المفتوحة في المملكة»: open data is subject to a licence that sets the conditions of use; using the data indicates acceptance of the licence terms.

NDMO Open Data Policy, National Data Governance Policies, version 1 of 5/5/2020, read from the PDF on sdaia.gov.sa on 25 November 2026. Paraphrased; the Arabic headings are quoted.

#### [day2#check-retry] Which response should the client retry?

*Checkpoint*

**Question:** A pull from a weather-station network's API gets these four answers on different pages. Which one should it retry after a wait, with no change to the request?

- A. 503 Service Unavailable
- B. 400 Bad Request: "limit must be at most 200"
- C. 401 Unauthorized
- D. 404 Not Found for one station

#### [day2#lab-2-1] Every record, exactly once

Lab 2.1 · 100 min

A client for the mock platform API that follows cursors, retries, keeps raw pages and resumes, then a polite public pull

[D2_1_api_client.ipynb](https://sdaiaacademy.github.io/fnd-dat-103/labs/D2_1_api_client.ipynb)

- [ ] Read the API’s terms; load the token from the environment (10 min)
- [ ] Fetch one page by hand (10 min)
- [ ] Write fetch_all: cursor, raw pages, checkpoint (25 min)
- [ ] Add retries for 429 and 5xx; stop on other errors (20 min)
- [ ] Interrupt, resume, prove exactly once (10 min)
- [ ] Find what offset paging repeats and misses (10 min)
- [ ] Read a public API’s licence, then pull every page politely (15 min)
- [ ] ✱ Stretch: Make the public pull resumable

#### [day2#api-debrief] 1,200 sessions, exactly once, through 429, 500, 503 and a crash

*Debrief of lab 2.1*

- **16** requests for 12 pages, retries included
- **4.2 s** waited, on the fake clock
- **100** records dropped as duplicates on resume
- **20** ids repeated by offset paging, and 20 never seen

The course's reference run of lab 2.1 on the mock API (1,200 synthetic sessions). The public pull of that run read 266 rows in 6 pages, matching the API's own total.

### Session 2: Schema and validation

#### [day2#s2] Schema and validation

*Session 2*

- Flatten nested records into one table per grain, keys carried down
- Declare a schema and prove the written files match it
- Decide per batch whether to load, quarantine rows or reject, and report why

#### [day2#one-table-per-grain] Nested JSON becomes one table per grain, with the key carried down

*Flattening*

```
# file: appointment.json
{"visit_id": "V-0193",
 "clinic": {"id": "C04", "floor": 2},
 "booked_at": "2026-11-03T08:40:00+03:00",
 "tests": [{"code": "T-11", "result": 5.4},
           {"code": "T-27", "result": 0.9}]}
```

- **Once per visit** (the clinic object): columns of the visits table, `clinic_id`, `clinic_floor`.
- **A list** (the tests): its own table, one row per test, with `visit_id` on every row.
- Count after flattening: visits equal records; tests equal the sum of list lengths.

#### [day2#declared-schema] Declare the schema in code, and cast to it before writing

*Declared types*

```python
# file: schema.py
import pyarrow as pa

VISITS = pa.schema([
    pa.field("visit_id", pa.string(), nullable=False),
    pa.field("clinic_id", pa.string(), nullable=False),
    pa.field("booked_at", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("month", pa.string(), nullable=False),   # the partition column
])
table = pa.Table.from_pandas(visits, schema=VISITS, preserve_index=False)
```

- A value that cannot be cast fails here, at the boundary, not in next month's report.

#### [day2#check-written] Prove the files match the declaration by reading their schema back

*Proof*

1. **1 · Write** partitioned by the declared column
2. **2 · Read the schema** of one written file
3. **3 · Compare** with the declaration, minus the partition column
4. **4 · Count** rows read back from the whole folder

> **Why minus one column.** In hive partitioning the partition value lives in the folder name; readers add it back as a column.

#### [day2#two-layers] Check each record, then check the table

*Validation*

| Layer | Rules | Example tool |
| --- | --- | --- |
| **Record**, one at a time | Required fields, types, patterns (a time with its offset), allowed values | JSON Schema |
| **Table**, the batch as a whole | Unique keys, ranges, one column against another, values that must exist in a register | Pandera |

- Record checks run before flattening, on the raw JSON.
- Table checks run on the typed table, after the cast.

#### [day2#json-schema-example] A JSON Schema states what one record must be

*Record checks*

```
# file: visit.schema.json
{"type": "object",
 "required": ["visit_id", "clinic", "booked_at", "tests"],
 "properties": {
   "visit_id": {"type": "string", "pattern": "^V-[0-9]{4}$"},
   "booked_at": {"type": "string",
     "pattern": "^[0-9-]{10}T[0-9:]{8}(Z|[+-][0-9]{2}:[0-9]{2})$"},
   "tests": {"type": "array", "minItems": 1}}}
```

- Each error names its rule (`required`, `type`, `pattern`) and its path: the report's reason.

#### [day2#pandera-example] Named table checks give every failing row a reason

*Table checks*

```python
# file: checks.py
import pandera.pandas as pa

checks = pa.DataFrameSchema(
    {"visit_id": pa.Column(None, pa.Check(lambda s: ~s.duplicated(keep=False), name="duplicate_key")),
     "clinic_id": pa.Column(None, pa.Check(lambda s: s.isin(CLINICS), name="unknown_clinic"))},
    checks=[pa.Check(lambda df: df["seen_at"] >= df["booked_at"], name="seen_before_booked")])
checks.validate(visits, lazy=True)   # raises SchemaErrors listing every failure
```

#### [day2#fail-or-quarantine] Reject the batch, or quarantine rows: decide by written rules

*The decision*

1. **The interface changed** a required field missing from nearly every record: reject the batch, name the field
2. **Some rows break the rules** quarantine each with its reason, keep the rest
3. **Too many rows break** above the organisation's threshold: reject the batch
4. **Otherwise** load the valid rows

#### [day2#owners-see] Quarantine so that owners see what failed, and fix it at the source

*Quarantine*

- **The loader.** Writes each row with its rule and meaning; does not edit or release rows.
- **The data owner.** Corrects the source and sends the rows again.
- **A second person.** Reviews any release of quarantined rows.

> **Next.** Data contracts, with versions and service levels between sender and receiver, follow in DEV-DAT-204.

#### [day2#check-quarantine] Load, quarantine or reject?

*Checkpoint*

**Question:** A library's loans batch has 400 rows. Twelve rows (3%) name a branch code that is not in the branch register; every other check passes. The written rules: reject on a changed interface, or above 5% quarantined.

- A. Reject the whole batch
- B. Map the twelve codes to the nearest valid branch and load all
- C. Load 388 rows and quarantine 12 with their reason
- D. Load 388 rows and drop the 12

#### [day2#lab-2-2] Flatten, write, validate

Lab 2.2 · 90 min

Raw API pages flattened to typed tables, written as day-partitioned Parquet, then five batches loaded, quarantined or rejected

[D2_2_flatten_validate.ipynb](https://sdaiaacademy.github.io/fnd-dat-103/labs/D2_2_flatten_validate.ipynb)

- [ ] Check every raw record against the JSON Schema (15 min)
- [ ] Flatten into sessions and readings tables (20 min)
- [ ] Write day-partitioned Parquet with the declared schema; check it (15 min)
- [ ] Declare the table checks with Pandera (15 min)
- [ ] Validate five batches and write the report (20 min)
- [ ] Read the quarantine file as its owner (5 min)
- [ ] ✱ Stretch: Add an optional field (schema version 2) without breaking version 1

#### [day2#validate-debrief] Two batches rejected, two partly quarantined, the clean one loaded whole

*Debrief of lab 2.2*

| Batch | Decision | Why |
| --- | --- | --- |
| 1 | load 200 | clean |
| 2 | load 197, quarantine 3 | a missing field, a wrong type, a time without offset |
| 3 | load 194, quarantine 6 | a duplicated key, two out-of-range values, an end before its start, an unknown station |
| 4 | reject | energy_kwh renamed in every record |
| 5 | reject, 20 rows to quarantine | 10% of times without offsets, above 5% |

#### [day2#capstone-brief] Your follow-up task: a checked ingestion script, run live on an unseen batch

*The capstone*

- One script: read the register in its real encoding, convert a vendor log to UTC, validate the sessions, write typed Parquet, quarantine and report.
- Practise on `labs/capstone/practice/` and on batches of your own seeds.
- Hand in a public GitHub repository link within two weeks; no token or `.env` in it.

- **On the day.** The assessor generates a batch you have not seen. You run the script live for six minutes, then answer five minutes of questions.

#### [day2#wrap-up] Three things to keep

*Day 2 · Wrap-up*

- **Pull politely, prove completeness.** Terms first, cursor, backoff, raw pages, and a count that proves exactly once.
- **Declare, then prove.** A schema in code, a cast at the boundary, and the written schema read back.
- **Stop bad batches visibly.** Reject or quarantine by written rules, and send the reasons to the owner.

#### [day2#next] The supervised check now; the capstone in two weeks

*Next*

- The check is without assistants; bring only the device that shows it.
- Build the ingestion script in the follow-up task, and test it on several seeds.
- Bring a terminal that runs it, and your repository link, to the capstone session.
