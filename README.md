# 🧬 ClinicalTrials.gov Biotech Intelligence ETL Pipeline

An automated, fault-tolerant Python ETL (Extract, Transform, Load) pipeline that extracts global clinical study records from the **U.S. National Library of Medicine (ClinicalTrials.gov REST API v2)**, flattens deeply nested 4-layer JSON structures using **Pandas**, filters for large-scale active or completed studies, and loads validated records into a **MySQL** database via **SQLAlchemy**.

---

## 🏗️ Architecture Overview

This repository implements a modular 5-file Data Engineering standard:

* **`config.py` (The Vault):** Centralizes the ClinicalTrials.gov v2 endpoint (`pageSize=50`) and network timeout settings (`TIMEOUT = 10`).
* **`extract.py` (The Ironclad Harvester):** Manages HTTP requests using a resilient `requests.Session()` mounted with a `urllib3` `Retry` adapter (`total=5`, `backoff_factor=1`) to automatically recover from rate limits (`429`) and transient server errors (`500`, `502`, `503`, `504`).
* **`transform.py` (The Blacksmith):** 
  * Unpacks deeply nested `protocolSection` sub-modules (`identificationModule`, `statusModule`, `sponsorCollaboratorsModule`, `conditionsModule`, and `designModule`) using defensive `or` fallback chaining to prevent `KeyError`, `TypeError`, and `IndexError` exceptions on missing array/dictionary fields.
  * Drops records with null patient counts, casts `enrollment_count` to integers, and enforces a Quarantine Gate keeping only trials with a status in `["RECRUITING", "COMPLETED"]` and `enrollment_count >= 100`.
* **`load.py` (The Vault Keeper):** Reads database credentials from environment variables via `python-dotenv`, URL-encodes special characters in passwords with `urllib.parse.quote_plus`, idempotently provisions the `biotech_vault` MySQL database, and writes clean records to the `major_clinical_trials` table.
* **`main.py` (The Orchestrator):** Coordinates the end-to-end ETL workflow with DataFrame validation gates (`clean_df is not None and not clean_df.empty`), top-level exception handling (`sys.exit(1)`), and dual-stream logging (`stdout` + UTF-8 `pipeline.log`).

---

## 📊 Database Schema (`major_clinical_trials`)

| Column | Type | Description |
| :--- | :--- | :--- |
| `nct_id` | `VARCHAR` | Unique ClinicalTrials.gov identifier (`nctId`) |
| `full_name` | `VARCHAR` | Lead organization or hospital full name (`organization.fullName`) |
| `title` | `TEXT` | Brief study title (`briefTitle`) |
| `status` | `VARCHAR` | Trial recruitment status (`RECRUITING` or `COMPLETED`) |
| `sponsor_name` | `VARCHAR` | Primary lead sponsor (`leadSponsor.name`) |
| `primary_condition` | `VARCHAR` | Primary disease or medical condition evaluated |
| `primary_phase` | `VARCHAR` | Clinical trial phase (defaults to `"NA"` for observational studies) |
| `enrollment_count` | `INT` | Total patient enrollment (`>= 100`) |

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **HTTP & Resilience:** `requests`, `urllib3`
* **Data Transformation:** `pandas`
* **Database & ORM:** MySQL, `SQLAlchemy`, `mysql-connector-python`
* **Environment & Observability:** `python-dotenv`, Python `logging`

---

## ⚙️ Setup & Execution

### 1. Clone the Repository
```bash
git clone [https://github.com/VINAMRA16/biotech-clinical-trials-etl.git](https://github.com/VINAMRA16/biotech-clinical-trials-etl.git)
cd biotech-clinical-trials-etl
