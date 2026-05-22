# MediSync Portal

A simple Flask-based hospital bed management portal with MySQL-backed storage.

## What it does

- Displays bed availability by ward
- Admits patients and assigns available beds
- Handles patient discharge and billing
- Generates receipts for discharged patients

## Files

- `app.py` — Flask application and route logic
- `setup_db.py` — Creates `medisync_db`, schema, and seeds bed data
- `schema.sql` — SQL schema for database creation
- `index.html` — Main app view template
- `receipt.html` — Discharge receipt template
- `.gitignore` — Excludes Python artifacts and virtual environments

## Requirements

- Python 3.10+ (or compatible)
- MySQL server

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create the database and seed beds:
   ```bash
   python setup_db.py
   ```

3. Update MySQL credentials in `app.py` if needed.

4. Run the app:
   ```bash
   python app.py
   ```

5. Open the displayed local URL in your browser.

## Notes

- The app currently uses MySQL credentials from `app.py`.
- For production, move credentials to environment variables and avoid hardcoding passwords.
