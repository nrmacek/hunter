"""
Seed script — populates the database with 5 real firms for Phase 5 demo.

Run with: python seed.py
"""

from database import init_db, get_connection
from scoring.engine import score_firm
from models import compute_composite

# ── Seed Data (real firms, confirmed by Nick) ────────────────────────────────

SEED_FIRMS = [
    {"name": "Gresham Smith",       "city": "Nashville",  "state": "TN", "source": "ENR", "tier": 1},
    {"name": "Kimley-Horn",         "city": "Raleigh",    "state": "NC", "source": "ENR", "tier": 1},
    {"name": "WD Partners",         "city": "Dublin",     "state": "OH", "source": "CenterBuild", "tier": 2},
    {"name": "Little Diversified",  "city": "Charlotte",  "state": "NC", "source": "CenterBuild", "tier": 2},
    {"name": "Corgan",              "city": "Dallas",     "state": "TX", "source": "ENR", "tier": 1},
]


def seed():
    """Insert seed firms and generate stub scores for each."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data for a clean seed
    cursor.execute("DELETE FROM scores")
    cursor.execute("DELETE FROM firms")

    for firm in SEED_FIRMS:
        # Insert firm
        cursor.execute(
            """INSERT INTO firms (name, city, state, source, tier, bd_stage)
               VALUES (?, ?, ?, ?, ?, 'Meet')""",
            (firm["name"], firm["city"], firm["state"], firm["source"], firm["tier"]),
        )
        firm_id = cursor.lastrowid

        # Generate stub scores
        scores = score_firm(firm["name"])

        # Insert scores
        cursor.execute(
            """INSERT INTO scores (
                firm_id,
                cultural_alignment, cultural_confidence,
                growth_orientation, growth_confidence,
                industry_services, industry_confidence,
                revenue, revenue_confidence,
                employees, employees_confidence,
                geography, geography_confidence,
                composite, score_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                firm_id,
                scores["cultural_alignment"], scores["cultural_confidence"],
                scores["growth_orientation"], scores["growth_confidence"],
                scores["industry_services"], scores["industry_confidence"],
                scores["revenue"], scores["revenue_confidence"],
                scores["employees"], scores["employees_confidence"],
                scores["geography"], scores["geography_confidence"],
                scores["composite"], scores["score_notes"],
            ),
        )

        print(f"  ✓ {firm['name']:25s}  composite: {scores['composite']}")

    conn.commit()
    conn.close()
    print(f"\nSeeded {len(SEED_FIRMS)} firms.")


if __name__ == "__main__":
    seed()
