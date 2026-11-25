---
course: "Data Formats, Interfaces and Quality Checks"
code: "FND-DAT-103"
version: "2027.1.0"
deck: "day1"
day: 1
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/fnd-dat-103/slides/day1.html"
---

# Data Formats, Interfaces and Quality Checks

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
