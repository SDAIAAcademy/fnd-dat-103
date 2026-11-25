---
course: "Data Formats, Interfaces and Quality Checks"
code: "FND-DAT-103"
version: "2027.1.0"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/fnd-dat-103/index.html"
---

# Data Formats, Interfaces and Quality Checks

صيغ البيانات وواجهاتها وفحوص جودتها

Data & AI Foundations Track · 2 teaching days + capstone day · 16 hours · Level 100

Move data between files, interfaces and tables without losing or corrupting it, and stop a bad batch at the boundary

Participants move data between files, interfaces and tables without losing or corrupting it. They compare delimited, JSON Lines and columnar files, repair encoding and time-zone faults, write a paginated API client with retries, flatten nested JSON and declare a schema whose checks stop a bad batch from loading.

**Who it is for:** Beginners. Anyone starting technical data or AI work, including future analysts, data scientists, data engineers and AI engineers who can code but have not yet worked with messy real data.

**Format:** Workshop: two days with labs, a short pre-work task and a tracked follow-up task

## The case study

**The charging network.** The charging network is a fictional private operator of 40 public fast-charging stations for electric vehicles in one unnamed city, whose charging sessions reach the data team as charger logs from two vendors, legacy exports from the station team and pages of the charge-point platform API. Every file is synthetic and generated with a fixed seed: 200,000 sessions for the format comparison, six damaged files, 1,200 nested sessions behind a mock API with injected faults, five batches with seeded defects, and capstone batches an assessor generates from a seed.

## The course

### Day 1: Files: formats, text and time

Slides: https://sdaiaacademy.github.io/fnd-dat-103/slides/day1.md

- **Session 1: File formats**
  - Name the dialect settings a delimited file needs: delimiter, quoting, encoding, line ending
  - Explain how columnar files store types, compress columns and read only what a query needs
  - Measure size, read time and type fidelity of one dataset in three formats
  - [Lab 1.1: One dataset, three formats (80 min)](https://sdaiaacademy.github.io/fnd-dat-103/labs/D1_1_three_formats.ipynb)
- **Session 2: Text and time**
  - Tell bytes from characters and read a file’s first bytes for its encoding
  - Recognise the symptom of a wrong code page, a byte order mark, double encoding and UTF-16
  - Convert local times without offsets to UTC, across a daylight-saving change
  - [Lab 1.2: Six damaged files (90 min)](https://sdaiaacademy.github.io/fnd-dat-103/labs/D1_2_damaged_files.ipynb)

### Day 2: Interfaces and the boundary

Slides: https://sdaiaacademy.github.io/fnd-dat-103/slides/day2.md

- **Session 1: Interfaces**
  - Decide from a status code whether to retry, wait or stop
  - Explain why cursor pagination survives inserts that offset pagination does not
  - Build a rerunnable pull with raw responses, a checkpoint and idempotent writes
  - [Lab 2.1: Every record, exactly once (100 min)](https://sdaiaacademy.github.io/fnd-dat-103/labs/D2_1_api_client.ipynb)
- **Session 2: Schema and validation**
  - Flatten nested records into one table per grain, keys carried down
  - Declare a schema and prove the written files match it
  - Decide per batch whether to load, quarantine rows or reject, and report why
  - [Lab 2.2: Flatten, write, validate (90 min)](https://sdaiaacademy.github.io/fnd-dat-103/labs/D2_2_flatten_validate.ipynb)

### Capstone: Live ingestion run

Slides: https://sdaiaacademy.github.io/fnd-dat-103/slides/capstone.md

## Capstone

A checked ingestion script, run live on a batch the assessor supplies

**What you submit:** An individual task, submitted as a public GitHub repository link within two weeks of the workshop: the ingestion script, its declared schemas, a README with its rules and how to run it, and the report of a run on the practice batch. No token, key or .env file in the repository. The live run uses a batch the assessor generates on the day from a seed of their choice.

**Rubric:**

- Every input read correctly: encodings and times normalised to UTF-8 and UTC, each repair logged: 20%
- Typed, partitioned output whose written schema matches the declared one: 15%
- Record and table checks applied with stated rules: load, quarantine or reject: 20%
- Rerunnable: a second run on the same batch gives the same files, the input kept untouched: 10%
- A report and quarantine file the data owner can act on; no token in the repository: 10%
- Live run: the assessor’s batch loaded or rejected for the correct reasons, and explained: 25%

## Outcomes

- **LO1** Compare delimited, JSON Lines and columnar files on size, read time and type fidelity, given one dataset in each format (Awareness) Evidence: a measured comparison table
- **LO2** Explain how encodings, byte order marks and time zones corrupt data, and identify each symptom, given six damaged files (Awareness) Evidence: a diagnosis correct on five of six
- **LO3** Implement an API client that follows cursor pagination, respects rate limits, retries with backoff and keeps raw responses, given a mock API with injected errors (Applied) Evidence: a run log showing every record retrieved exactly once
- **LO4** Convert nested JSON into typed tables written as partitioned columnar files, given the raw responses (Applied) Evidence: files whose schema matches the declared one
- **LO5** Implement validation checks that stop a load when a batch breaks the declared schema, given batches with seeded defects (Applied) Evidence: a report that catches every defect and passes a clean batch

## Tools

- **Columnar file reading and writing:** Apache Arrow with Parquet, DuckDB
- **HTTP client:** httpx, requests
- **Schema validation:** JSON Schema, Pandera
- **Mock API:** an Academy mock service in a container, a local FastAPI server

## Prerequisites

- FND-DAT-102 Data Wrangling with DataFrames
- Writes Python functions and handles exceptions (FND-PRG-101 or equivalent)

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

---

SDAIA Academy · Data & AI Foundations Track · Data Formats, Interfaces and Quality Checks

Course version 2027.1.0 · engine 1.0.0 · built 2026-11-25 · commit 45af7a9
