"""
Audit script — shows full scoring detail for any firm in the database.

Usage (run from project root or backend/):
    python scripts/audit_firm.py "Firm Name"
    python scripts/audit_firm.py "Firm Name" --stored-only
    python scripts/audit_firm.py --list
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env")

WEIGHTS = {
    "cultural_alignment": 0.10,
    "growth_orientation": 0.30,
    "industry_services":  0.25,
    "revenue":            0.15,
    "employees":          0.10,
    "geography":          0.10,
}

LABELS = {
    "cultural_alignment": "Cultural Alignment",
    "growth_orientation": "Growth Orientation",
    "industry_services":  "Industry & Services",
    "revenue":            "Total Revenue",
    "employees":          "# of Employees",
    "geography":          "Geography",
}

# Maps criterion key → stored DB column name for score value
SCORE_COL = {
    "cultural_alignment": "cultural_alignment",
    "growth_orientation": "growth_orientation",
    "industry_services":  "industry_services",
    "revenue":            "revenue",
    "employees":          "emp_score",
    "geography":          "geography",
}

CONF_COL = {
    "cultural_alignment": "cultural_confidence",
    "growth_orientation": "growth_confidence",
    "industry_services":  "industry_confidence",
    "revenue":            "revenue_confidence",
    "employees":          "employees_confidence",
    "geography":          "geography_confidence",
}


# ── Formatting helpers ────────────────────────────────────────────────────────

W = 72

def div(char="─"):
    print(char * W)

def section(title):
    print()
    div()
    print(f"  {title}")
    div()

def wrap(text, indent="    ", width=70):
    words = text.split()
    line = indent
    for word in words:
        if len(line) + len(word) + 1 > width:
            print(line.rstrip())
            line = indent + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line.rstrip())


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_stored(name):
    from database import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.name, f.tier, f.source, f.employees, f.revenue_m,
               s.cultural_alignment, s.cultural_confidence,
               s.growth_orientation, s.growth_confidence,
               s.industry_services,  s.industry_confidence,
               s.revenue,            s.revenue_confidence,
               s.employees AS emp_score, s.employees_confidence,
               s.geography,          s.geography_confidence,
               s.composite, s.scored_at, s.score_notes, s.is_real_score
        FROM firms f
        LEFT JOIN scores s ON s.firm_id = f.id
        WHERE f.name = ?
    """, (name,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def list_all():
    from database import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.name, f.tier, s.composite, s.is_real_score
        FROM firms f LEFT JOIN scores s ON s.firm_id = f.id
        ORDER BY s.composite DESC NULLS LAST
    """)
    rows = cur.fetchall()
    conn.close()
    print(f"\n  {'#':<5} {'Firm':<45} {'Tier':<6} {'Score':<8} {'Type'}")
    print(f"  {'─'*68}")
    for i, r in enumerate(rows, 1):
        score = f"{r['composite']:.2f}" if r['composite'] is not None else "—"
        kind  = "AI" if r['is_real_score'] else "stub"
        print(f"  {i:<5} {r['name']:<45} {str(r['tier'] or '?'):<6} {score:<8} {kind}")
    print()


# ── Live scrape ───────────────────────────────────────────────────────────────

def live_scrape(name, known_employees):
    import scoring.scraper as scraper_mod
    import scoring.ai_scorer as scorer_mod

    captured = {}
    orig = scorer_mod._parse_response
    def capture(text):
        captured["raw"] = text
        return orig(text)
    scorer_mod._parse_response = capture

    scraped = scraper_mod.scrape_firm(name)
    known   = {"employees": known_employees} if known_employees else {}
    scores  = scorer_mod.ai_score_firm(name, scraped, known_data=known)

    scorer_mod._parse_response = orig
    return scraped, scores


# ── Main audit ────────────────────────────────────────────────────────────────

def audit(name, run_live):
    stored = get_stored(name)
    if not stored:
        print(f'\n  Error: "{name}" not found in the database.')
        print("  Use --list to see all firm names.\n")
        sys.exit(1)

    # ── Header ──
    div("═")
    print(f"  AUDIT: {name}")
    div("═")
    rev = f"${stored['revenue_m']:.1f}M" if stored['revenue_m'] else "—"
    print(f"  Tier {stored['tier'] or '?'}  │  Source: {stored['source'] or '—'}"
          f"  │  DB employees: {stored['employees'] or '—'}  │  DB revenue: {rev}")

    # ── Stored scores ──
    section("STORED SCORES")
    if not stored["composite"]:
        print("  No scores on record.")
    else:
        kind = "AI-scored" if stored["is_real_score"] else "STUB — not yet real-scored"
        print(f"  Type      : {kind}")
        print(f"  Scored at : {stored['scored_at'] or '—'}")
        print()
        print(f"  {'Criterion':<26} {'Score':<8} {'Confidence'}")
        print(f"  {'─────────':<26} {'─────':<8} {'──────────'}")
        for key, label in LABELS.items():
            score = stored.get(SCORE_COL[key])
            conf  = stored.get(CONF_COL[key], "—")
            dot   = "● " if conf == "low" else "  "
            score_str = f"{score:.1f}" if score is not None else "—"
            print(f"  {dot}{label:<26} {score_str:<8} {conf}")

    # ── Stored weighted math ──
    if stored["composite"]:
        section("COMPOSITE SCORE MATH")
        print(f"  {'Criterion':<26} {'Score':>6}  {'Weight':>7}  {'Weighted':>8}")
        print(f"  {'─────────':<26} {'─────':>6}  {'──────':>7}  {'────────':>8}")
        total = 0.0
        for key, label in LABELS.items():
            score    = stored.get(SCORE_COL[key]) or 0.0
            weight   = WEIGHTS[key]
            weighted = score * weight
            total   += weighted
            print(f"  {label:<26} {score:>6.1f}  {weight*100:>6.0f}%  {weighted:>8.3f}")
        print(f"  {'─'*54}")
        print(f"  {'COMPOSITE':26} {'':>6}  {'100%':>7}  {total:>8.3f}  →  {round(total, 2)}")

    # ── Stored rationale ──
    if stored.get("score_notes"):
        section("AI RATIONALE  (stored)")
        wrap(stored["score_notes"])

    # ── Live scrape ──
    if not run_live:
        print()
        return

    section("LIVE SCRAPE  (fresh run)")
    print("  Scraping now — this takes 20–40 seconds...\n")

    scraped, live = live_scrape(name, stored.get("employees"))

    print(f"  Website URL      : {scraped.get('website_url') or '(not found)'}")
    print()
    print(f"  {'Source':<26} {'Chars collected':>15}")
    print(f"  {'──────':<26} {'───────────────':>15}")
    sources = {
        "overview":          "DDG overview search",
        "growth":            "DDG growth/news search",
        "industry_services": "Firm website pages",
        "geography":         "Geography signals",
    }
    for key, label in sources.items():
        chars = len(scraped.get(key, ""))
        print(f"  {label:<26} {chars:>14} chars")

    section("LIVE AI SCORES")
    print(f"  {'Criterion':<26} {'Score':>6}  {'Conf':<8} {'Weight':>7}  {'Weighted':>8}")
    print(f"  {'─────────':<26} {'─────':>6}  {'────':<8} {'──────':>7}  {'────────':>8}")
    total = 0.0
    for key, label in LABELS.items():
        score    = live[key]
        conf     = live[CONF_COL[key]]
        weight   = WEIGHTS[key]
        weighted = score * weight
        total   += weighted
        dot = "● " if conf == "low" else "  "
        print(f"  {dot}{label:<26} {score:>6.1f}  {conf:<8} {weight*100:>6.0f}%  {weighted:>8.3f}")
    print(f"  {'─'*62}")
    print(f"  {'COMPOSITE':26} {'':>6}  {'':8} {'100%':>7}  {total:>8.3f}  →  {round(total,2)}")

    section("LIVE AI RATIONALE")
    wrap(live.get("score_notes", "—"))
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Audit scoring detail for any firm in the Hunter database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python scripts/audit_firm.py "HFA"\n'
            '  python scripts/audit_firm.py "Gresham Smith" --stored-only\n'
            "  python scripts/audit_firm.py --list"
        ),
    )
    parser.add_argument("firm", nargs="?", help="Firm name (exact, case-sensitive)")
    parser.add_argument("--list", action="store_true", help="List all firms ranked by score")
    parser.add_argument("--stored-only", action="store_true",
                        help="Show stored DB scores only — skip live re-scrape")
    args = parser.parse_args()

    if args.list:
        list_all()
        return

    if not args.firm:
        parser.print_help()
        sys.exit(1)

    audit(args.firm, run_live=not args.stored_only)


if __name__ == "__main__":
    main()
