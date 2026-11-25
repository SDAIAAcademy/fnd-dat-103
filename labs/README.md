# Data Formats, Interfaces and Quality Checks: labs

## Quick start

- Google Colab: open a notebook from the course page; its first cell clones this repository and installs `requirements-colab.txt`.
- Locally: clone the repository, then from `labs/` run `uv sync` and open the notebooks with `uv run jupyter lab`.
- Run `00_setup_check.ipynb` first: its last line says whether you are ready.
- Copy `.env.example` to `.env` before Day 2: the mock API's token is read from there, never written in a notebook.

| Unit | Session | Notebook |
|---|---|---|
| Day 1 | Session 1 · File formats | [`D1_1_three_formats.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/fnd-dat-103/blob/main/labs/D1_1_three_formats.ipynb) |
| Day 1 | Session 2 · Text and time | [`D1_2_damaged_files.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/fnd-dat-103/blob/main/labs/D1_2_damaged_files.ipynb) |
| Day 2 | Session 1 · Interfaces | [`D2_1_api_client.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/fnd-dat-103/blob/main/labs/D2_1_api_client.ipynb) |
| Day 2 | Session 2 · Schema and validation | [`D2_2_flatten_validate.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/fnd-dat-103/blob/main/labs/D2_2_flatten_validate.ipynb) |

The notebooks are generated from the percent-format sources in `labs/_src/` by `labs/_tools/py2nb.py` (`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions to `labs/solutions/`. Edit the sources, not the notebooks.

## What is here

| Path | What it is |
|---|---|
| `prework.md` | The pre-work before Day 1: the Open Data Policy reading and a reading drill, with answers |
| `chargekit.py` | The helper module every lab imports (`import chargekit as U`): paths, quick mode, checks, the case's generators, the declared schemas, the reference versions the safety nets use |
| `mockapi.py` | The mock charge-point platform API (FastAPI) with its fault schedule |
| `prepare_data.py` | Writes `data/` from fixed seeds; run it to rebuild the data byte for byte |
| `schema/session.schema.json` | The declared JSON Schema of one session record |
| `data/` | The synthetic case data; `data/damaged/` holds the six damaged files of lab 1.2, byte-exact |
| `capstone/` | The capstone brief, the batch generator and the practice batch with its key |
| `solutions/` | The solution notebooks, the answer key and the trainer's reference capstone script |

**Quick mode.** `FDT103_QUICK=1` makes lab 1.1 use 20,000 sessions instead of 200,000; the other labs are small already. **Outputs** go to `labs/out/` (git ignores it), or to the folder named in `FDT103_OUT`.

To run a solution as a script (from `labs/`): `uv run python _src/D2_1_api_client.py`. To execute a notebook: `uv run jupyter execute solutions/D2_1_api_client.ipynb`. On a Windows computer whose system code page is not UTF-8 (an Arabic Windows uses cp1256), set `PYTHONUTF8=1` first (`$env:PYTHONUTF8 = "1"` in PowerShell): `jupyter execute` opens the notebook file with the system code page, which turns the Arabic in lab 1.2's checks into the very mojibake the lab teaches. Opening the notebooks in Jupyter Lab or Colab is not affected.

`uv.lock` pins the versions the labs were last run with; `uv sync` installs exactly those.
