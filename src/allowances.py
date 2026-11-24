
from datetime import date

from .io_utils import read_csv, read_output_csv, write_csv


def calculate_allowances(month):
    agents = read_csv("agents.csv")
    punches = read_output_csv("punch_results.csv")
    roster = read_output_csv("roster.csv")

    totals = {}

    agent_lookup = {
        agent["agent_id"]: agent for agent in agents
    }

    # Prepare monthly totals.
    for agent in agents:
        aid = agent["agent_id"]

        totals[aid] = {
            "agent_id": aid,
            "name": agent["name"],
            "overtime_pay": 0.0,
            "night_allowance": 0.0,
            "weekly_off_premium": 0.0,
            "meal_allowance": 0.0
        }

    # Collect weekly OFF and compensatory OFF dates.
    weekly_off_dates = set()
    comp_off_dates = set()

    for row in roster:
        if not row["roster_date"].startswith(month):
            continue

        key = (row["agent_id"], row["roster_date"])
        status = row["status"].upper()

        if status == "WEEKLY_OFF":
            weekly_off_dates.add(key)

        elif status in ("COMP_OFF", "COMPENSATORY_OFF"):
            comp_off_dates.add(key)

    # Track employees who worked on scheduled weekly OFF.
    weekly_off_worked = {}

    for punch in punches:
        punch_date = punch["date"]

        if not punch_date.startswith(month):
            continue

        aid = punch["agent_id"]

        if aid not in totals:
            continue

        agent = agent_lookup[aid]
        basic = float(agent["monthly_basic"])

        worked = float(punch["worked_hours"])
        overtime = float(punch["overtime_hours"])
        night_hours = float(punch["night_hours"])

        is_night = punch["shift_code"] == "NIGHT"
        is_violation = punch["daily_violation"] == "TRUE"
        is_half_day = punch["half_day"] == "TRUE"

        # Overtime pay: twice hourly basic.
        hourly_basic = basic / 208

        totals[aid]["overtime_pay"] += (
            overtime * hourly_basic * 2
        )

        # Night allowance.
        # Daily violations are not eligible.
        if not is_violation and worked > 0:
            if is_night:
                totals[aid]["night_allowance"] += 200
            else:
                totals[aid]["night_allowance"] += (
                    night_hours * 25
                )

        # Meal allowance.
        if not is_half_day and worked >= 6:
            if is_night:
                totals[aid]["meal_allowance"] += 150
            else:
                totals[aid]["meal_allowance"] += 100

        # Record work on scheduled weekly OFF.
        if (aid, punch_date) in weekly_off_dates and worked > 0:
            weekly_off_worked[(aid, punch_date)] = True

    # Calculate weekly-off premium.
    for aid, off_date_text in weekly_off_worked:
        basic = float(agent_lookup[aid]["monthly_basic"])
        daily_basic = basic / 26

        off_date = date.fromisoformat(off_date_text)
        comp_off_given = False

        # Check whether compensatory OFF was given within 14 days.
        for comp_aid, comp_date_text in comp_off_dates:
            if comp_aid != aid:
                continue

            comp_date = date.fromisoformat(comp_date_text)
            days_difference = (comp_date - off_date).days

            if 1 <= days_difference <= 14:
                comp_off_given = True
                break

        # Double premium if compensatory OFF was not given.
        if comp_off_given:
            totals[aid]["weekly_off_premium"] += daily_basic
        else:
            totals[aid]["weekly_off_premium"] += daily_basic * 2

    results = []

    # Round only after monthly totals are calculated.
    for item in totals.values():
        for field in [
            "overtime_pay",
            "night_allowance",
            "weekly_off_premium",
            "meal_allowance"
        ]:
            item[field] = round(item[field])

        item["total_allowance"] = (
            item["overtime_pay"]
            + item["night_allowance"]
            + item["weekly_off_premium"]
            + item["meal_allowance"]
        )

        results.append(item)

    write_csv(
        "monthly_allowances.csv",
        [
            "agent_id",
            "name",
            "overtime_pay",
            "night_allowance",
            "weekly_off_premium",
            "meal_allowance",
            "total_allowance"
        ],
        results
    )

    return results
