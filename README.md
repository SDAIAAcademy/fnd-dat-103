<!-- academy:title -->
# Data Formats, Interfaces and Quality Checks

صيغ البيانات وواجهاتها وفحوص جودتها

Data & AI Foundations Track · SDAIA Academy · FND-DAT-103 · Level 100

REPLACE: one line under the title: what participants can do after the course

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
| Day 1 | REPLACE: the theme of this unit, in a few words | REPLACE: the title of Session 1; REPLACE: the title of Session 2; REPLACE: the title of Session 3; REPLACE: the title of Session 4 | [`slides/day1.html`](slides/day1.html) |
| Day 2 | REPLACE: the theme of this unit, in a few words | REPLACE: the title of Session 1; REPLACE: the title of Session 2; REPLACE: the title of Session 3; REPLACE: the title of Session 4 | [`slides/day2.html`](slides/day2.html) |
<!-- /academy:units -->

## Case study

**REPLACE: the name of the fictional organisation every lab works on.** REPLACE: two sentences on the case study and its synthetic data

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | REPLACE: what participants build in lab 1.1 | [`D1_1.ipynb`](labs/D1_1.ipynb) |
| 1.2 | Day 1 · Session 2 | REPLACE: what participants build in lab 1.2 | [`D1_2.ipynb`](labs/D1_2.ipynb) |
| 1.3 | Day 1 · Session 3 | REPLACE: what participants build in lab 1.3 | [`D1_3.ipynb`](labs/D1_3.ipynb) |
| 1.4 | Day 1 · Session 4 | REPLACE: what participants build in lab 1.4 | [`D1_4.ipynb`](labs/D1_4.ipynb) |
| 2.1 | Day 2 · Session 1 | REPLACE: what participants build in lab 2.1 | [`D2_1.ipynb`](labs/D2_1.ipynb) |
| 2.2 | Day 2 · Session 2 | REPLACE: what participants build in lab 2.2 | [`D2_2.ipynb`](labs/D2_2.ipynb) |
| 2.3 | Day 2 · Session 3 | REPLACE: what participants build in lab 2.3 | [`D2_3.ipynb`](labs/D2_3.ipynb) |
| 2.4 | Day 2 · Session 4 | REPLACE: what participants build in lab 2.4 | [`D2_4.ipynb`](labs/D2_4.ipynb) |
<!-- /academy:labs -->

## Prerequisites

- FND-DAT-102 Data Wrangling with DataFrames
- Writes Python functions and handles exceptions (FND-PRG-101 or equivalent)

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

- REPLACE: every source the course cites, with its address, in course.json under "sources"; this list is written from there
<!-- /academy:sources -->

### National references

- NDMO Open Data Policy: machine-readable formats, read before the public API lab: REPLACE: the address of the official text
