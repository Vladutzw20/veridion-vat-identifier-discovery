# Data

Data and checks as of October 2026.

Everything here is small enough to keep in git, except the raw files listed under
[Raw data (not in git)](#raw-data-not-in-git). File names are kept as in the research log
(`docs/research_log.md`), which is in Romanian, so column names are Romanian too
(`nume` = name, `cp` = postcode, `tva` = VAT, `da`/`nu` = yes/no, `lipsa` = missing).

All identifiers (VAT numbers, Companies House numbers) are stored as text: reading them as numbers drops
leading zeros.

HMRC check timestamps (`data_ora`, `data_ora_bst`) are kept at month resolution only (`2026-10`).

## `samples/` — how each sample was drawn

| File | Rows | Produced by | Description |
|---|---|---|---|
| `set_explorare_grup4.csv` | 12 | `notebooks/01_companies_house_exploration.ipynb` | First exploratory sample of "group 4" companies (accounts category FULL / MEDIUM / GROUP / AUDIT EXEMPTION SUBSIDIARY). |
| `set_explorare_endole.csv` | 30 | `notebooks/03_endole_sample.ipynb` | Random sample of 30 group-4 companies (seed 42) used for the Endole test. |
| `cc_pas2_fisiere_alese.csv` | 3 | `notebooks/05_cc_step2_from_number_wet.ipynb` | The 3 WET files drawn at random (seed 42) from the 100,000 in `CC-MAIN-2026-39`. |
| `fat_esantion_30.csv` | 10 | `notebooks/07_find_a_tender.ipynb` | Find a Tender attempt 2 (one supplier per contract, CPV 85 excluded, 1,000 contracts): only 10 eligible. Attempt 1 was overwritten by this file (see research log). |
| `fat_esantion_30_v3.csv` | 30 | `notebooks/07_find_a_tender.ipynb` | Find a Tender attempt 3: 30 suppliers, one per contract, Jan–Sep 2026 award notices, CPV 85 and .gov/.ac/.nhs sites excluded, seed 42. Column `domeniu_verificat_manual` is the manual domain check (`da` / `grup` / `nu` / `neverificat`). |

## `results/` — outputs of each method

| File | Rows | Produced by | Description |
|---|---|---|---|
| `cc_pas1_domenii_v1.csv` | 12 | `04_cc_step1_from_company` | Common Crawl Step 1, code v1 (the notebook writes `cc_pas1_domenii.csv`; the file was renamed afterwards). |
| `cc_pas1_domenii_v2.csv` | 2 | `04_cc_step1_from_company` | Step 1, v2. |
| `cc_pas1_v3_laine.csv` | 1 | `04_cc_step1_from_company` | Step 1, v3 test on Laine Theatre Arts (VAT only in a PDF). |
| `cc_pas1_v3_toate.csv` | 12 | `04_cc_step1_from_company` | Step 1, v3 on all 12 companies. |
| `cc_pas1_v3_retry.csv` | 2 | `04_cc_step1_from_company` | Step 1, v3 retry of companies that hit index errors (504). |
| `cc_pas2_candidati.csv` | 165 | `05_cc_step2_from_number_wet` | Every regex match in the 3 WET files, with checksum result and context. |
| `cc_pas2_statistici.csv` | 3 | `05_cc_step2_from_number_wet` | Per-WET-file stats: size, download / processing seconds, pages, `.uk` pages, pages with the word "VAT", matches. |
| `fat_esantion_30_v3_verificat_ch.csv` | 30 | `07_find_a_tender` | Find a Tender CH numbers joined to Companies House (name and postcode comparison). |
| `cc_fat_rezultat_firme.csv` | 26 | `08_cc_on_fat_sample` | Common Crawl run on the Find a Tender sample: one row per company (domain status, pages in index, pages read, VAT found, seconds). |
| `cc_fat_candidati.csv` | 5 | `08_cc_on_fat_sample` | The 5 VAT numbers found in that run, with URL and context. |
| `eori_pas2_wet.csv` | 1 | `09_eori_check` | EORI numbers found in the same 3 WET files as Step 2. |

## `hmrc_checks/` — manual HMRC verifications

The HMRC production API needs a registered organisation, so real numbers were checked by hand on the
HMRC web page "Check a UK VAT number". The automated check exists only against the HMRC Sandbox
(`notebooks/02_hmrc_api_sandbox.ipynb`).

| File | Rows | How it was made | Description |
|---|---|---|---|
| `urma_endole_30.csv` | 30 | manual (template created by `03_endole_sample`) | Endole trail: VAT shown on Endole, HMRC result, HMRC name/postcode, category, estimated minutes, notes. Columns `marime_endole`, `cautare_grup`, `adresa_ch`, `evaluare_lipsa_asistent` added during the step (the last one is the AI assistant's assessment, not verified at HMRC). |
| `explorare_grupuri_endole.csv` | 7 | manual | Companies in the same group as sample companies (outside the sample), checked on Endole and HMRC. |
| `hmrc_transcriere.csv` | 36 | HMRC pages copied by hand, transcribed by the AI assistant | HMRC results for Common Crawl Step 2. |
| `cc_pas2_verificare_hmrc.csv` | 108 | `05_cc_step2_from_number_wet` + manual | All 108 unique Step 2 numbers, CH match, and HMRC result for the 31 checked (random order, seed 42). |
| `cc_pas2_rezultat_hmrc.csv` | 31 | `05_cc_step2_from_number_wet` | The 31 checked numbers with classification and attribution. |
| `hmrc_transcriere_fat.csv` | 5 | HMRC pages transcribed by the AI assistant | HMRC results for the 5 numbers found on the Find a Tender sample. |

## `registre/` — public spending and procurement files (evidence)

| File | Source | Notes |
|---|---|---|
| `dorset_2026_06.csv` | Dorset Council, Payments to suppliers over £500: <https://www.dorsetcouncil.gov.uk/w/payments-to-suppliers-over-500> | June 2026. Not UTF-8 (the notebook reads it as Latin-1). On one attempt the site refused access from Romania ("This page is unavailable") while the AI assistant's fetch, also from outside the UK, worked; a later attempt worked. |
| `kirklees_2026_06.xlsx` | Kirklees Council, Expenditure data: <https://www.kirklees.gov.uk/beta/information-and-data/expenditure-data.aspx> | June 2026. |
| `find_a_tender_scheme.json` | Find a Tender OCDS API (see below) | Supplier identifier schemes counted over 500 award notices (Sep 2026): 1,480 supplier appearances; `LIPSĂ` = missing. |

## Raw data (not in git)

| File | How to get it |
|---|---|
| `BasicCompanyDataAsOneFile-2026-09-01.csv` (2.8 GB) / `.zip` (0.5 GB) | Companies House "Free Company Data Product", single-file version, snapshot of 2026-09-01: <https://download.companieshouse.gov.uk/en_output.html> [CHECK: the URL is not recorded in the research log]. Unzip into `data/`. |
| `wet/` | The 3 WET files listed in `samples/cc_pas2_fisiere_alese.csv`, from `https://data.commoncrawl.org/<path>`. `05_cc_step2_from_number_wet` downloads them itself if missing (~65 MB each). |
| `registre/fat_award_2026_01_09.jsonl` | 6,000 award notices, Jan–Sep 2026, from the Find a Tender OCDS API `https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages` (`stages=award`, `limit=100`). `07_find_a_tender` downloads it if missing; expect HTTP 429 with `Retry-After: 120` roughly every 10 pages. Licence: Open Government Licence v3. |
| `firme_probabil_import_export.csv` (147 MB) | Derived, not raw: written by `03_endole_sample` (SIC goods / import-export filter over the whole CH file). |

## Data sources and licences

- **Companies House** (bulk company data): public data from Companies House [CHECK licence wording].
- **Dorset Council, Kirklees Council** (payments over £500) and **Find a Tender** (OCDS API):
  Contains public sector information licensed under the Open Government Licence v3.0.
- **HMRC** "Check a UK VAT number": results were checked by hand on the public service.
- **Common Crawl** (`CC-MAIN-2026-39`): short text excerpts around VAT numbers are kept for research
  purposes only; the original pages belong to their owners.
- **Endole**: used for manual checks only. Data shown on Endole is not redistributed here; the
  trail keeps only Companies House fields and my own HMRC checks.
