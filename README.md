# T078-PS-056: Shift Roster and Overtime Engine with Labour-Law Hours and Swaps

This project is a Python-based backend engine that automates employee shift scheduling and workforce management. It generates employee rosters, processes shift swap requests, checks attendance records, identifies scheduling and labour-hour related issues, and calculates monthly allowances.

The project reads employee, shift, demand, punch and other input data from CSV files and generates structured output reports.

**Team T078:**
- Niriksha N (1AT24CG056)
- Neeha Taj (1AT24CG055)

## What it does

The engine performs four main operations:

1. **Shift Roster Generation:** Creates employee shift schedules based on staffing requirements and scheduling rules, including weekly offs.
2. **Shift Swap Processing:** Validates employee shift swap requests and records approved or rejected requests.
3. **Attendance and Punch Processing:** Processes employee punch-in and punch-out records and identifies attendance-related issues.
4. **Monthly Allowance Calculation:** Calculates employee monthly allowances based on the available shift and work information.

## Requirements

- Python 3.13
- Windows or any system with Python installed.

## How to run

Open the project folder in the terminal and execute:

```bash
py -m src.main --month 2026-09
```

Here, `2026-09` represents September 2026.

The program executes the different stages of the engine and generates the output reports inside the `output` folder.

## How to run the tests

Execute the following command:

```bash
py -m unittest discover -s tests -v
```

The project currently has 11 tests that pass successfully.

## Output files

The project generates five output reports:

| File | What it contains |
|---|---|
| roster.csv | Employee shift schedules, weekly offs and staffing shortfalls |
| swap_results.csv | Approved and rejected employee shift swap requests |
| punch_results.csv | Processed employee attendance and punch records |
| violations.csv | Scheduling, attendance and labour-hour related issues identified during processing |
| monthly_allowances.csv | Monthly allowance calculation details for employees |

## Project layout

| Path | Purpose |
|---|---|
| src/main.py | Main starting point that runs the project |
| src/roster.py | Generates employee shift rosters |
| src/io_utils.py | Handles input and output file operations |
| src/punches.py | Processes attendance and punch records |
| src/allowances.py | Calculates monthly employee allowances |
| src/swaps.py | Processes and validates shift swap requests |
| data/ | Contains input CSV files |
| output/ | Stores the generated reports |
| tests/ | Contains project test cases |
| T078-PS-056-sample-data/ | Contains the provided sample data |
| README.md | Project documentation |

## Input files

The project uses the following input files:

- `agents.csv` – Employee information.
- `shifts.csv` – Available shift details.
- `demand.csv` – Staffing requirements.
- `punches.csv` – Employee attendance and punch records.
- `commands.txt` – Shift swap and processing commands.
- `prior_week_hours.csv` – Previous weekly working-hour information.

## Main features

- Automated employee shift roster generation.
- Weekly off management.
- Staffing shortage identification.
- Employee shift swap validation.
- Attendance and punch record processing.
- Identification of invalid and duplicate punch records.
- Labour-hour and scheduling violation detection.
- Monthly allowance calculation.
- Automatic generation of structured CSV reports.

## Project Demo Video

Watch our five-minute project demonstration here:

[Click here to watch the Project Demo Video](https://drive.google.com/file/d/14bcrnxARexc18aJ7dXrkirWyfdW67MjY/view?usp=drivesdk)
## Documents

[View Decision Log](docs/docs/decision-log.md)

## Project Repository

[GitHub Repository – T078-PS-056](https://github.com/niriksha4139/T078-PS-056)
