
# Command Console

Minimal Flask dashboard for one‑click running of internal automation scripts. Dark, tabbed UI. Supports Python and PowerShell. All config lives in `.env`—no hardcoded paths.

## What it does
- Renders tabs (e.g. `income`, `general`) and buttons per script.
- Runs Python/PowerShell via `subprocess` and shows stdout/stderr in the page.
- Reads everything from `.env` (`SCRIPTS_JSON`, `GROUPS`, `ACTIVE_TAB`, `DEBUG`).

## Requirements
- Python 3.10+
- Packages: `Flask`, `python-dotenv`
- Windows-friendly (PowerShell supported), but Python scripts work cross‑platform.

Install:
```bash
pip install flask python-dotenv
