# Answer key for the trainer

All data is synthetic, written by `labs/prepare_data.py` with fixed seeds. The case is the
charging network, a fictional operator of public fast-charging stations in one unnamed city.
Identifiers are letter-prefixed codes; no file holds a telephone, identity, account or card
number. Numbers below are from the solution runs of this edition (pandas 3.1, pyarrow 26,
DuckDB 2.0, pandera 0.36, jsonschema 4.26, Python 3.12, a laptop processor). Read times change
with the machine; sizes, fidelity and every count below do not.

## Lab 1.1 · One dataset, three formats

Full run, 200,000 sessions (quick mode uses 20,000):

| Format | Size | Median read time (5 reads) | Columns that kept type and values |
|---|---|---|---|
| CSV | 16,894 KB | 0.030 s | 7 of 11 (lost: connector, started_at, status, idle_min) |
| JSON Lines | 45,219 KB | 1.149 s | 6 of 11 (lost: connector, energy_kwh, amount, status, idle_min) |
| Parquet (zstd) | 2,562 KB | 0.016 s | 11 of 11 |

- Connector "01" comes back as the integer 1 from both CSV and JSON Lines (default readers).
- CSV returns `started_at` as text; `pd.read_json` parses it back because the column name ends
  in `_at` (its default date-column rule): a convenience that depends on a naming habit.
- JSON Lines changes `energy_kwh` in 2,069 of 200,000 rows by at most 3.6e-15: the default fast
  float parser of `pd.read_json`; `precise_float=True` removes it. Invisible in a printout, fatal to
  an equality check or a hash.
- `idle_min` (nullable integer) comes back as float with NaN from CSV and JSON Lines.
- The DuckDB query on the file and on the in-memory Arrow table give the same top five stations
  (ST18, ST36, ST20, ST06, ST09 in the full run).

Expected recommendation: Parquet for the hand-over to analysts; JSON Lines for an append-only
log from chargers (one record per line, appendable, readable by any tool) with a declared schema;
CSV only with the dialect and a written schema beside it.

## Lab 1.2 · Six damaged files

| File | Code | Evidence | Repair |
|---|---|---|---|
| station_register_legacy.csv | A | UTF-8 cannot decode single high bytes (e3 c8 e4 ...) where Arabic names should be; CRLF | decode as cp1256 |
| tariffs.csv | B | starts with ef bb bf; first column reads as "﻿tariff_code" | decode as utf-8-sig |
| station_notes.csv | C | valid UTF-8 but Arabic shows as pairs of other Arabic letters (ط§ظ„...) | `text.encode("cp1256").decode("utf-8")` |
| maintenance_log.txt | D | starts with ff fe; a 00 after every ASCII letter | decode as UTF-16, tab-separated |
| vendor_a_sessions.csv | E | a constant 180 minutes ahead of the platform's UTC | localise to +03:00, convert to UTC |
| vendor_b_sessions.csv | F | 120 minutes ahead before 25 October 2026, 60 after; seq 9 and 10 end before they start; seq 11 starts before seq 10 | localise to CET; in the repeated hour choose fold by seq order |

Evidence threshold for LO2: five of six codes right. The commonest confusion is A with C (both
show "wrong" Arabic): A fails to decode as UTF-8, C decodes without error but reads as nonsense.
Second commonest: E with F; the cure is to compare with the platform on two different days.
Results: all 40 register names match; 3 tariff rows; 12 notes; 16 log rows; 30 + 30 sessions equal
the platform's UTC times; Vendor B negative durations 2 before, 0 after.

## Lab 2.1 · Every record, exactly once

Mock fault schedule (by request number of each fresh mock): 3 → 429 (Retry-After 2), 6 → 503,
9 → 500 with an HTML body, 13 → 429 (Retry-After 1).

- Well-behaved mock: 12 pages, 1,200 new records.
- Plain client against the faults: stops at the 429 (KeyError on the missing `data` key) after
  keeping 200 records. Point out that the crash is in the parsing, far from the cause.
- With retries: 16 requests, statuses 200, 429, 500, 503; 4.162 s waited on the fake clock.
- Interrupted after page 7, then resumed: 1,200 records, 1,200 unique, 0 missing; page 7 fetched
  twice and its 100 records dropped as duplicates; 17 requests. No file holds the token.
- Offset endpoint with 20 arrivals inserted before the third page: 1,220 ids received, 20
  repeated, all 20 new sessions missed.
- Public API (World Bank Indicators API, series EG.ELC.ACCS.ZS, year 2023, live on 25 November
  2026): licence CC BY-4.0 read from the series metadata; 266 rows in 6 pages of 50, equal to the
  API's own total; 263 with a value. Nothing of it is committed. Its counts may change when the
  publisher revises the series: the check compares with the API's own total, not a fixed number.

Segregation of duties: the client's author does not hold the production token; the token is
issued per person by the platform owner, kept in the environment, and revoked by the owner.

## Lab 2.2 · Flatten, write, validate

- 12 raw pages, 1,200 records, all valid against `schema/session.schema.json`.
- Sessions table 1,200 rows; readings table 4,187 rows; 14 day partitions (UTC days 2026-10-18 to
  2026-10-31); written schemas equal the declared ones.

| Batch | Seeded defects | Decision | Loaded | Quarantined |
|---|---|---|---|---|
| batch_01 | none | load | 200 | 0 |
| batch_02 | CS-20018 missing_field (energy_kwh); CS-20065 wrong_type ("12,5"); CS-20151 no_offset | load | 197 | 3 |
| batch_03 | CS-30041 duplicate_key (two rows); CS-30078 out_of_range (−3.2); CS-30089 out_of_range (912.0); CS-30100 end_before_start; CS-30134 unknown_station (ST47) | load | 194 | 6 |
| batch_04 | every record renames energy_kwh to energy | reject (schema_break:energy_kwh) | 0 | 0 |
| batch_05 | 20 records without offsets (10%) | reject (above 5%) | 0 | 20 |

Rows loaded in all: 591. `solutions/batch_key.json` lists every defect. The 5% and 90% thresholds
are the case organisation's own rules, not a standard.

Segregation of duties: the loader quarantines and reports; the station team (the data owner)
corrects and resends; a second person, not the loader's author, approves any release of
quarantined rows.

## Capstone

`labs/capstone/make_batch.py --seed <n> --label <letter>` writes a batch folder and, separately,
its key. The seed draws the scenario, the encoding and the ids at random, so the batch does not
reveal it; the key names the scenario. The practice batch P (seed 1) is in
`labs/capstone/practice/`. The assessor chooses other seeds on the day, keeps them and the keys,
and hands batches over by letter.
