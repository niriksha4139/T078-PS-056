# T078-PS-056 – Project Decision Log

## 1. Introduction

This document records the important technical and design decisions made during the development of the Shift Roster and Overtime Engine. It explains the reasons behind these decisions and how they support the project requirements.

## 2. Decision Records

### DEC-01: Use Python as the Programming Language

**Decision:** Python was selected for developing the project.

**Reason:** Python provides simple syntax, useful built-in libraries and support for handling CSV files and implementing scheduling logic.

**Status:** Accepted

### DEC-02: Use CSV Files for Input and Output

**Decision:** CSV files were selected for storing input data and generated reports.

**Reason:** CSV files are easy to create, read, update and share. They also make project testing easier using sample datasets.

**Status:** Accepted

### DEC-03: Use a Modular Project Structure

**Decision:** The project was divided into separate Python modules such as `roster.py`, `swaps.py`, `punches.py`, `allowances.py` and `io_utils.py`.

**Reason:** Separating responsibilities makes the code easier to understand, maintain, test and debug.

**Status:** Accepted

### DEC-04: Generate Monthly Employee Rosters

**Decision:** The system generates employee rosters for a selected month.

**Reason:** Monthly roster generation helps organize employee shifts and staffing requirements over a defined period.

**Status:** Accepted

### DEC-05: Validate Shift Swap Requests Before Approval

**Decision:** Every shift swap request is checked against employee details and scheduling rules before approval.

**Reason:** This helps prevent invalid shift exchanges and ensures that both employees satisfy the configured scheduling requirements.

**Status:** Accepted

### DEC-06: Apply Configurable Working-Hour Rules

**Decision:** The system uses configured limits for weekly working hours, overtime, rest periods and night shifts.

**Reason:** These rules help identify scheduling issues and calculate working hours consistently.

**Status:** Accepted

### DEC-07: Process Attendance Using Punch Records

**Decision:** Employee attendance is calculated using punch-in and punch-out records.

**Reason:** This allows the system to calculate working hours, identify attendance issues and determine overtime.

**Status:** Accepted

### DEC-08: Generate Separate Output Reports

**Decision:** The system generates separate CSV reports for roster details, shift swaps, punch results, violations and monthly allowances.

**Reason:** Separate reports make the results easier to review, understand and use.

**Status:** Accepted

### DEC-09: Use Unit Testing

**Decision:** Python unit tests are used to test important project functionality.

**Reason:** Unit testing helps identify errors and check whether individual parts of the application behave as expected.

**Status:** Accepted

## 3. Conclusion

These decisions helped establish a modular, structured and testable application. They support the main objectives of the Shift Roster and Overtime Engine and make future improvements easier.

**Project:** T078-PS-056  
**Title:** Shift Roster and Overtime Engine with Labour-Law Hours and Swaps
