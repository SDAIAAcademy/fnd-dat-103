<!-- academy:title -->
# Data Formats, Interfaces and Quality Checks

صيغ البيانات وواجهاتها وفحوص جودتها

Data & AI Foundations Track · SDAIA Academy · FND-DAT-103 · Level 100

Move data between files, interfaces and tables without losing or corrupting it, and stop a bad batch at the boundary

Participants move data between files, interfaces and tables without losing or corrupting it. They compare delimited, JSON Lines and columnar files, repair encoding and time-zone faults, write a paginated API client with retries, flatten nested JSON and declare a schema whose checks stop a bad batch from loading.

**Format:** Workshop: two days with labs, a short pre-work task and a tracked follow-up task

**Course page:** https://sdaiaacademy.github.io/fnd-dat-103/
<!-- /academy:title -->

## Outcomes

| | Outcomes | Level | Evidence |
|---|---|---|---|
| LO1 | Compare delimited, JSON Lines and columnar files on size, read time and type fidelity, given one dataset in each format | Awareness | a measured comparison table |
| LO2 | Explain how encodings, byte order marks and time zones corrupt data, and identify each symptom, given six damaged files | Awareness | a diagnosis correct on five of six |
| LO3 | Implement an API client that follows cursor pagination, respects rate limits, retries with backoff and keeps raw responses, given a mock API with injected errors | Applied | a run log showing every record retrieved exactly once |
| LO4 | Convert nested JSON into typed tables written as partitioned columnar files, given the raw responses | Applied | files whose schema matches the declared one |
| LO5 | Implement validation checks that stop a load when a batch breaks the declared schema, given batches with seeded defects | Applied | a report that catches every defect and passes a clean batch |

<!-- academy:units -->
## Units

| Unit | Title | Sessions | Slides |
|---|---|---|---|
| Day 1 | Files: formats, text and time | File formats; Text and time | [`slides/day1.html`](slides/day1.html) |
| Day 2 | Interfaces and the boundary | Interfaces; Schema and validation | [`slides/day2.html`](slides/day2.html) |
| Capstone | Live ingestion run |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**The charging network** is a fictional private operator of 40 public fast-charging stations for electric vehicles in one unnamed city, coded ST01 to ST40 in five generic sectors (North, South, East, West, Central). Its charging sessions reach the data team in four shapes: charger logs from two vendors (Vendor A and Vendor B), legacy exports from the station team's old asset system, pages of the charge-point platform's API, and the typed tables that finance and operations read. People appear only by role: the data team lead, the operations analyst, the finance controller and the station team.

Every file is synthetic and generated with fixed seeds (`labs/prepare_data.py`, `labs/chargekit.py`): 200,000 sessions for the format comparison; six damaged files from the station team and the two charger vendors, with encoding and time faults to diagnose; 1,200 nested sessions behind a mock API with injected faults; five batches with seeded defects; and capstone batches generated from a seed. Sessions, stations and accounts are letter-prefixed codes; the files hold no telephone, identity, account or card numbers. The mock API's token is a course value that opens nothing else.

## How the course is organised

Two teaching days of two long sessions each, a short pre-work task, a supervised check at the end of Day 2, and a tracked follow-up task that ends in the live capstone run. Sixteen hours in all (960 minutes):

| Part | Minutes | What happens |
|---|---|---|
| Instruction | 240 | Concepts, demonstrations, checkpoints and lab debriefs: 65 in session 1.1, 60 in 1.2, 55 in 2.1, 60 in 2.2 |
| Labs | 360 | Lab 1.1 80, lab 1.2 90, lab 2.1 100, lab 2.2 90 |
| Assessment | 60 | The supervised AI-off check at the end of Day 2: rules and devices away 5, the check 50, collection 5 |
| Guided self-study | 180 | Pre-work before Day 1 (45, AI-off, [`labs/prework.md`](labs/prework.md)): read principles 2 and 7 of the Open Data Policy (15) and a byte, dialect and time reading drill (30); the tracked follow-up task (135): the capstone ingestion script, tested on the practice batch and on batches of your own seeds |
| Capstone | 120 | The live runs in groups of eight: opening 8; eight participants, each with a 6-minute live run, 5 minutes of questions and 2 minutes of changeover (104); close 8 |

Day 1 is 295 minutes of teaching; Day 2 is 305 minutes of teaching and the 60-minute check.

## Assessment

- Lab outputs, test-checked (40%)
- Supervised AI-off check (20%)
- Capstone script and report (30%)
- Live run (10%)

**Passing:** 70% overall, with the capstone batch loaded or rejected for the correct reasons

**Authenticity:** A supervised check without assistance, and a live capstone run on an unseen batch

**Certificate:** completion with assessed work

The capstone script, its report and the live run are scored with the rubric of the capstone deck (six criteria, 100 points): the live-run criterion carries 25 of the 100, the same share as the live run's 10% within the capstone's 40%. The supervised check items are kept out of this repository.

## AI policy

AI-off in the pre-work and the supervised check. AI-tutor in labs. AI-full in the capstone, which runs live.

## Responsible use

Covers respectful collection: participants read an API's terms and rate limits before pulling, keep tokens out of code, and quarantine invalid rows so owners see what failed.

In the labs: lab 2.1 reads the mock API's terms and the public series' licence before the first pull, paces the public pull at one request a second (the course's own rule, since that API publishes no limit), loads the token from the environment and checks that no saved file holds it; lab 2.2 writes a quarantine file with a reason per row for the station team, who correct and resend, while a second person reviews any release.

## The capstone: a checked ingestion script

A checked ingestion script, run live on a batch the assessor supplies. Each participant submits a public GitHub repository link within two weeks of the workshop: the script, its declared schemas, a README with its rules and how to run it, and the report of a run on the practice batch, with no token, key or `.env` file. On the capstone day the assessor generates an unseen batch with `labs/capstone/make_batch.py` from a seed of their choice and keeps its key; the participant runs the script live (6 minutes) and answers questions (5). The brief is `labs/capstone/README.md`; the practice batch and its key are in `labs/capstone/`.

## The data, the mock API and the public API

The labs run on a laptop processor or in Google Colab, with Python through `uv` (`labs/pyproject.toml`). No lab calls a language model. The mock of the charge-point platform API (`labs/mockapi.py`) is a FastAPI application the notebooks call in-process, with a fixed schedule of faults; `uv run python mockapi.py` (from `labs/`) also serves it on this computer. The last task of lab 2.1 calls a public open-data API, the World Bank Indicators API, live: it reads the series' licence first (CC BY 4.0), and nothing it returns is stored in this repository.

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | One dataset, three formats | [`D1_1_three_formats.ipynb`](labs/D1_1_three_formats.ipynb) |
| 1.2 | Day 1 · Session 2 | Six damaged files | [`D1_2_damaged_files.ipynb`](labs/D1_2_damaged_files.ipynb) |
| 2.1 | Day 2 · Session 1 | Every record, exactly once | [`D2_1_api_client.ipynb`](labs/D2_1_api_client.ipynb) |
| 2.2 | Day 2 · Session 2 | Flatten, write, validate | [`D2_2_flatten_validate.ipynb`](labs/D2_2_flatten_validate.ipynb) |
<!-- /academy:labs -->

## Prerequisites

- FND-DAT-102 Data Wrangling with DataFrames
- Writes Python functions and handles exceptions (FND-PRG-101 or equivalent)

Day 1 assumes typed DataFrames from FND-DAT-102 and Python exceptions from FND-PRG-101. Data contracts, with versions and service levels, follow in DEV-DAT-204.

<!-- academy:tools -->
## Tools

Each line is a capability; the examples are interchangeable.

- **Columnar file reading and writing:** Apache Arrow with Parquet, DuckDB
- **HTTP client:** httpx, requests
- **Schema validation:** JSON Schema, Pandera
- **Mock API:** an Academy mock service in a container, a local FastAPI server
<!-- /academy:tools -->

<!-- academy:sources -->
## Sources

### National references

- [National Data Management Office: Open Data Policy (National Data Governance Policies, version 1, 5/5/2020)](https://sdaia.gov.sa/en/SDAIA/about/Documents/OpenDataPolicy.pdf)
- [مكتب إدارة البيانات الوطنية: سياسة البيانات المفتوحة](https://sdaia.gov.sa/ar/SDAIA/about/Documents/OpenDataPolicyAr.pdf)
- [SDAIA: Regulations and policies (index page)](https://sdaia.gov.sa/en/SDAIA/about/Pages/RegulationsAndPolicies.aspx)

### Formats and standards

- [RFC 4180: Common Format and MIME Type for Comma-Separated Values (CSV) Files](https://www.rfc-editor.org/rfc/rfc4180)
- [RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259)
- [JSON Lines](https://jsonlines.org/)
- [RFC 3339: Date and Time on the Internet: Timestamps](https://www.rfc-editor.org/rfc/rfc3339)
- [RFC 9110: HTTP Semantics (status codes, Retry-After)](https://www.rfc-editor.org/rfc/rfc9110)
- [RFC 6585: Additional HTTP Status Codes (429 Too Many Requests)](https://www.rfc-editor.org/rfc/rfc6585)
- [Apache Parquet: file format documentation](https://parquet.apache.org/docs/file-format/)
- [Python documentation: zoneinfo, IANA time zone support (fold and ambiguous times)](https://docs.python.org/3/library/zoneinfo.html)
- [Python documentation: codecs, standard encodings (cp1256, utf-8-sig, utf-16)](https://docs.python.org/3/library/codecs.html#standard-encodings)

### Tools (examples of each slot)

- [Apache Arrow: Python documentation (pyarrow, datasets and partitioning)](https://arrow.apache.org/docs/python/)
- [DuckDB: reading Parquet files](https://duckdb.org/docs/stable/data/parquet/overview)
- [DuckDB: SQL on Apache Arrow (querying Arrow tables held in Python variables)](https://duckdb.org/docs/stable/guides/python/sql_on_arrow)
- [HTTPX](https://www.python-httpx.org/)
- [Requests](https://requests.readthedocs.io/)
- [JSON Schema: specification (draft 2020-12)](https://json-schema.org/specification)
- [Pandera documentation](https://pandera.readthedocs.io/)
- [FastAPI: testing with TestClient](https://fastapi.tiangolo.com/tutorial/testing/)

### The public open-data API of lab 2.1

- [World Bank: API basic call structures (page and per_page)](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures)
- [World Bank: terms of use for datasets (CC BY 4.0 unless labelled otherwise)](https://www.worldbank.org/ext/en/legal/terms-conditions/datasets)
- [World Bank Data Catalog: public licenses](https://datacatalog.worldbank.org/public-licenses)
<!-- /academy:sources -->

### National references

- NDMO Open Data Policy («سياسة البيانات المفتوحة»), one of the National Data Governance Policies, version 1 of 5/5/2020, read from the PDFs at https://sdaia.gov.sa/en/SDAIA/about/Documents/OpenDataPolicy.pdf (Arabic: https://sdaia.gov.sa/ar/SDAIA/about/Documents/OpenDataPolicyAr.pdf) on 25 November 2026; SDAIA's regulations and policies page (https://sdaia.gov.sa/en/SDAIA/about/Pages/RegulationsAndPolicies.aspx) lists the national policies but refuses automated requests, so the edition it shows was not checked by script. Read in the pre-work for principle 2, «الصيغة المفتوحة وإمكانية القراءة آلياً» (open format and machine-readable), and principle 7, «ترخيص البيانات المفتوحة في المملكة» (open data licensing).
