"""
Targeted geography re-score — updates only the geography score for all firms
using the updated HQ-weighted rubric. Recomputes composite after each update.

Faster than a full re-batch: scrapes geography signals only, sends a
focused Claude call, updates geography + composite in the DB.

Run from backend/:
    python ../scripts/rescore_geography.py
"""

import sys
import time
import random
import logging
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

GEO_SYSTEM_PROMPT = """You are scoring an architecture/engineering firm on a single criterion: Geography.

GEOGRAPHY RUBRIC (score 1.0–5.0):

HQ location is the primary factor. Use two steps:

Step 1 — HQ sets the base:
  East Coast HQ (ME, NH, VT, MA, RI, CT, NY, NJ, PA, DE, MD, VA, NC, SC, GA, FL, DC) → base 4
  Central time zone HQ (OH, MI, IN, IL, WI, MN, IA, MO, ND, SD, NE, KS, TX, OK, AR, LA, MS, AL, TN, KY, WV) → base 3
  Mountain / West Coast / International HQ → base 1

Step 2 — Satellite offices adjust:
  All offices East Coast only → +1
  East Coast + Central mix → 0
  Any Mountain or West Coast office → −1
  Any international offices → −1

Final = HQ base + modifier, clamped to 1–5.

Examples:
  NJ HQ, all East Coast offices → 5
  NJ HQ, East + Central mix → 4
  NJ HQ + one West Coast office → 3
  TX HQ, all Central offices → 3
  Seattle HQ, East Coast offices → 1

If office locations are unknown or unclear, score 2 and mark confidence low.

Return ONLY this JSON (no other text):
{"geography": <float 1.0-5.0>, "geography_confidence": "<high|low>", "rationale": "<1-2 sentences explaining HQ location and any satellite offices found>"}"""


def scrape_geo(firm_name: str) -> str:
    """Scrape geography signals only — DDG search + website."""
    from scoring.scraper import _ddg_search, _guess_website_urls, _fetch_firm_pages, _get
    import random, time

    time.sleep(random.uniform(2.0, 3.5))
    geo_text = _ddg_search(f'"{firm_name}" headquarters office locations cities states')

    # Try firm website for office pages
    website_text = ""
    for candidate in _guess_website_urls(firm_name):
        time.sleep(0.3)
        html = _get(candidate)
        if html and len(html) > 500:
            website_text = _fetch_firm_pages(candidate)
            break

    return (geo_text + "\n" + website_text)[:4000]


def score_geography(firm_name: str, geo_text: str) -> dict:
    """Ask Claude to score geography only using the updated rubric."""
    import anthropic, json
    from scoring.ai_scorer import _parse_response

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=GEO_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"FIRM: {firm_name}\n\n--- LOCATION DATA ---\n{geo_text or '(no data found)'}\n\nScore this firm's geography."
        }],
    )
    return _parse_response(msg.content[0].text)


def main():
    from database import get_connection
    from models import compute_composite

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.name, f.tier,
               s.id AS score_id,
               s.cultural_alignment, s.growth_orientation,
               s.industry_services, s.revenue, s.employees,
               s.geography, s.geography_confidence
        FROM firms f JOIN scores s ON s.firm_id = f.id
        ORDER BY f.tier ASC, f.id ASC
    """)
    firms = [dict(r) for r in cur.fetchall()]
    conn.close()

    total = len(firms)
    print(f"\nRe-scoring geography for {total} firms using updated HQ-weighted rubric\n")
    print(f"{'#':<5} {'Firm':<42} {'Old':>5} {'New':>5} {'Conf':<6} {'Composite'}")
    print("─" * 75)

    for i, firm in enumerate(firms, 1):
        name = firm["name"]
        try:
            geo_text = scrape_geo(name)
            result   = score_geography(name, geo_text)

            new_geo  = max(1.0, min(5.0, float(result["geography"])))
            new_conf = result.get("geography_confidence", "low")

            new_composite = compute_composite({
                "cultural_alignment": firm["cultural_alignment"],
                "growth_orientation": firm["growth_orientation"],
                "industry_services":  firm["industry_services"],
                "revenue":            firm["revenue"],
                "employees":          firm["employees"],
                "geography":          new_geo,
            })

            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("""
                UPDATE scores SET geography = ?, geography_confidence = ?, composite = ?
                WHERE id = ?
            """, (new_geo, new_conf, new_composite, firm["score_id"]))
            conn.commit()
            conn.close()

            old = firm["geography"]
            arrow = "→" if new_geo != old else "="
            print(f"{i:<5} {name:<42} {old:>5.1f} {arrow} {new_geo:>4.1f} {new_conf:<6} {new_composite:.2f}")

        except Exception as e:
            print(f"{i:<5} {name:<42} {'—':>5}   {'ERR':<6} {e}")

        if i < total:
            time.sleep(random.uniform(5, 9))

    print("─" * 75)
    print(f"\nDone. {total} firms re-scored on geography.")


if __name__ == "__main__":
    main()
