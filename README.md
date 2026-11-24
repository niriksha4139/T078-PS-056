# T078-PS-056 — Shift Roster and Overtime Engine

## Project Overview

The Shift Roster and Overtime Engine is a Python-based command-line application designed to manage employee shift scheduling, attendance, overtime, shift swaps and monthly allowances.

The system processes employee and shift data, generates monthly rosters, validates shift swaps, calculates working hours and overtime, identifies attendance violations and prepares monthly allowance reports.

## Features

- Monthly employee roster generation.
- Shift allocation based on employee and demand data.
- Shift swap request processing and validation.
- Attendance and punch-in/punch-out processing.
- Calculation of regular working hours and overtime.
- Night working-hour calculation.
- Detection and reporting of attendance and labour-rule violations.
- Calculation of overtime pay, night allowance, weekly-off premium and meal allowance.
- CSV-based input and output reports.

## Technologies Used

- Python 3
- CSV file handling
- Python standard library
- Visual Studio Code

## Project Structure

```text
T078-PS-056/
├── data/
├── output/
├── src/
│   ├── main.py
│   ├── roster.py
│   ├── io_utils.py
│   ├── punches.py
│   ├── allowances.py
│   └── swaps.py
├── tests/
├── T078-PS-056-sample-data/
├── README.md
└── .gitignore
```

## Requirements

- Python 3.10 or later.
- Visual Studio Code or any Python-compatible editor.

No third-party Python packages are currently required.

## How to Run

Open PowerShell in the project root directory.

Run the complete project for September 2026:

```bash
py -m src.main --month 2026-09
```

## Run Unit Tests

Execute the following command:

```bash
py -m unittest discover -s tests -v
```

## Input Files

The application uses CSV files stored in the `data/` directory, including:

- agents.csv
- shifts.csv
- demand.csv
- punches.csv
- commands.txt
- prior_week_hours.csv

## Generated Output Files

The application generates the following reports in the `output/` directory:

| File | Description |
|---|---|
| roster.csv | Monthly employee shift roster |
| swap_results.csv | Shift swap processing results |
| punch_results.csv | Employee attendance and working-hour results |
| violations.csv | Detected attendance and rule violations |
| monthly_allowances.csv | Monthly employee allowance statement |

## Testing and Execution Status

- Unit tests executed successfully: 11 passed.
- Monthly roster generation completed.
- Shift swap processing completed.
- Attendance and punch processing completed.
- Monthly allowance calculation completed.
- All five output CSV reports generated successfully.

The project has a working end-to-end processing pipeline. The existing unit tests cover selected roster and punch calculation functions; further testing of all business rules and edge cases may still be required.
