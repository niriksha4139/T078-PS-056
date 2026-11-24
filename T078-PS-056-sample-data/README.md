# T078-PS-056 — Shift Roster and Overtime Engine

## 1. Project Overview

The Shift Roster and Overtime Engine is a Python-based command-line application designed to manage employee shift scheduling, attendance tracking, overtime calculations, shift swaps and monthly allowance calculations.

The system helps generate monthly employee rosters while considering labour-law-related working-hour limits, rest periods, weekly offs and overtime restrictions.

It also processes employee attendance records, identifies violations and generates monthly reports in CSV format.

## 2. Technologies Used

- Python 3.10+
- CSV files for input and output data
- Python standard library
- Visual Studio Code

No third-party Python packages are required.

## 3. Project Features

1. Employee data management.
2. Shift template management.
3. Monthly shift roster generation.
4. Skill-based employee allocation.
5. Attendance and punch processing.
6. Calculation of regular working hours and overtime.
7. Detection and reporting of attendance violations.
8. Shift swap request validation.
9. Monthly overtime and allowance calculation.
10. CSV report generation.

## 4. Shift Details

The system supports three main shift types:

| Shift | Start Time | End Time |
|---|---|---|
| MORNING | 06:00 AM | 02:00 PM |
| EVENING | 02:00 PM | 10:00 PM |
| NIGHT | 10:00 PM | 06:00 AM |

Each shift has a scheduled duration of 8 hours, including a 30-minute unpaid break, resulting in 7.5 paid hours.

## 5. Business Rules

The project is designed around the following working-hour and scheduling rules:

### Working Hour Limits
- Maximum scheduled work per day: 9 hours, including overtime.
- Weekly regular working-hour limit: 48 hours.
- Overtime may apply after 48 hours, up to the 60-hour weekly threshold.
- Work exceeding 60 hours in a week is treated as a violation.
- Quarterly overtime limit: 125 hours.

### Rest and Shift Rules
- A minimum rest period of 12 hours is required between shifts.
- A NIGHT shift must not be followed by a MORNING shift the next day.
- Maximum 7 consecutive NIGHT shifts.
- Employees who joined less than 90 days ago should not be assigned NIGHT shifts.
- Employees should receive exactly one scheduled weekly OFF day from Monday to Sunday.
- Maximum 6 consecutive working days.

### Overtime and Allowance Rules
- Overtime pay is calculated at twice the hourly basic rate.
- Hourly basic rate = Monthly basic salary / 208.
- NIGHT shift allowance: ₹200 per worked NIGHT shift.
- Night hours on non-NIGHT shifts: ₹25 per hour.
- Weekly-off work attracts a premium, with a higher premium when compensatory OFF is not provided within 14 days.
- Meal allowance: ₹100 for eligible shifts and ₹150 for eligible NIGHT shifts.

### Attendance Rules
- Punches within 10 minutes of scheduled timings may be adjusted to the schedule.
- Late arrival deductions are calculated in 15-minute blocks.
- Working less than 4 hours is treated as a half-day.
- Daily work exceeding 9 hours is flagged as a violation.

### Shift Swap Rules
- Shift swaps must be requested at least 24 hours before the earlier shift.
- Both employees must have the required skills.
- Swaps must satisfy rest-period and working-hour restrictions.
- A maximum of 4 approved swaps per employee per month is allowed.

## 6. Project Structure

```text
T078-PS-056/
│
├── src/
│   ├── main.py
│   ├── roster.py
│   ├── punches.py
│   ├── swaps.py
│   ├── allowances.py
│   └── io_utils.py
│
├── tests/
│   ├── test_punches.py
│   └── test_roster.py
│
├── data/
│   ├── agents.csv
│   ├── shifts.csv
│   ├── demand.csv
│   ├── punches.csv
│   └── commands.txt
│
├── output/
│
├── README.md
└── .gitignore
```

## 7. Input Files

The application uses CSV and command files as input.

- **agents.csv:** Contains employee details such as employee ID, grade, skills, weekly-off preference and basic salary.
- **shifts.csv:** Contains shift templates and timings.
- **demand.csv:** Contains daily employee requirements for different shifts and skills.
- **punches.csv:** Contains employee attendance punch-in and punch-out details.
- **commands.txt:** Contains shift swap requests.

## 8. Output Reports

The application generates the following reports inside the `output` folder:

| File Name | Description |
|---|---|
| roster.csv | Generated monthly employee shift roster |
| swap_results.csv | Approved and rejected shift swap requests |
| punch_results.csv | Employee attendance and working-hour calculations |
| violations.csv | Detected attendance and scheduling violations |
| monthly_allowances.csv | Monthly overtime and allowance statements |

## 9. Setup Instructions

1. Install Python 3.10 or later.
2. Open the project folder in Visual Studio Code.
3. Open the integrated terminal.
4. Ensure the required input CSV files are available inside the `data` folder.
5. No additional package installation is required.

## 10. Running the Project

Open the terminal in the project root directory.

### Run the Complete Application

```bash
py -m src.main --month 2026-09
```

This executes the complete processing pipeline:

1. Monthly roster generation.
2. Shift swap processing.
3. Attendance and punch processing.
4. Monthly allowance calculation.

### Generate Only the Monthly Roster

```bash
py -m src.main --month 2026-09 --roster-only
```

Generated reports can be found in the `output` folder.

## 11. Running Tests

Run the following command to execute the available unit tests:

```bash
py -m unittest discover -s tests -v
```

The current test suite contains 11 basic tests covering roster calculations, shift timings, night-hour calculations and time conversions.

## 12. Current Development Status

- [x] Project structure and setup
- [x] Monthly roster generation
- [x] Attendance and punch processing
- [x] Violation reporting
- [x] Basic shift swap validation
- [x] Monthly allowance calculation
- [x] Main program integration
- [x] Basic unit tests
- [ ] Complete labour-law rule validation
- [ ] Comprehensive business-rule and edge-case testing

**Note:** The application successfully executes its four main processing stages. Advanced business rules and edge cases are still undergoing verification.

## 13. Conclusion

The Shift Roster and Overtime Engine provides an automated approach to employee scheduling, attendance management, shift swap validation and allowance calculation.

By generating structured CSV reports, the application helps simplify workforce management and supports better monitoring of employee working hours and overtime.
