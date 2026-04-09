"""
Targeted growth re-score — updates only the growth_orientation score for firms
where growth_confidence = 'low', using the improved scraper (news pages,
DDG news sources, LinkedIn job postings).

Run from backend/:
    python ../scripts/rescore_growth.py
    python ../scripts/rescore_growth.py --all      # re-score all firms, not just low-confidence
    python ../scripts/rescore_growth.py --limit 10 # cap at N firms (for testing)
"""

import sys
import time
import random
import logging
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

GROWTH_SYSTEM_PROMPT = """You are scoring an architecture/engineering firm on a single criterion: Growth Orientation.

GROWTH ORIENTATION RUBRIC (score 1.0–5.0):

1 = Revenue or headcount clearly declining; layoffs, office closures, downsizing news
2 = Little evidence of growth; flat or unclear trajectory
3 = Stable, modest growth; some hiring or expansion signals
4 = Clear growth signals — new offices, hiring, acquisitions, or ENR rank improvement
5 = >10% Y/Y growth, actively expanding, forward-thinking — multiple strong signals

Data sources to consider:
- ENR ranking change year-over-year (strongest signal when present)
- LinkedIn job postings volume and active roles
- News: new office openings, acquisitions, new market entries, awards
- Press releases from BusinessWire, PRNewswire, ENR, Architect Magazine, BDCnetwork
- Firm /news or /press page content
- Negative override: layoff news, office closures, or downsizing overrides positive signals

MISSING DATA: If you find no usable growth signals, score 2 and set confidence to "low".

Return ONLY this JSON (no other text):
{"growth_orientation": <float 1.0-5.0>, "growth_confidence": "<high|low>", "rationale": "<1-2 sentences explaining the key growth signals found or absence of data>"}"""


def scrape_growth(firm_name: str) -> str:
    """Collect growth signals using the improved scraper functions."""
    from scoring.scraper import (
        _ddg_search, _ddg_news_search, _ddg_linkedin_jobs,
        _guess_website_urls, _fetch_news_pages, _get,
    )

    parts = []

    # DDG general growth search
    time.sleep(random.uniform(2.0, 3.5))
    ddg_general = _ddg_search(
        f'"{firm_name}" architecture engineering growth revenue ENR ranking 2023 2024 expansion'
    )
    if ddg_general:
        parts.append(ddg_general)

    # DDG news sources (BusinessWire, PRNewswire, ENR, etc.)
    time.sleep(random.uniform(3.0, 5.0))
    ddg_news = _ddg_news_search(f'"{firm_name}"')
    if ddg_news:
        parts.append(ddg_news)

    # LinkedIn job postings
    time.sleep(random.uniform(3.0, 5.0))
    ddg_jobs = _ddg_linkedin_jobs(firm_name)
    if ddg_jobs:
        parts.append(ddg_jobs)

    # Firm /news or /press page
    website_url = None
    for candidate in _guess_website_urls(firm_name):
        time.sleep(0.3)
        html = _get(candidate)
        if html and len(html) > 500:
            website_url = candidate
            break

    if website_url:
        news_page = _fetch_news_pages(website_url)
        if news_page:
            parts.append(news_page)

    combined = "\n\n".join(parts)
    return combined[:5000]


def score_growth(firm_name: str, growth_text: str) -> dict:
    """Ask Claude to score growth only."""
    import anthropic, json
    from scoring.ai_scorer import _parse_response

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=GROWTH_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"FIRM: {firm_name}\n\n"
                f"--- GROWTH SIGNALS ---\n{growth_text or '(no data found)'}\n\n"
                "Score this firm's growth orientation."
            ),
        }],
    )
    return _parse_response(msg.content[0].text)


def main():
    parser = argparse.ArgumentParser(
        description="Re-score growth orientation for low-confidence firms.",
    )
    parser.add_argument("--all", action="store_true",
                        help="Re-score all firms, not just low-confidence ones")
    parser.add_argument("--limit", type=int, default=None,
                        help="Cap number of firms to process (for testing)")
    args = parser.parse_args()

    from database import get_connection
    from models import compute_composite

    conn = get_connection()
    cur = conn.cursor()

    if args.all:
        cur.execute("""
            SELECT f.id, f.name, f.tier,
                   s.id AS score_id,
                   s.cultural_alignment, s.growth_orientation, s.growth_confidence,
                   s.industry_services, s.revenue, s.employees,
                   s.geography
            FROM firms f JOIN scores s ON s.firm_id = f.id
            ORDER BY f.tier ASC, f.id ASC
        """)
    else:
        cur.execute("""
            SELECT f.id, f.name, f.tier,
                   s.id AS score_id,
                   s.cultural_alignment, s.growth_orientation, s.growth_confidence,
                   s.industry_services, s.revenue, s.employees,
                   s.geography
            FROM firms f JOIN scores s ON s.firm_id = f.id
            WHERE s.growth_confidence = 'low'
            ORDER BY f.tier ASC, f.id ASC
        """)

    firms = [dict(r) for r in cur.fetchall()]
    conn.close()

    if args.limit:
        firms = firms[: args.limit]

    total = len(firms)
    label = "all" if args.all else "low-confidence"
    print(f"\nRe-scoring growth orientation for {total} {label} firms\n")
    print(f"{'#':<5} {'Firm':<42} {'Old':>5} {'':>2} {'New':>5} {'Conf':<6} {'Composite'}")
    print("─" * 78)

    for i, firm in enumerate(firms, 1):
        name = firm["name"]
        try:
            growth_text = scrape_growth(name)
            result = score_growth(name, growth_text)

            new_growth = max(1.0, min(5.0, float(result["growth_orientation"])))
            new_conf = result.get("growth_confidence", "low")

            new_composite = compute_composite({
                "cultural_alignment": firm["cultural_alignment"],
                "growth_orientation": new_growth,
                "industry_services":  firm["industry_services"],
                "revenue":            firm["revenue"],
                "employees":          firm["employees"],
                "geography":          firm["geography"],
            })

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE scores SET growth_orientation = ?, growth_confidence = ?, composite = ?
                WHERE id = ?
            """, (new_growth, new_conf, new_composite, firm["score_id"]))
            conn.commit()
            conn.close()

            old = firm["growth_orientation"]
            arrow = "→" if new_growth != old else "="
            conf_flag = "*" if new_conf == "low" else " "
            print(f"{i:<5} {name:<42} {old:>5.1f} {arrow}  {new_growth:>4.1f} {conf_flag}{new_conf:<5} {new_composite:.2f}")

        except Exception as e:
            print(f"{i:<5} {name:<42} {'—':>5}    {'ERR':<6} {e}")

        if i < total:
            time.sleep(random.uniform(6, 10))

    print("─" * 78)
    print(f"\nDone. {total} firms re-scored on growth orientation.")


if __name__ == "__main__":
    main()
