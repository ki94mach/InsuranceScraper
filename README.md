# Insurance Scraper

Python tool that scrapes Iranian insurance websites (Khadamat, Taamin) for generic drug codes, processes results, merges history, and optionally updates a Google Sheet for supply-chain review. Generic codes for routine runs are loaded from a triple-price Excel file (`TriplePrice`).

## Requirements

- **Windows** (primary environment; Selenium uses Firefox locally)
- **Python 3.10** via Conda (see `environment.yml`)
- **Mozilla Firefox** installed
- **GeckoDriver** on `PATH`, compatible with your Firefox version
- Network access to:
  - `https://mdp.ihio.gov.ir/` (Khadamat portal and file download)
  - Taamin / Khadamat scrape targets (see `src/pkg/scraper.py`)
  - Triple-price source (currently a public Dropbox URL in `src/pkg/tripleprice.py`)
  - Google APIs (routine modes that update Sheets)

## Quick start

```powershell
git clone <repository-url>
cd InsuranceScraper

conda env create -f environment.yml
conda activate Insurance

# Obtain src/data from your team (not in git) — see "Local data" below
# Unzip handover archive into src\ so you have src\data\...

cd src
python main.py
```

Always run commands from the **`src`** directory. Paths such as `data/KhadamatData.csv` and `data/credentials.json` are relative to the current working directory.

## Project layout

```
InsuranceScraper/
├── environment.yml          # Conda env "Insurance"
├── requirements.txt         # Exported conda spec (optional)
├── README.md
└── src/
    ├── main.py              # Interactive CLI
    ├── auto_job.py          # Non-interactive Taamin example
    ├── insurance_package.dtsx   # SSIS package (separate from Python CLI)
    ├── data/                # Local only — gitignored
    └── pkg/
        ├── scraper.py       # Selenium crawlers
        ├── processing.py    # HTML → cleaned DataFrames
        ├── manager.py       # CSV history, analysis, Google Sheets
        ├── tripleprice.py   # Download & parse triple-price Excel
        ├── khadamat.py      # Khadamat reference file download
        └── mosallah.py      # Mosallah utilities (optional)
```

## Local data (not in git)

Everything under `src/data/` is ignored by git (see `.gitignore`). After cloning, you need a copy of that folder from whoever maintains the project.

**Handover:** Ask for the `data` folder (or an approved shared copy). Do **not** commit `data/` or zip archives that contain secrets. `*.zip` is gitignored.

### Expected files

| File | Purpose |
|------|---------|
| `data/credentials.json` | Google service account for Sheets API |
| `data/KhadamatData.csv` | Khadamat scrape history (routine merge) |
| `data/TaaminData.csv` | Taamin scrape history (routine merge) |
| `data/Khadamat_file.csv` | Khadamat reference export (utility + processing) |
| `data/KhadamatGenericBrand.csv` | Khadamat generic/brand mapping |
| `data/Khadamat_raw.csv`, `data/Taamin_raw.csv` | Raw scrape outputs (routine) |
| `data/Mosallah_file.csv` | Mosallah reference (if using Mosallah paths) |
| `data/batch/generic_codes.csv` | Batch mode input (`generic_code` column) |
| `data/batch/<jalali-date>/` | Batch run outputs (created by the app) |

Treat `credentials.json` as confidential. Share it only through company-approved channels.

### Google Sheets

Routine options **1–3** call `DataManager.google_sheet_update()`, which:

- Uses `data/credentials.json`
- Opens workbook **"Insurance Update"**
- Updates the worksheet named after the website (`Khadamat`, `Taamin`, etc.)

The service account must have access to that spreadsheet.

## Interactive menu (`main.py`)

| Option | Description | Triple price | History CSVs | Google Sheet |
|--------|-------------|--------------|--------------|--------------|
| **1** | Khadamat + Taamin | Yes | Yes | Yes |
| **2** | Khadamat only | Yes | Yes | Yes |
| **3** | Taamin only | Yes | Yes | Yes |
| **4** | Download Khadamat file only | No | No | No |
| **5** | Batch scrape (pick sites) | No | No | No |
| **Q** | Quit | — | — | — |

**Routine (1–3):** Downloads Khadamat reference data, loads generic codes from triple price, scrapes selected sites, merges into `data/*Data.csv`, compares with triple price, updates Google Sheet.

**Batch (5):** Reads codes from `data/batch/generic_codes.csv`, writes results under `data/batch/<today-jalali>/` without history merge or Sheet updates.

## Automation

`src/auto_job.py` runs a fixed Taamin pipeline (Khadamat file download → triple price → scrape → storage → analysis → Sheet). Run from `src`:

```powershell
python auto_job.py
```

## Triple price input

`TriplePrice.download_file()` in `src/pkg/tripleprice.py`:

1. Downloads `sc-fr-008.xlsx` (currently via a public Dropbox `dl=1` link)
2. Parses sheet 1 into a DataFrame with column `generic_code` (5-digit zero-padded strings) and Persian columns used in `DataManager.analysis()`

Downstream code (`main.py`, `WebScraper`, `DataProcessing`, `DataManager`) only depends on that DataFrame shape—not on Dropbox specifically.

### Migrating to an internal URL (future)

When moving off Dropbox to a corporate file URL with **Windows integrated authentication**:

- Change only the download step in `TriplePrice` (keep `_process_data()` if the Excel layout is unchanged)
- Use something like `requests-negotiate-sspi` with `HttpNegotiateAuth()` on Windows
- Configure the URL via environment variable (e.g. `TRIPLE_PRICE_URL`), not hardcoded secrets
- Run as a domain user who can open the URL in a browser; scheduled tasks need an appropriate service account

No changes are required in `main.py` or the scraper if `download_file()` still returns the same columns.

## Optional: DistCore terminal UI

If [DistCore](https://github.com/your-org/DistCore) is installed alongside this repo, set:

```powershell
$env:DISTCORE_SRC = "C:\path\to\DistCore\src"
```

Otherwise the CLI uses plain text prompts (built-in fallback in `main.py`).

## Handover checklist (new developer / PR)

1. Clone the repository and create the Conda env (`Insurance`).
2. Copy `src/data/` from the previous maintainer (not included in the PR).
3. `cd src` and run `python main.py`.
4. **Smoke test:** Option **5** (batch) or **4** (Khadamat file only) to verify Firefox and network without Sheets.
5. **Full routine test:** Option **3** (Taamin only) once `credentials.json` and history CSVs are in place.
6. Confirm Firefox opens and CSVs update under `data/`.

### What a pull request does *not* provide

- `src/data/` contents (credentials, history, batch CSVs)
- Conda environment (create locally from `environment.yml`)
- Firefox / geckodriver setup
- Google Sheet sharing for the service account

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `FileNotFoundError` for `data/...` | Running from repo root instead of `src/`, or missing handover `data/` folder |
| Firefox / WebDriver errors | Firefox or geckodriver missing or version mismatch |
| `Failed to download the file` (triple price) | Dropbox link expired, or network blocked |
| Google Sheets / `gspread` errors | Missing `credentials.json`, wrong path, or sheet not shared with service account |
| `401` on future internal triple-price URL | Windows auth not configured; run as domain user on VPN |

## Security notes

- Never commit `src/data/`, `credentials.json`, or zip files containing them.
- `*.zip` is listed in `.gitignore` to avoid accidental commits of handover archives.
- Rotate the Google service account key if `credentials.json` is exposed.

## Related assets

- **`insurance_package.dtsx`**: SQL Server Integration Services package for CSV import workflows; separate from the Python CLI documented above.
