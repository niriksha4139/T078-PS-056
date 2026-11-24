
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

from .io_utils import read_csv, read_output_csv, write_csv


ROOT = Path(__file__).resolve().parents[1]
COMMAND_FILE = ROOT / "T078-PS-056-sample-data" / "commands.txt"


def load_swap_requests():
    requests = []

    with COMMAND_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split("|")

            if parts[0] == "SWAP_REQUEST" and len(parts) >= 9:
                requests.append({
                    "requested_at": parts[1],
                    "swap_id": parts[2],
                    "agent1": parts[3],
                    "date1": parts[4],
                    "shift1": parts[5],
                    "agent2": parts[6],
                    "date2": parts[7],
                    "shift2": parts[8]
                })

    return requests


def shift_interval(day, shift_code, shifts):
    shift = shifts[shift_code]

    start = datetime.combine(
        date.fromisoformat(day),
        datetime.strptime(shift["start_time"], "%H:%M").time()
    )

    end = datetime.combine(
        date.fromisoformat(day),
        datetime.strptime(shift["end_time"], "%H:%M").time()
    )

    if end <= start:
        end += timedelta(days=1)

    return start, end


def get_agent_assignments(agent_id, proposed):
    assignments = []

    for (aid, day), row in proposed.items():
        if aid == agent_id and row["shift_code"] in (
            "MORNING", "EVENING", "NIGHT"
        ):
            assignments.append((date.fromisoformat(day), row))

    assignments.sort(key=lambda item: item[0])
    return assignments


def validate_agent(agent_id, proposed, agents, shifts, prior):
    agent = agents[agent_id]

    assignments = get_agent_assignments(agent_id, proposed)

    skills = set(agent["skills"].split(";"))

    # Check skill eligibility.
    for day, row in assignments:
        if row["skill"] not in skills:
            return "RULE_SKILL_MISMATCH"

        if row["shift_code"] not in shifts:
            return "RULE_INVALID_SHIFT"

        # New employees cannot work NIGHT before 90 days.
        if row["shift_code"] == "NIGHT":
            joined = date.fromisoformat(agent["joining_date"])

            if (day - joined).days < 90:
                return "RULE_NIGHT_JOINING_90_DAYS"

    # Include previous weekly hours.
    weekly_hours = defaultdict(float)

    for row in prior:
        if row["agent_id"] != agent_id:
            continue

        work_day = date.fromisoformat(row["work_date"])
        week_start = work_day - timedelta(days=work_day.weekday())

        weekly_hours[week_start] += float(row["worked_hours"])

    for day, row in assignments:
        week_start = day - timedelta(days=day.weekday())

        weekly_hours[week_start] += float(
            shifts[row["shift_code"]]["paid_hours"]
        )

    for hours in weekly_hours.values():
        if hours > 60:
            return "RULE_WEEKLY_HOURS_OVER_60"

    # Check quarterly overtime cap using existing quarter-to-date hours.
    quarter_ot = float(agent["quarter_ot_hours_to_date"])

    month_dates = [
        day for day, row in assignments
    ]

    if month_dates:
        first_day = min(month_dates)
        last_day = max(month_dates)

        month_weekly_hours = defaultdict(float)

        for day, row in assignments:
            week_start = day - timedelta(days=day.weekday())
            month_weekly_hours[week_start] += float(
                shifts[row["shift_code"]]["paid_hours"]
            )

        for week_start, hours in month_weekly_hours.items():
            # Only estimate new overtime caused by this month's roster.
            previous_hours = 0

            for row in prior:
                if row["agent_id"] != agent_id:
                    continue

                prior_day = date.fromisoformat(row["work_date"])
                prior_week = prior_day - timedelta(
                    days=prior_day.weekday()
                )

                if prior_week == week_start:
                    previous_hours += float(row["worked_hours"])

            additional_ot = max(
                0, previous_hours + hours - 48
            ) - max(0, previous_hours - 48)

            quarter_ot += max(0, additional_ot)

        if quarter_ot > 125:
            return "RULE_QUARTERLY_OT_OVER_125"

    # Check 12-hour rest between consecutive shifts.
    intervals = []

    for day, row in assignments:
        start, end = shift_interval(
            day.isoformat(), row["shift_code"], shifts
        )
        intervals.append((start, end))

    intervals.sort(key=lambda item: item[0])

    for previous, current in zip(intervals, intervals[1:]):
        if current[0] - previous[1] < timedelta(hours=12):
            return "RULE_REST_GAP_12_HOURS"

    # Check maximum six consecutive working days.
    work_dates = sorted(day for day, row in assignments)

    previous_dates = []

    for row in prior:
        if row["agent_id"] != agent_id:
            continue

        if row["shift_code"] in shifts:
            previous_dates.append(
                date.fromisoformat(row["work_date"])
            )

    all_work_dates = sorted(set(previous_dates + work_dates))

    consecutive = 0
    previous_day = None

    for current_day in all_work_dates:
        if (
            previous_day is not None
            and (current_day - previous_day).days == 1
        ):
            consecutive += 1
        else:
            consecutive = 1

        if consecutive > 6:
            return "RULE_MAX_6_CONSECUTIVE_DAYS"

        previous_day = current_day

    # Check maximum seven consecutive NIGHT shifts.
    night_dates = sorted(
        day for day, row in assignments
        if row["shift_code"] == "NIGHT"
    )

    prior_nights = []

    for row in prior:
        if (
            row["agent_id"] == agent_id
            and row["shift_code"] == "NIGHT"
        ):
            prior_nights.append(
                date.fromisoformat(row["work_date"])
            )

    all_nights = sorted(set(prior_nights + night_dates))

    consecutive_nights = 0
    previous_day = None

    for current_day in all_nights:
        if (
            previous_day is not None
            and (current_day - previous_day).days == 1
        ):
            consecutive_nights += 1
        else:
            consecutive_nights = 1

        if consecutive_nights > 7:
            return "RULE_MAX_7_NIGHT_SHIFTS"

        previous_day = current_day

    return ""


def process_swaps():
    requests = load_swap_requests()

    agents = {
        row["agent_id"]: row
        for row in read_csv("agents.csv")
    }

    shifts = {
        row["shift_code"]: row
        for row in read_csv("shifts.csv")
    }

    prior = read_csv("prior_week_hours.csv")
    roster = read_output_csv("roster.csv")

    roster_map = {
        (row["agent_id"], row["roster_date"]): dict(row)
        for row in roster
        if row["agent_id"] != "SHORTFALL"
    }

    approved_count = defaultdict(int)
    results = []

    for request in requests:
        aid1 = request["agent1"]
        aid2 = request["agent2"]
        day1 = request["date1"]
        day2 = request["date2"]

        status = "REJECTED"
        reason = ""

        try:
            requested_at = datetime.strptime(
                request["requested_at"],
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            requested_at = None
            reason = "RULE_INVALID_REQUEST_DATE"

        actual_day2 = day1 if day2 in ("-", "") else day2

        if not reason and (aid1 not in agents or aid2 not in agents):
            reason = "RULE_AGENT_NOT_FOUND"

        elif not reason and aid1 == aid2:
            reason = "RULE_SAME_AGENT"

        elif not reason and (
            approved_count[aid1] >= 4
            or approved_count[aid2] >= 4
        ):
            reason = "RULE_MAX_4_SWAPS_PER_MONTH"

        elif not reason:
            key1 = (aid1, day1)
            key2 = (aid2, actual_day2)

            if key1 not in roster_map or key2 not in roster_map:
                reason = "RULE_NO_ROSTER_ENTRY"

            else:
                row1 = roster_map[key1]
                row2 = roster_map[key2]

                if row1["shift_code"] != request["shift1"]:
                    reason = "RULE_AGENT1_SHIFT_MISMATCH"

                elif request["shift2"] == "OFF":
                    if row2["shift_code"] != "OFF":
                        reason = "RULE_AGENT2_NOT_OFF"

                elif row2["shift_code"] != request["shift2"]:
                    reason = "RULE_AGENT2_SHIFT_MISMATCH"

                if not reason:
                    starts = [
                        shift_interval(
                            day1, request["shift1"], shifts
                        )[0]
                    ]

                    if request["shift2"] != "OFF":
                        starts.append(
                            shift_interval(
                                actual_day2,
                                request["shift2"],
                                shifts
                            )[0]
                        )

                    if requested_at > min(starts) - timedelta(hours=24):
                        reason = "RULE_SWAP_LESS_THAN_24_HOURS"

                if not reason:
                    proposed = {
                        key: dict(value)
                        for key, value in roster_map.items()
                    }

                    if request["shift2"] == "OFF":
                        proposed[key1]["shift_code"] = "OFF"
                        proposed[key1]["skill"] = ""
                        proposed[key1]["status"] = "SWAP_OFF"

                        proposed[key2]["shift_code"] = request["shift1"]
                        proposed[key2]["skill"] = row1["skill"]
                        proposed[key2]["status"] = "SWAP_APPROVED"

                    else:
                        proposed[key1]["shift_code"] = request["shift2"]
                        proposed[key1]["skill"] = row2["skill"]
                        proposed[key1]["status"] = "SWAP_APPROVED"

                        proposed[key2]["shift_code"] = request["shift1"]
                        proposed[key2]["skill"] = row1["skill"]
                        proposed[key2]["status"] = "SWAP_APPROVED"

                    reason = validate_agent(
                        aid1, proposed, agents, shifts, prior
                    )

                    if not reason:
                        reason = validate_agent(
                            aid2, proposed, agents, shifts, prior
                        )

                    if not reason:
                        roster_map = proposed
                        status = "APPROVED"
                        reason = "ALL_RULES_PASSED"

                        approved_count[aid1] += 1
                        approved_count[aid2] += 1

        results.append({
            "swap_id": request["swap_id"],
            "agent1": aid1,
            "agent2": aid2,
            "date1": day1,
            "shift1": request["shift1"],
            "date2": day2,
            "shift2": request["shift2"],
            "status": status,
            "reason": reason
        })

    updated_roster = []

    for row in roster:
        if row["agent_id"] == "SHORTFALL":
            updated_roster.append(row)
        else:
            key = (row["agent_id"], row["roster_date"])
            updated_roster.append(roster_map[key])

    write_csv(
        "roster.csv",
        [
            "roster_date",
            "agent_id",
            "shift_code",
            "skill",
            "status"
        ],
        updated_roster
    )

    write_csv(
        "swap_results.csv",
        [
            "swap_id",
            "agent1",
            "agent2",
            "date1",
            "shift1",
            "date2",
            "shift2",
            "status",
            "reason"
        ],
        results
    )

    return results
