"""
Phase 6 import script — loads all Tier 1/2/3 firms from Master Target List 2.0.xlsx
into the Hunter SQLite database with stub scores.

Run from the backend/ directory:
    python ../scripts/import_firms.py
"""

import sys
import os
from pathlib import Path

# Allow imports from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import openpyxl
from database import init_db, get_connection
from scoring.engine import score_firm

XLSX_PATH = Path(__file__).resolve().parent.parent / "data" / "Master Target List 2.0.xlsx"

TIER_SHEETS = [
    (1, "2023 Tier 1"),
    (2, "2023 Tier 2"),
    (3, "2023 Tier 3"),
]

# Column indices (0-based) shared across all three tier sheets
COL_NAME      = 0
COL_REVENUE   = 7   # Total Relevant Revenue
COL_EMPLOYEES = 8   # LI Employees
COL_SOURCE    = 9   # Data Source


def load_firms_from_sheet(ws, tier: int) -> list[dict]:
    firms = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = row[COL_NAME]
        if not name or not str(name).strip():
            continue

        revenue_raw = row[COL_REVENUE] if len(row) > COL_REVENUE else None
        employees_raw = row[COL_EMPLOYEES] if len(row) > COL_EMPLOYEES else None
        source_raw = row[COL_SOURCE] if len(row) > COL_SOURCE else None

        # Revenue stored as dollars in the sheet — convert to millions
        revenue_m = None
        if isinstance(revenue_raw, (int, float)) and revenue_raw > 0:
            revenue_m = round(revenue_raw / 1_000_000, 2)

        employees = None
        if isinstance(employees_raw, (int, float)) and employees_raw > 0:
            employees = int(employees_raw)

        source = str(source_raw).strip() if source_raw else "BDC 2023"

        firms.append({
            "name": str(name).strip(),
            "tier": tier,
            "source": source,
            "employees": employees,
            "revenue_m": revenue_m,
        })
    return firms


def run_import():
    init_db()

    wb = openpyxl.load_workbook(str(XLSX_PATH))

    all_firms = []
    for tier, sheet_name in TIER_SHEETS:
        ws = wb[sheet_name]
        firms = load_firms_from_sheet(ws, tier)
        print(f"Tier {tier} ({sheet_name}): {len(firms)} firms loaded")
        all_firms.extend(firms)

    print(f"\nTotal: {len(all_firms)} firms — clearing DB and importing...")

    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM scores")
    cursor.execute("DELETE FROM firms")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('firms','scores')")

    imported = 0
    for firm in all_firms:
        cursor.execute(
            """INSERT INTO firms (name, tier, source, employees, revenue_m, bd_stage)
               VALUES (?, ?, ?, ?, ?, 'Meet')""",
            (firm["name"], firm["tier"], firm["source"], firm["employees"], firm["revenue_m"]),
        )
        firm_id = cursor.lastrowid

        scores = score_firm(firm["name"])

        cursor.execute(
            """INSERT INTO scores (
                firm_id,
                cultural_alignment, cultural_confidence,
                growth_orientation, growth_confidence,
                industry_services,  industry_confidence,
                revenue,            revenue_confidence,
                employees,          employees_confidence,
                geography,          geography_confidence,
                composite,          score_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                firm_id,
                scores["cultural_alignment"], scores["cultural_confidence"],
                scores["growth_orientation"], scores["growth_confidence"],
                scores["industry_services"],  scores["industry_confidence"],
                scores["revenue"],            scores["revenue_confidence"],
                scores["employees"],          scores["employees_confidence"],
                scores["geography"],          scores["geography_confidence"],
                scores["composite"],          scores["score_notes"],
            ),
        )

        imported += 1

    conn.commit()
    conn.close()

    print(f"Done — {imported} firms imported with stub scores.")


if __name__ == "__main__":
    run_import()
