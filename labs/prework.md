# Pre-work before Day 1

45 minutes, on your own, before the workshop. **AI policy: AI-off.** Work from the reading and
your own reasoning; the point is to find out what you can already read in a file, so the
assistant stays closed. Bring your answers to Day 1: the first session starts from them.

## Part 1 · The reading (15 minutes)

Read two principles of the National Data Management Office's Open Data Policy (National Data
Governance Policies, version 1 of 5/5/2020), in either language:

- English: <https://sdaia.gov.sa/en/SDAIA/about/Documents/OpenDataPolicy.pdf>
- العربية: <https://sdaia.gov.sa/ar/SDAIA/about/Documents/OpenDataPolicyAr.pdf>

Read **principle 2** (open format and machine-readable) and **principle 7** (open data licensing).
Then write one or two lines for each question:

1. Principle 2 names some widely used formats. Which of them keeps the type of a column (number,
   date, text) inside the file, and which leaves the type to whoever reads it?
2. "Machine-readable" is more than "a file a program can open". Name one thing a publisher would
   have to state, beyond the format, for a program to read a CSV file right the first time.
3. Principle 7 ties use to a licence. Where would you look for the licence of a dataset you pull
   from an API, and what would you record next to the data you keep?

## Part 2 · The drill (30 minutes)

Each item shows what a file holds or what a reader printed. Say what you see and what you would
do. The examples are deliberately not the ones in the labs.

1. A text file starts with the bytes `ef bb bf`. What are they, and what happens to the first
   column's name if a reader does not expect them?
2. A product list written in UTF-8 contains the word café. A colleague's tool shows it as `cafÃ©`.
   Was the file damaged, or was it read with the wrong encoding? What would you try first?
3. The same word shows as `caf?` in a second file, and the bytes behind the `?` are `3f`. Can the
   original letter be recovered from this file?
4. A CSV line reads `ST-Q7;12,5;2026-05-04`. Name the delimiter and the decimal mark. What does a
   reader that assumes commas make of the line?
5. A log written in a zone that moves its clocks forward one hour at 02:00 on 29 March 2026
   records a session that started at `2026-03-29 02:30`, with no offset. What is wrong with that
   time?
6. A log from another zone, where the clocks go back from 02:00 to 01:00 on 1 November 2026,
   records a session that started at `2026-11-01 01:40`. How many moments could that be, and what extra column in the log would
   let you tell which?
7. Two exports of the same meter give one reading as `7500` and as `7.5`, both in a column named
   `energy`. What is the likely cause, and where should the answer be written down?

## Answers

Check your answers only after writing them.

Part 1. (1) CSV leaves every type to the reader; JSON keeps numbers, text and true or false but has
no date type; XML and XLS can carry types when a schema or the cell format says so. (2) Any of: the
encoding, the delimiter and quote character, the decimal mark, the time zone or offset of times,
the units of each measure. (3) In the API's documentation or its metadata endpoint, and in the
portal's terms; record the licence name, where it was read and when, beside the data.

Part 2. (1) The UTF-8 byte order mark; a reader that does not expect it puts it in front of the
first column's name, so a lookup by that name fails. (2) The file is fine: it was decoded with a
single-byte code page instead of UTF-8. Decode the same bytes as UTF-8. (3) No: the writer
replaced the letter with a question mark when it saved, so the information is gone from this file;
ask for the source again. (4) Semicolon delimiter, decimal comma; a comma-assuming reader sees two
fields, `ST-Q7;12` and `5;2026-05-04`. (5) That local time never happened: the clock jumped from
02:00 to 03:00. Ask the vendor what their device does in the gap rather than guessing. (6) Two
moments, an hour apart; a sequence number, an offset column or a UTC column would decide it. (7)
Different units, watt-hours and kilowatt-hours; the unit belongs in the column's name or in the
declared schema, so the next reader does not have to guess.
