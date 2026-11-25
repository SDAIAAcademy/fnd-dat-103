---
course: "Data Formats, Interfaces and Quality Checks"
code: "FND-DAT-103"
version: "2027.1.0"
scope: "course"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/fnd-dat-103/"
---

# Data Formats, Interfaces and Quality Checks

Move data between files, interfaces and tables without losing or corrupting it, and stop a bad batch at the boundary

Participants move data between files, interfaces and tables without losing or corrupting it. They compare delimited, JSON Lines and columnar files, repair encoding and time-zone faults, write a paginated API client with retries, flatten nested JSON and declare a schema whose checks stop a bad batch from loading.

- **Audience:** Beginners. Anyone starting technical data or AI work, including future analysts, data scientists, data engineers and AI engineers who can code but have not yet worked with messy real data.
- **Prerequisites:** FND-DAT-102 Data Wrangling with DataFrames; Writes Python functions and handles exceptions (FND-PRG-101 or equivalent)
- **Case study:** The charging network: The charging network is a fictional private operator of 40 public fast-charging stations for electric vehicles in one unnamed city, whose charging sessions reach the data team as charger logs from two vendors, legacy exports from the station team and pages of the charge-point platform API. Every file is synthetic and generated with a fixed seed: 200,000 sessions for the format comparison, six damaged files, 1,200 nested sessions behind a mock API with injected faults, five batches with seeded defects, and capstone batches an assessor generates from a seed.

## Outcomes

- LO1 (Awareness): Compare delimited, JSON Lines and columnar files on size, read time and type fidelity, given one dataset in each format
- LO2 (Awareness): Explain how encodings, byte order marks and time zones corrupt data, and identify each symptom, given six damaged files
- LO3 (Applied): Implement an API client that follows cursor pagination, respects rate limits, retries with backoff and keeps raw responses, given a mock API with injected errors
- LO4 (Applied): Convert nested JSON into typed tables written as partitioned columnar files, given the raw responses
- LO5 (Applied): Implement validation checks that stop a load when a batch breaks the declared schema, given batches with seeded defects

## Day 1: Files: formats, text and time

What a file promises, what it loses, and how bytes and clocks corrupt data

#### [day1#title] Files: formats, text and time

*SDAIA Academy · Data Formats, Interfaces and Quality Checks*

Day 1: What a file promises, what it loses, and how bytes and clocks corrupt data

Data & AI Foundations Track · 2 teaching days + capstone day · 2 sessions · 2 labs · FND-DAT-103

#### [day1#agenda] Files: formats, text and time

*Today*

- **Session 1 · File formats**: Delimited dialects, JSON and JSON Lines, columnar files with partitions, and in-memory interchange, compared by measurement
- **Session 2 · Text and time**: Bytes and characters, UTF-8 and legacy Arabic code pages, byte order marks, offsets, UTC and daylight saving

#### [day1#setup-check] One notebook proves your setup

*Before we start*

- **Colab:** open `labs/00_setup_check.ipynb` from the course page; its first cell clones the course and installs the libraries.
- **Laptop:** from `labs/`, run `uv sync`, then open the notebook.
- Its last line must read **PASS · ready for the labs**.

- **What it checks.** pandas, pyarrow, DuckDB, httpx, FastAPI, Pandera, jsonschema and the time-zone database; the case data; one call to the mock API. No lab calls a language model, so no model key is needed.

### Session 1: File formats

#### [day1#s1] File formats

*Session 1*

- Name the dialect settings a delimited file needs: delimiter, quoting, encoding, line ending
- Explain how columnar files store types, compress columns and read only what a query needs
- Measure size, read time and type fidelity of one dataset in three formats

#### [day1#four-shapes] Charging sessions reach the data team in four shapes

*The case*

- **Charger logs.** Text files from Vendor A and Vendor B chargers, one line per session.
- **Legacy exports.** The station team's old asset system: registers and notes in Arabic.
- **Platform API.** The charge-point platform's pages of nested JSON.
- **Analysts' tables.** What finance and operations read: typed, partitioned, checked.

The charging network runs 40 fictional stations in one unnamed city. Every file in this course is synthetic.

#### [day1#format-promises] A format decides what survives the trip

*What a format promises*

| Promise | Delimited (CSV) | JSON Lines | Columnar (Parquet) |
| --- | --- | --- | --- |
| Types travel with the data | No: all text | A few: string, number, true/false, null | Yes, in the file's schema |
| Nested values | No | Yes | Yes |
| Append one record | Yes | Yes, one line | No: write a new file |
| Read only some columns | No | No | Yes |
| Readable in a text editor | Yes | Yes | No |

#### [day1#csv-dialect] A CSV without its dialect is half a file

*Delimited files*

```
# file: payroll_export.csv
staff_code;grade;allowance;note
0042;B2;1250,50;"ترقية، ""مؤقتة"""
0107;A1;980,00;
```

- **Delimiter:** here a semicolon, because the comma is the decimal mark.
- **Quoting:** a field holding the delimiter or a quote is enclosed in quotes; an inner quote is doubled.
- **Encoding, line ending:** not in the file; someone must say them.
- **Types:** not in the file: "0042" is a code, not 42.

> **What goes wrong.** A reader with the default dialect splits the note at its comma and turns the staff code into the number 42.

#### [day1#json-lines] JSON Lines is one record per line, and that changes everything operational

*JSON and JSON Lines*

- **One JSON document.** An array of a million objects: one opening bracket, one closing bracket. To add a record, rewrite the file. A cut at byte 900,000 makes the whole file invalid.
- **JSON Lines.** One complete JSON value per line, UTF-8, a newline after each. Append a line; stream it line by line; a damaged line loses one record, not the file.

> **Still text.** Every line repeats every key, and numbers and times are written as text: large on disk, and a reader must parse each value back.

#### [day1#columnar] A columnar file stores each column together, typed and compressed

*Columnar files*

1. **File** a footer with the schema and where everything is
2. **Row groups** blocks of rows, e.g. 100,000 sessions each
3. **Column chunks** one per column per row group, with min and max
4. **Pages** encoded and compressed values

- A query that needs two columns reads two chunks per row group, not every byte.
- Statistics let a reader skip row groups whose range cannot match.
- Similar values side by side compress well: codes, dates, small numbers.

#### [day1#partitions] A partition is a folder per value, so a reader opens only what it needs

*Partitions*

```
# file: tables/sessions/
day=2026-10-19/part-0.parquet
day=2026-10-20/part-0.parquet
day=2026-10-21/part-0.parquet
...
```

- The value lives in the folder name (the "hive" style), not inside the files.
- A query for one day reads one folder.
- Choose a column people filter on, with tens to hundreds of values, not millions.

> **What goes wrong.** Partitioning by session id writes one tiny file per session: thousands of files and slower reads.

#### [day1#arrow-interchange] Arrow lets two tools share a table in memory, with no file between them

*In memory*

```python
# file: interchange.py
import duckdb, pyarrow.parquet as pq

loans = pq.read_table("loans.parquet",
                      columns=["branch", "items"])
duckdb.sql("""SELECT branch, sum(items)
              FROM loans GROUP BY branch""")
```

- Arrow is a columnar layout in memory, as Parquet is on disk.
- DuckDB finds the Python variable `loans` and queries it as a table.
- No CSV in between: the types arrive as they left.

#### [day1#measure-fairly] Compare formats on three measures, taken the same way

*Measuring*

- **Size.** Bytes on disk. Stable: the same data gives the same size.
- **Read time.** The median of several reads on one machine. It moves with the machine, the cache and the run.
- **Type fidelity.** Column by column: same type and same values after a round trip with default readers.

> **What goes wrong.** One timing quoted as a property of a format. Report the machine and the median, and trust sizes and fidelity more than seconds.

#### [day1#check-formats] Which hand-over keeps the codes intact?

*Checkpoint*

**Question:** A library sends loan records with branch codes like "007" to analysts who read files with default settings. Which hand-over keeps "007" as "007"?

- A. A CSV with every field in quotes
- B. A Parquet file with the code declared as a string
- C. A JSON Lines file read back with the default reader settings
- D. A semicolon-separated file in UTF-8

#### [day1#lab-1-1] One dataset, three formats

Lab 1.1 · 80 min

The same 200,000 charging sessions written as CSV, JSON Lines and Parquet, measured for size, read time and type fidelity, and queried with DuckDB

[D1_1_three_formats.ipynb](https://sdaiaacademy.github.io/fnd-dat-103/labs/D1_1_three_formats.ipynb)

- [ ] Run the setup cell and generate the sessions table (5 min)
- [ ] Write CSV, JSON Lines and Parquet and compare their sizes (15 min)
- [ ] Read each file back and time it (15 min)
- [ ] Check type fidelity column by column (20 min)
- [ ] Query the Parquet file with DuckDB, and hand it an Arrow table (10 min)
- [ ] Write the comparison table and a recommendation (15 min)
- [ ] ✱ Stretch: Write the Parquet partitioned by day and query one partition

#### [day1#formats-debrief] Parquet kept 11 of 11 columns; CSV kept 7, JSON Lines 6

*Debrief of lab 1.1*

| Format | Size | Median read | Lost with default readers |
| --- | --- | --- | --- |
| CSV | 16,894 KB | 0.030 s | connector, started_at, status, idle_min |
| JSON Lines | 45,219 KB | 1.149 s | connector, energy_kwh, amount, status, idle_min |
| Parquet (zstd) | 2,562 KB | 0.016 s | none |

The course's reference run: 200,000 synthetic sessions on one laptop. Your seconds will differ; the sizes and losses will not.

### Session 2: Text and time

#### [day1#s2] Text and time

*Session 2*

- Tell bytes from characters and read a file’s first bytes for its encoding
- Recognise the symptom of a wrong code page, a byte order mark, double encoding and UTF-16
- Convert local times without offsets to UTC, across a daylight-saving change

#### [day1#bytes-not-text] A file holds bytes; text is bytes plus an agreed encoding

*Bytes and characters*

| The word سلام in | Bytes | Per letter |
| --- | --- | --- |
| UTF-8 | `d8 b3 d9 84 d8 a7 d9 85` | 2 |
| Windows-1256 (cp1256) | `d3 e1 c7 e3` | 1 |
| ISO-8859-6 | `d3 e4 c7 e5` | 1 |
| UTF-16 (little-endian, with its mark) | `ff fe 33 06 44 06` and so on | 2 |

#### [day1#legacy-code-pages] Read a legacy file as UTF-8 and it fails; read UTF-8 as legacy and it lies

*Legacy Arabic code pages*

- **cp1256 bytes read as UTF-8.** A UTF-8 decoder meets single high bytes it cannot use: an error, or `����` with `errors="replace"`. Loud, at least.
- **UTF-8 bytes read as cp1256.** cp1256 maps every byte to a character, so it never fails: سلام reads as ط³ظ„ط§ظ…. Quiet, and wrong.

> **Saved again, it sticks.** Write that wrong text back as UTF-8 and the file is now double-encoded: valid UTF-8, nonsense Arabic. Undo it by reversing the wrong step: encode as cp1256, decode as UTF-8.

#### [day1#byte-order-mark] A byte order mark is invisible text at the start of a file

*Byte order marks*

- `ef bb bf`: the UTF-8 mark, added by some editors and spreadsheet exports.
- `ff fe` or `fe ff`: the UTF-16 marks, which say the byte order.
- Read as plain UTF-8, the mark becomes the character ` ` glued to the first column name.

```python
# file: python
df = pd.read_csv("grades.csv")
df["student_code"]   # KeyError
df.columns[0]        # '﻿student_code'
pd.read_csv("grades.csv",
            encoding="utf-8-sig")
```

#### [day1#detect-then-confirm] Detection is a guess; confirm it with a word you know

*Diagnosis*

1. **1 · Look** the first bytes in hex: a mark, zero bytes, single high bytes
2. **2 · Try** decode with the likely encoding
3. **3 · Confirm** a value you know must appear, such as a station or branch name
4. **4 · Record** the encoding in the load log

> **Rule.** "It opened without an error" proves nothing for a single-byte code page: every byte decodes to something.

#### [day1#offsets-utc] A time without an offset is a guess about someone's clock

*Offsets and UTC*

| Written as | Means |
| --- | --- |
| `2026-11-02T09:00:00+03:00` | 09:00 on a clock three hours ahead of UTC |
| `2026-11-02T06:00:00Z` | The same instant, in UTC |
| `2026-11-02 09:00` | Unknown: which clock? |

- RFC 3339 times carry `Z` or `+hh:mm`: the instant is fixed.
- Store instants in UTC, keep the offset when it matters, convert to local time only to display.

#### [day1#daylight-saving] Daylight saving skips one hour in spring and repeats one in autumn

*Daylight saving*

- **Spring: a missing hour.** In the `CET` zone, on 29 March 2026, clocks jump from 02:00 to 03:00. A log line at 02:30 names a time that never happened there.
- **Autumn: a repeated hour.** In the `EET` zone, on 26 October 2025, 03:30 happens twice: first at 00:30 UTC, then at 01:30 UTC.

> **In Python.** `zoneinfo` marks the second pass of a repeated time with `fold=1`. Without another clue, such as the order of events, nobody can tell which pass a bare time meant.

#### [day1#symptoms] Each fault leaves its own fingerprint

*From symptom to cause*

| You see | Look for |
| --- | --- |
| A decode error, or `�` in place of Arabic | A single-byte code page read as UTF-8 |
| Arabic that reads as pairs of other Arabic letters, no error | Double encoding |
| A KeyError on a column you can see | A byte order mark |
| A zero byte after every ASCII letter | UTF-16 |
| Every time off by the same hours | A fixed-offset clock read as another |
| An offset that changes with the date | A zone with daylight saving |

#### [day1#check-text-time] What happened to the catalogue file?

*Checkpoint*

**Question:** A public library's catalogue export opens in UTF-8 without any error, but its Arabic titles read as long runs of pairs like ط§ظ„. What happened?

- A. It is in cp1256 and was read as UTF-8
- B. It starts with a UTF-8 byte order mark
- C. It was decoded as cp1256 once and saved again as UTF-8
- D. It was saved as UTF-16

#### [day1#lab-1-2] Six damaged files

Lab 1.2 · 90 min

Six files from the station team and two charger vendors diagnosed from their bytes and times, repaired, checked against the platform and logged

[D1_2_damaged_files.ipynb](https://sdaiaacademy.github.io/fnd-dat-103/labs/D1_2_damaged_files.ipynb)

- [ ] Run the setup cell and look at the six files as bytes (10 min)
- [ ] Write the diagnosis sheet before any repair (20 min)
- [ ] Repair the four text files (25 min)
- [ ] Convert Vendor A’s times to UTC (10 min)
- [ ] Convert Vendor B’s times to UTC across the clock change (15 min)
- [ ] Check against the platform and write the repair log (10 min)
- [ ] ✱ Stretch: Guess the code page of a file without being told

#### [day1#text-time-debrief] Vendor A was always 180 minutes off; Vendor B 120, then 60

*Debrief of lab 1.2*

- A constant gap is a fixed-offset clock: localise to `+03:00`, convert to UTC.
- A gap that changes on 25 October is a zone with daylight saving.
- Two of Vendor B's sessions ended before they started until the repeated hour was resolved by `seq`.

- **The repair log.** One line per file: symptom, cause, repair, rows. A repair nobody can see is a new fault.

#### [day1#wrap-up] Three things to keep

*Day 1 · Wrap-up*

- **Formats carry promises.** Only a format with a schema carries types; the others leave them to the reader's guess.
- **Bytes need an agreement.** Look at the bytes, decode, confirm with a known word, log the encoding.
- **Times need an offset.** Store UTC; a bare local time is a guess, and daylight saving makes it a bad one.

#### [day1#next] Interfaces, and the checks at the boundary

*Tomorrow*

- Copy `labs/.env.example` to `labs/.env`: the mock API's token lives there, never in a notebook.
- Reread principles 2 and 7 of the Open Data Policy from the pre-work before Day 2 starts.
- Day 2 ends with the supervised check, without assistants.

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

## Capstone: Live ingestion run

Each participant runs the ingestion script live on a batch the assessor generates, then answers questions

#### [capstone#title] Live ingestion run

*SDAIA Academy · Data Formats, Interfaces and Quality Checks*

Capstone: Each participant runs the ingestion script live on a batch the assessor generates, then answers questions

Data & AI Foundations Track · 2 teaching days + capstone day · 6 min talk and demo · 5 min Q&A · FND-DAT-103

#### [capstone#agenda] Two hours for eight live runs

*The capstone session*

- **Opening**: The task, the rubric, the running order
- **Eight live runs**: Each: the script on an unseen batch, then questions
- **Close**: What the batches caught, across the group

#### [capstone#the-task] A checked ingestion script, run live on a batch you have not seen

*What was asked*

- Reads the register in its real encoding and proves it.
- Converts the vendor log to UTC, the repeated hour included.
- Checks every session record and the table rules; loads, quarantines or rejects by stated rules.
- Writes typed Parquet partitioned by day, a quarantine file and a report.
- Gives the same files when run twice.

- **Submitted.** A public GitHub repository link within two weeks of the workshop: script, schemas, README, a practice run's report. No token, key or .env file.

#### [capstone#rubric] Six criteria, 100 points

*How the capstone is scored*

| Item | Value |
| --- | --- |
| Inputs read right, repairs logged | 20 |
| Output matches the declared schema | 15 |
| Checks with stated rules | 20 |
| Rerunnable, input untouched | 10 |
| A report the owner can act on | 10 |
| Live run, decided and explained | 25 |

> **In the course:** labs 40%, check 20%, script and report 30%, live run 10%. Pass: 70%, with the batch decided for the right reasons.

#### [capstone#run-format] Six minutes to run and explain, five for questions

*Each live run*

- **6 min · the run.** The assessor hands over a batch folder. Run the script on it, open the report, say what it decided and why.
- **5 min · questions.** The assessor asks about one decision, one repair and one rule, from the key in front of them.
- **2 min · changeover.** The next participant shares their screen and opens a terminal.

#### [capstone#running-order] Who runs when, on which batch

*Running order*

| # | Participant | Repository | Batch |
| --- | --- | --- | --- |
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |
| 6 |  |  |  |
| 7 |  |  |  |
| 8 |  |  |  |

#### [capstone#now-presenting] Live run

*Now running*

##### Questions

#### [capstone#peer-feedback] Write one line for each run

*While others run*

- The check you will copy into your own script.
- A decision the script made that you would make differently, and why.
- One thing the report should tell the data owner that it did not.

#### [capstone#review] What eight unseen batches showed

*After the runs*

- **Encodings.** Which scripts guessed the register's encoding, and which proved it with the Arabic it must contain?
- **Time.** Did every script place the repeated hour right, or only those that used the sequence?
- **Decisions.** Which rule was hardest to state: the changed field, or the share above which a batch is rejected?

#### [capstone#what-next] Keep the checks at the boundary, and take them further

*What next*

- **Re-check names and versions** of the libraries yearly: readers' defaults and format features change.
- **Data contracts:** DEV-DAT-204 Data Quality, Contracts and Observability adds versions, service levels and lineage to the checks built here.
- **Relational loads:** FND-DAT-101 SQL and Relational Data loads files into constrained tables with a load log.
