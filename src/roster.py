
from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta

from .io_utils import read_csv, write_csv


SHIFT_ORDER = {
    "MORNING": 0,
    "EVENING": 1,
    "NIGHT": 2,
}

SKILL_ORDER = {
    "VOICE": 0,
    "CHAT": 1,
    "EMAIL": 2,
}


def shift_interval(day: date, shift: dict):
    start = datetime.combine(
        day, datetime.strptime(shift["start_time"], "%H:%M").time()
    )

    end = datetime.combine(
        day, datetime.strptime(shift["end_time"], "%H:%M").time()
    )

    if end <= start:
        end += timedelta(days=1)

    return start, end


def generate_roster(month: str):
    if len(month) != 7 or month[4] != "-":
        raise ValueError("Month must be in YYYY-MM format")

    year, mon = map(int, month.split("-"))

    if mon < 1 or mon > 12:
        raise ValueError("Month must be in YYYY-MM format")

    agents = read_csv("agents.csv")

    shifts = {
        row["shift_code"]: row
        for row in read_csv("shifts.csv")
    }

    demands = read_csv("demand.csv")
    prior = read_csv("prior_week_hours.csv")

    days_in_month = calendar.monthrange(year, mon)[1]

    month_start = date(year, mon, 1)
    month_end = date(year, mon, days_in_month)

    demand_map = {}

    for row in demands:
        day = date.fromisoformat(row["demand_date"])

        if day.year == year and day.month == mon:
            key = (day, row["shift_code"], row["skill"])
            demand_map[key] = int(row["required_agents"])

    assigned = {}

    hours_week = defaultdict(float)
    hours_month = defaultdict(float)

    quarter_ot = {
        a["agent_id"]: float(a["quarter_ot_hours_to_date"])
        for a in agents
    }

    last_end = {}

    consecutive_days = defaultdict(int)
    consecutive_nights = defaultdict(int)

    prior_daily = {}

    # Load previous weekly hours and shift history.
    for row in prior:
        aid = row["agent_id"]
        work_date = date.fromisoformat(row["work_date"])

        week_start = work_date - timedelta(
            days=work_date.weekday()
        )

        hours_week[(aid, week_start)] += float(
            row["worked_hours"]
        )

        prior_daily[(aid, work_date)] = row["shift_code"]

        if row["shift_code"] in shifts:
            _, end = shift_interval(
                work_date, shifts[row["shift_code"]]
            )

            if aid not in last_end or end > last_end[aid]:
                last_end[aid] = end

    # Reconstruct consecutive working days and NIGHT shifts.
    for agent in agents:
        aid = agent["agent_id"]
        check_day = month_start - timedelta(days=1)

        while (aid, check_day) in prior_daily:
            previous_shift = prior_daily[(aid, check_day)]

            if previous_shift not in shifts:
                break

            consecutive_days[aid] += 1
            check_day -= timedelta(days=1)

        check_day = month_start - timedelta(days=1)

        while (aid, check_day) in prior_daily:
            previous_shift = prior_daily[(aid, check_day)]

            if previous_shift != "NIGHT":
                break

            consecutive_nights[aid] += 1
            check_day -= timedelta(days=1)

    # Identify previous weeks that already had an OFF day.
    prior_off_weeks = defaultdict(set)

    for (aid, work_date), shift_code in prior_daily.items():
        if shift_code == "OFF":
            week_start = work_date - timedelta(
                days=work_date.weekday()
            )
            prior_off_weeks[aid].add(week_start)

    # Assign preferred weekly OFF dates.
    weekly_off_dates = {}

    weekdays = [
        "MON", "TUE", "WED", "THU",
        "FRI", "SAT", "SUN"
    ]

    first_monday = month_start - timedelta(
        days=month_start.weekday()
    )

    last_monday = month_end - timedelta(
        days=month_end.weekday()
    )

    for agent in agents:
        aid = agent["agent_id"]
        preferred = agent["weekly_off"].upper()

        if preferred not in weekdays:
            raise ValueError(
                f"Invalid weekly off preference for {aid}"
            )

        monday = first_monday

        while monday <= last_monday:
            if monday in prior_off_weeks[aid]:
                monday += timedelta(days=7)
                continue

            preferred_day = monday + timedelta(
                days=weekdays.index(preferred)
            )

            week_end = monday + timedelta(days=6)

            earliest = max(monday, month_start)

            if preferred_day < earliest:
                preferred_day = earliest

            if preferred_day <= min(week_end, month_end):
                weekly_off_dates[(aid, preferred_day)] = True

            monday += timedelta(days=7)

    output = []

    # Generate the roster day by day.
    for offset in range(days_in_month):
        day = month_start + timedelta(days=offset)

        week_key = day - timedelta(
            days=day.weekday()
        )

        keys = [
            (shift_code, skill)
            for shift_code in sorted(
                shifts,
                key=lambda x: SHIFT_ORDER[x]
            )
            for skill in sorted(
                SKILL_ORDER,
                key=lambda x: SKILL_ORDER[x]
            )
        ]

        for shift_code, skill in keys:
            required = demand_map.get(
                (day, shift_code, skill), 0
            )

            if required <= 0:
                continue

            shift = shifts[shift_code]
            start, end = shift_interval(day, shift)

            eligible = []

            for agent in agents:
                aid = agent["agent_id"]

                if skill not in agent["skills"].split(";"):
                    continue

                if (aid, day) in assigned:
                    continue

                if (aid, day) in weekly_off_dates:
                    continue

                joining_date = date.fromisoformat(
                    agent["joining_date"]
                )

                # New employees cannot work NIGHT before 90 days.
                if (
                    shift_code == "NIGHT"
                    and (day - joining_date).days < 90
                ):
                    continue

                # Maximum six consecutive working days.
                if consecutive_days[aid] >= 6:
                    continue

                # Maximum seven consecutive NIGHT shifts.
                if (
                    shift_code == "NIGHT"
                    and consecutive_nights[aid] >= 7
                ):
                    continue

                # Minimum 12-hour rest between shifts.
                if (
                    aid in last_end
                    and start - last_end[aid] < timedelta(hours=12)
                ):
                    continue

                paid_hours = float(shift["paid_hours"])

                current_week = hours_week[(aid, week_key)]
                projected_week = current_week + paid_hours

                # Maximum 60 hours per week.
                if projected_week > 60:
                    continue

                # Calculate additional weekly overtime.
                old_ot = max(0, current_week - 48)
                new_ot = max(0, projected_week - 48)
                additional_ot = new_ot - old_ot

                remaining_ot = max(
                    0, 125 - quarter_ot[aid]
                )

                # Maximum 125 quarterly overtime hours.
                if additional_ot > remaining_ot:
                    continue

                eligible.append(agent)

            # Lowest month-to-date hours first.
            eligible.sort(
                key=lambda a: (
                    hours_month[a["agent_id"]],
                    a["agent_id"]
                )
            )

            selected = eligible[:required]

            for agent in selected:
                aid = agent["agent_id"]
                paid_hours = float(shift["paid_hours"])

                old_ot = max(
                    0, hours_week[(aid, week_key)] - 48
                )

                hours_week[(aid, week_key)] += paid_hours

                new_ot = max(
                    0, hours_week[(aid, week_key)] - 48
                )

                quarter_ot[aid] += new_ot - old_ot
                hours_month[aid] += paid_hours

                assigned[(aid, day)] = {
                    "shift_code": shift_code,
                    "skill": skill,
                    "status": "SCHEDULED"
                }

                last_end[aid] = end
                consecutive_days[aid] += 1

                if shift_code == "NIGHT":
                    consecutive_nights[aid] += 1
                else:
                    consecutive_nights[aid] = 0

            # Record unfilled demand.
            if len(selected) < required:
                output.append({
                    "roster_date": day.isoformat(),
                    "agent_id": "SHORTFALL",
                    "shift_code": shift_code,
                    "skill": skill,
                    "status": f"SHORTFALL:{required - len(selected)}"
                })

        # Create one row for every agent every day.
        for agent in sorted(
            agents,
            key=lambda a: a["agent_id"]
        ):
            aid = agent["agent_id"]
            item = assigned.get((aid, day))

            if item:
                output.append({
                    "roster_date": day.isoformat(),
                    "agent_id": aid,
                    **item
                })

            else:
                if (aid, day) in weekly_off_dates:
                    status = "WEEKLY_OFF"
                else:
                    status = "NO_ASSIGNMENT"

                output.append({
                    "roster_date": day.isoformat(),
                    "agent_id": aid,
                    "shift_code": "OFF",
                    "skill": "",
                    "status": status
                })

                # An unassigned day breaks both streaks.
                consecutive_days[aid] = 0
                consecutive_nights[aid] = 0

    output.sort(
        key=lambda r: (
            r["roster_date"],
            r["agent_id"] == "SHORTFALL",
            r["agent_id"]
        )
    )

    write_csv(
        "roster.csv",
        [
            "roster_date",
            "agent_id",
            "shift_code",
            "skill",
            "status"
        ],
        output
    )

    return output
