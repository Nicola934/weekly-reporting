Weekly Auto-Reporting System (Week 7 Capstone)

A CLI-first automation system that ingests survey files, cleans and deduplicates data, computes KPIs, generates report artifacts, writes logs and health status, and optionally emails results with attachments.
Designed to run unattended via Windows Task Scheduler.

What this project does

On each run, the system:

Scans an inbox folder for new input files (CSV / Excel / JSON)

Cleans and deduplicates records

Computes KPIs (satisfaction, recommendation, usage, etc.)

Writes report artifacts to output/

Archives processed inputs

Updates logs and a health/status file

Optionally emails reports as attachments

Project structure (simplified)
weekly_auto_reporting/
├── weekly_report/        # Python package (pipeline, CLI, logic)
├── data/
│   ├── inbox/
│   ├── processed/
│   └── failed/
├── output/               # reports + health file
├── logs/                 # app.log
├── config.json
├── pyproject.toml
└── README.md


Runtime folders are created automatically if missing.

Requirements

Python 3.10+

Windows (PowerShell examples shown)

Dependencies:

pandas

openpyxl (for Excel inputs)

Installation (recommended: virtual environment)

From the project root:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .


Verify installation:

python -m weekly_report --help

Configuration (config.json)

Edit config.json to match:

input/output directories

input file patterns

column names (service, region, satisfaction, recommendation, etc.)

email settings (disabled by default in the example; configure actual addresses locally)

Input files must be placed in:

data/inbox/


Supported formats:

CSV

XLSX

JSON

Running the system
Validate configuration
python -m weekly_report validate-config

Dry run (safe simulation)
python -m weekly_report run --dry-run

Full run
python -m weekly_report run

Verbose debug logging

Global flags must come before the command:

python -m weekly_report --verbose run --dry-run

Check last run status
python -m weekly_report status

Outputs

After a run, check:

Reports: output/

Logs: logs/app.log

Health/status file: output/health.txt

The health file is updated when processing begins or finishes; the log file records configured activity.

On a normal run with inputs, originals are moved to data/processed/ and cleaned/deduplicated outputs are written to output/. Dry-run mode does not move originals or send email, but **does** generate local outputs and health/log files.

Scheduling (Windows Task Scheduler)

Recommended execution (no activation required):

Program/script

C:\path\to\project\.venv\Scripts\python.exe


Arguments

-m weekly_report run


Start in

C:\path\to\project


This ensures relative paths and config.json resolve correctly.

Exit codes (automation-friendly)

0 — success

1 — bad CLI arguments

2 — pipeline failure

3 — configuration error

Email setup (optional)

The public config.json uses placeholder addresses and has email disabled by default. To send real messages, set email.enabled to true, configure real addresses in a local config file, and provide REPORT_SMTP_USER and REPORT_SMTP_PASS environment variables. Never commit credentials or private client addresses. Use --config to select your local configuration. Dry-run does not require SMTP credentials and never connects to an SMTP server.

Verification note

The repository contains implementation for data ingestion, cleaning, KPI calculation, reports and optional SMTP delivery. Production operation and unattended scheduling should be validated in the intended environment; documentation is not a guarantee of deployment.

Release & packaging

This project is packaged using pyproject.toml and published as a tagged release.

Current release: v0.1.0

Assets available via GitHub Releases (wheel + source)

License

MIT
