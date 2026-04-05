"""
Phase 7 batch scoring — scores all firms in the database that have stub scores.

Features:
- Skips firms already scored with real data (score_notes not containing "Stub")
- Saves progress after each firm so it can be safely interrupted and resumed
- Prints a running summary as it goes
- Adds randomized delays between firms to avoid rate limiting

Run from backend/ directory:
    python ../scripts/batch_score.py

Options:
    --rescore    Re-score all firms, even ones already scored with real data
    --tier N     Only score firms of tier N (1, 2, or 3)
    --limit N    Stop after N firms (useful for spot-checking)
"""

import sys
import time
import random
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_firms_to_score(conn, rescore: bool, tier: int | None) -> list[dict]:
    cursor = conn.cursor()

    if rescore:
        where = "1=1"
    else:
        # Skip firms that already have real (non-stub) scores
        where = "(s.score_notes IS NULL OR s.score_notes LIKE 'Stub%')"

    tier_clause = f"AND f.tier = {tier}" if tier else ""

    cursor.execute(f"""
        SELECT f.id, f.name, f.tier, f.source, s.composite, s.score_notes
        FROM firms f
        LEFT JOIN scores s ON s.firm_id = f.id
        WHERE {where} {tier_clause}
        ORDER BY f.tier ASC, f.id ASC
    """)
    return [dict(row) for row in cursor.fetchall()]


def write_score(conn, firm_id: int, scores: dict) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scores WHERE firm_id = ?", (firm_id,))
    cursor.execute("""
        INSERT INTO scores (
            firm_id,
            cultural_alignment, cultural_confidence,
            growth_orientation, growth_confidence,
            industry_services,  industry_confidence,
            revenue,            revenue_confidence,
            employees,          employees_confidence,
            geography,          geography_confidence,
            composite,          score_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        firm_id,
        scores["cultural_alignment"], scores["cultural_confidence"],
        scores["growth_orientation"], scores["growth_confidence"],
        scores["industry_services"],  scores["industry_confidence"],
        scores["revenue"],            scores["revenue_confidence"],
        scores["employees"],          scores["employees_confidence"],
        scores["geography"],          scores["geography_confidence"],
        scores["composite"],          scores["score_notes"],
    ))
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Batch score all firms")
    parser.add_argument("--rescore", action="store_true",
                        help="Re-score firms that already have real scores")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3],
                        help="Only score firms of this tier")
    parser.add_argument("--limit", type=int,
                        help="Stop after this many firms")
    args = parser.parse_args()

    from database import init_db, get_connection
    from scoring.engine import score_firm

    init_db()
    conn = get_connection()
    firms = get_firms_to_score(conn, rescore=args.rescore, tier=args.tier)
    conn.close()

    if args.limit:
        firms = firms[:args.limit]

    total = len(firms)
    if total == 0:
        print("No firms to score. Use --rescore to re-score all firms.")
        return

    tier_str = f" (Tier {args.tier})" if args.tier else ""
    print(f"\nBatch scoring {total} firms{tier_str}\n")
    print(f"{'#':<5} {'Firm':<40} {'Tier':<6} {'Composite':<10} {'Status'}")
    print("-" * 75)

    scored = 0
    failed = 0

    for i, firm in enumerate(firms, 1):
        name = firm["name"]
        tier = firm["tier"]

        try:
            scores = score_firm(name)
            conn = get_connection()
            write_score(conn, firm["id"], scores)
            conn.close()

            composite = scores["composite"]
            is_stub = "Stub" in scores.get("score_notes", "")
            status = "STUB fallback" if is_stub else "OK"
            print(f"{i:<5} {name:<40} {str(tier):<6} {composite:<10.2f} {status}")
            scored += 1

        except Exception as e:
            print(f"{i:<5} {name:<40} {str(tier):<6} {'—':<10} FAILED: {e}")
            logger.error(f"Unhandled error scoring {name}: {e}", exc_info=True)
            failed += 1

        # Randomized delay between firms — long enough for DDG not to rate-limit
        if i < total:
            delay = random.uniform(8, 14)
            time.sleep(delay)

    print("-" * 75)
    print(f"\nDone. {scored} scored, {failed} failed, {total} total.")
    if failed:
        print(f"Re-run with --rescore to retry failed firms.")


if __name__ == "__main__":
    main()
