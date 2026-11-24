
from __future__ import annotations

import argparse

from .roster import generate_roster
from .swaps import process_swaps
from .punches import process_punches
from .allowances import calculate_allowances


def main():
    parser = argparse.ArgumentParser(
        description="T078-PS-056 Shift Roster and Overtime Engine"
    )

    parser.add_argument(
        "--month",
        default="2026-09",
        help="Month to process in YYYY-MM format"
    )

    parser.add_argument(
        "--roster-only",
        action="store_true",
        help="Generate roster only"
    )

    args = parser.parse_args()

    print("\nSTEP 1: Generating monthly roster...")
    generate_roster(args.month)

    if args.roster_only:
        print("\nRoster generation completed.")
        return

    print("\nSTEP 2: Processing shift swaps...")
    process_swaps()

    print("\nSTEP 3: Processing attendance and punches...")
    process_punches(args.month)

    print("\nSTEP 4: Calculating monthly allowances...")
    calculate_allowances(args.month)

    print("\nAll processing steps completed!")
    print("Check the output folder for generated reports.")


if __name__ == "__main__":
    main()
