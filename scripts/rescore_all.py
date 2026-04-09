"""
Batch re-score all firms that lack rationale data.
Scrapes fresh (caches result), scores with updated prompt.
Prints progress as each firm completes.
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database import init_db, get_connection
from scoring.engine import score_firm
from models import compute_composite, WEIGHTS

init_db()


def get_firms_needing_rescore():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT f.id, f.name, s.growth_rationale
        FROM firms f
        JOIN scores s ON s.firm_id = f.id
        ORDER BY f.name
    """)
    rows = c.fetchall()
    conn.close()
    return [(r["id"], r["name"]) for r in rows if not r["growth_rationale"]]


def save_scores(firm_id, firm_name, scores):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scores WHERE firm_id = ?", (firm_id,))

    is_real = 0 if scores.get("score_notes", "").startswith("Stub") else 1
    cursor.execute(
        """INSERT INTO scores (
            firm_id,
            cultural_alignment, cultural_confidence, cultural_rationale, cultural_sources,
            growth_orientation, growth_confidence, growth_rationale, growth_sources,
            industry_services, industry_confidence, industry_rationale, industry_sources,
            revenue, revenue_confidence, revenue_rationale, revenue_sources,
            employees, employees_confidence, employees_rationale, employees_sources,
            geography, geography_confidence, geography_rationale, geography_sources,
            composite, score_notes, is_real_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            firm_id,
            scores["cultural_alignment"], scores["cultural_confidence"],
            scores.get("cultural_rationale"), scores.get("cultural_sources"),
            scores["growth_orientation"], scores["growth_confidence"],
            scores.get("growth_rationale"), scores.get("growth_sources"),
            scores["industry_services"], scores["industry_confidence"],
            scores.get("industry_rationale"), scores.get("industry_sources"),
            scores["revenue"], scores["revenue_confidence"],
            scores.get("revenue_rationale"), scores.get("revenue_sources"),
            scores["employees"], scores["employees_confidence"],
            scores.get("employees_rationale"), scores.get("employees_sources"),
            scores["geography"], scores["geography_confidence"],
            scores.get("geography_rationale"), scores.get("geography_sources"),
            scores["composite"], scores["score_notes"], is_real,
        ),
    )
    conn.commit()
    conn.close()


def main():
    firms = get_firms_needing_rescore()
    total = len(firms)
    print(f"=== Batch re-score: {total} firms ===")
    print(f"Started at {time.strftime('%I:%M %p')}")
    print()

    succeeded = 0
    failed = 0
    stubs = 0

    for i, (firm_id, name) in enumerate(firms, 1):
        start = time.time()
        try:
            scores = score_firm(name, refresh=False)
            save_scores(firm_id, name, scores)
            elapsed = time.time() - start
            is_stub = scores.get("score_notes", "").startswith("Stub")
            has_rationale = bool(scores.get("growth_rationale"))

            if is_stub:
                stubs += 1
                status = "STUB"
            else:
                succeeded += 1
                status = "OK" if has_rationale else "OK (no rationale)"

            print(f"[{i}/{total}] {status} {name} — {scores['composite']:.2f} — {elapsed:.0f}s")
        except Exception as e:
            failed += 1
            elapsed = time.time() - start
            print(f"[{i}/{total}] FAIL {name} — {e} — {elapsed:.0f}s")

        sys.stdout.flush()

    print()
    print(f"=== Done at {time.strftime('%I:%M %p')} ===")
    print(f"Succeeded: {succeeded} | Stubs: {stubs} | Failed: {failed} | Total: {total}")


if __name__ == "__main__":
    main()
