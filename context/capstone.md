---
course: "Data Formats, Interfaces and Quality Checks"
code: "FND-DAT-103"
version: "2027.1.0"
deck: "capstone"
day: 3
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/fnd-dat-103/slides/capstone.html"
---

# Data Formats, Interfaces and Quality Checks

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
