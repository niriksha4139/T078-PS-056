
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from math import ceil

from .io_utils import read_csv, read_output_csv, write_csv


def get_night_minutes(start, end):
    """Calculate minutes worked between 10 PM and 6 AM."""
    total = 0
    current_day = start.date() - timedelta(days=1)

    while current_day <= end.date():
        night_start = datetime.combine(current_day, time(22, 0))
        night_end = datetime.combine(
            current_day + timedelta(days=1), time(6, 0)
        )

        overlap_start = max(start, night_start)
        overlap_end = min(end, night_end)

        if overlap_end > overlap_start:
            total += int(
                (overlap_end - overlap_start).total_seconds() // 60
            )

        current_day += timedelta(days=1)

    return total


def hours_to_minutes(value):
    return int(round(float(value or 0) * 60))


def add_violation(violations, aid, day, violation, details):
    violations.append({
        "agent_id": aid,
        "date": day,
        "violation": violation,
        "details": details
    })


def process_punches(month):
    punches = read_csv("punches.csv")

    shifts = {
        row["shift_code"]: row
        for row in read_csv("shifts.csv")
    }

    agents = {
        row["agent_id"]: row
        for row in read_csv("agents.csv")
    }

    prior_records = read_csv("prior_week_hours.csv")
    roster = read_output_csv("roster.csv")

    roster_map = {
        (row["agent_id"], row["roster_date"]): row
        for row in roster
        if row["agent_id"] != "SHORTFALL"
    }

    results = []
    violations = []

    weekly_minutes = defaultdict(int)

    # Load previous weekly worked hours.
    for row in prior_records:
        aid = row["agent_id"]

        if aid not in agents:
            continue

        work_date = date.fromisoformat(row["work_date"])
        week_start = work_date - timedelta(
            days=work_date.weekday()
        )

        weekly_minutes[(aid, week_start)] += hours_to_minutes(
            row["worked_hours"]
        )

    # Load quarterly overtime already used.
    quarter_ot_minutes = {
        aid: hours_to_minutes(
            agent.get("quarter_ot_hours_to_date", 0)
        )
        for aid, agent in agents.items()
    }

    seen = set()

    punches = sorted(
        [
            p for p in punches
            if p["shift_date"].startswith(month)
        ],
        key=lambda p: (p["shift_date"], p["agent_id"])
    )

    for punch in punches:
        aid = punch["agent_id"]
        day = punch["shift_date"]
        key = (aid, day)

        # Reset for every punch record.
        late_deduction_minutes = 0

        if aid not in agents:
            add_violation(
                violations, aid, day,
                "VIOLATION_UNKNOWN_AGENT",
                "Agent does not exist in agents.csv"
            )
            continue

        # Validate date and timestamps.
        try:
            shift_day = date.fromisoformat(day)

            actual_in = datetime.strptime(
                punch["punch_in"], "%Y-%m-%d %H:%M:%S"
            )

            actual_out = datetime.strptime(
                punch["punch_out"], "%Y-%m-%d %H:%M:%S"
            )

        except (ValueError, TypeError):
            add_violation(
                violations, aid, day,
                "VIOLATION_INVALID_PUNCH",
                "Invalid punch date or time format"
            )
            continue

        if actual_in.date() != shift_day:
            add_violation(
                violations, aid, day,
                "VIOLATION_INVALID_PUNCH",
                "Punch-in date does not match shift date"
            )
            continue

        if actual_out <= actual_in:
            add_violation(
                violations, aid, day,
                "VIOLATION_INVALID_PUNCH",
                "Punch-out must be after punch-in"
            )
            continue

        # Duplicate check.
        if key in seen:
            add_violation(
                violations, aid, day,
                "VIOLATION_DUPLICATE_PUNCH",
                "Multiple punch records for one agent and date"
            )
            continue

        seen.add(key)

        # Check roster.
        assignment = roster_map.get(key)

        if not assignment or assignment["shift_code"] in (
            "OFF", "SWAP_OFF"
        ):
            add_violation(
                violations, aid, day,
                "VIOLATION_NO_ROSTER",
                "Punch recorded without a scheduled shift"
            )
            continue

        shift_code = assignment["shift_code"]

        if shift_code not in shifts:
            add_violation(
                violations, aid, day,
                "VIOLATION_INVALID_SHIFT",
                "Scheduled shift template does not exist"
            )
            continue

        shift = shifts[shift_code]

        scheduled_start = datetime.combine(
            shift_day,
            datetime.strptime(
                shift["start_time"], "%H:%M"
            ).time()
        )

        scheduled_end = datetime.combine(
            shift_day,
            datetime.strptime(
                shift["end_time"], "%H:%M"
            ).time()
        )

        # Handle overnight shifts.
        if scheduled_end <= scheduled_start:
            scheduled_end += timedelta(days=1)

        # Existing shift-mismatch check.
        shift_mismatch = actual_in >= scheduled_end

        if shift_mismatch:
            add_violation(
                violations, aid, day,
                "VIOLATION_SHIFT_MISMATCH",
                "Punch-in occurred at or after scheduled shift end"
            )

        # Apply 10-minute tolerance only.
        # Do not round late arrival into actual working time.
        effective_in = actual_in
        effective_out = actual_out

        if abs(
            (actual_in - scheduled_start).total_seconds()
        ) <= 600:
            effective_in = scheduled_start

        # Calculate late deduction separately.
        elif (
            actual_in > scheduled_start + timedelta(minutes=10)
            and actual_in < scheduled_end
        ):
            late_minutes = int(
                (actual_in - scheduled_start).total_seconds() // 60
            )

            late_deduction_minutes = (
                ceil(late_minutes / 15) * 15
            )

        if abs(
            (actual_out - scheduled_end).total_seconds()
        ) <= 600:
            effective_out = scheduled_end

        elapsed_minutes = int(
            (effective_out - effective_in).total_seconds() // 60
        )

        if elapsed_minutes <= 0:
            add_violation(
                violations, aid, day,
                "VIOLATION_INVALID_PUNCH",
                "Effective punch duration is not positive"
            )
            continue

        # Deduct unpaid break.
        unpaid_break = int(shift["unpaid_break_minutes"])

        break_deduction = (
            unpaid_break if elapsed_minutes >= 240 else 0
        )

        # Actual worked time is calculated independently
        # from the late deduction.
        worked_minutes = max(
            0, elapsed_minutes - break_deduction
        )

        actual_worked_hours = worked_minutes / 60

        # Daily limit: 9 hours.
        daily_violation = worked_minutes > 9 * 60

        if daily_violation:
            add_violation(
                violations, aid, day,
                "VIOLATION_DAILY",
                (
                    f"Worked {actual_worked_hours:.2f} hours; "
                    "maximum payable hours are 9"
                )
            )

        daily_payable_minutes = min(
            worked_minutes, 9 * 60
        )

        # Half-day if actual worked time is below 4 hours.
        half_day = worked_minutes < 4 * 60

        # Weekly calculation.
        week_start = shift_day - timedelta(
            days=shift_day.weekday()
        )

        week_key = (aid, week_start)
        previous_week_minutes = weekly_minutes[week_key]

        projected_week_minutes = (
            previous_week_minutes + worked_minutes
        )

        weekly_violation = projected_week_minutes > 60 * 60

        if weekly_violation:
            add_violation(
                violations, aid, day,
                "VIOLATION_WEEKLY",
                (
                    f"Weekly hours reached "
                    f"{projected_week_minutes / 60:.2f}; "
                    "maximum is 60"
                )
            )

        # Maximum payable weekly hours: 60.
        allowed_minutes = min(
            daily_payable_minutes,
            max(0, 60 * 60 - previous_week_minutes)
        )

        # First 48 hours are regular.
        regular_entitlement = min(
            allowed_minutes,
            max(0, 48 * 60 - previous_week_minutes)
        )

        # Hours above 48 and up to 60 are overtime.
        weekly_overtime_minutes = max(
            0, allowed_minutes - regular_entitlement
        )

        # Late deduction reduces regular payable hours only.
        regular_payable_minutes = max(
            0,
            regular_entitlement - late_deduction_minutes
        )

        # Quarterly overtime cap: 125 hours.
        remaining_quarter_minutes = max(
            0,
            125 * 60 - quarter_ot_minutes[aid]
        )

        overtime_minutes = min(
            weekly_overtime_minutes,
            remaining_quarter_minutes
        )

        blocked_overtime = (
            weekly_overtime_minutes - overtime_minutes
        )

        if blocked_overtime > 0:
            add_violation(
                violations, aid, day,
                "VIOLATION_QUARTERLY_OT",
                (
                    f"{blocked_overtime / 60:.2f} overtime hours "
                    "exceeded the quarterly 125-hour cap"
                )
            )

        quarter_ot_minutes[aid] += overtime_minutes

        # Update weekly ledger using actual worked time.
        weekly_minutes[week_key] += worked_minutes

        # Calculate night hours.
        night_minutes = get_night_minutes(
            effective_in, effective_out
        )

        # Assumption: NIGHT shift's unpaid break occurs
        # during the 10 PM to 6 AM period.
        # Exact break timing is not supplied in shifts.csv.
        if shift_code == "NIGHT":
            night_minutes = max(
                0, night_minutes - break_deduction
            )

        night_hours = night_minutes / 60

        results.append({
            "agent_id": aid,
            "date": day,
            "shift_code": shift_code,
            "worked_hours": round(actual_worked_hours, 4),
            "regular_hours": round(
                regular_payable_minutes / 60, 4
            ),
            "overtime_hours": round(
                overtime_minutes / 60, 4
            ),
            "night_hours": round(night_hours, 4),
            "late_deduction_hours": round(
                late_deduction_minutes / 60, 4
            ),
            "half_day": str(half_day).upper(),
            "daily_violation": str(daily_violation).upper(),
            "weekly_violation": str(weekly_violation).upper(),
            "shift_mismatch": str(shift_mismatch).upper()
        })

    # Write punch results.
    write_csv(
        "punch_results.csv",
        [
            "agent_id",
            "date",
            "shift_code",
            "worked_hours",
            "regular_hours",
            "overtime_hours",
            "night_hours",
            "late_deduction_hours",
            "half_day",
            "daily_violation",
            "weekly_violation",
            "shift_mismatch"
        ],
        results
    )

    # Write violations.
    write_csv(
        "violations.csv",
        [
            "agent_id",
            "date",
            "violation",
            "details"
        ],
        violations
    )

    return results, violations
