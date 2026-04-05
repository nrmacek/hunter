"""
Scoring engine for Hunter.

Phase 7: real pipeline — scrape public data, score with Claude AI.
Falls back to stub scores if scraping or AI call fails.
"""

import logging
import random

from models import WEIGHTS, compute_composite

logger = logging.getLogger(__name__)


def _stub_score(name: str) -> dict:
    """Deterministic stub scores seeded by firm name. Used as fallback."""
    seed = sum(ord(c) for c in name)
    rng = random.Random(seed)
    criteria = {k: round(rng.uniform(1.0, 5.0), 1) for k in WEIGHTS}
    composite = compute_composite(criteria)
    return {
        "cultural_alignment":   criteria["cultural_alignment"],
        "cultural_confidence":  "low",
        "growth_orientation":   criteria["growth_orientation"],
        "growth_confidence":    "low",
        "industry_services":    criteria["industry_services"],
        "industry_confidence":  "low",
        "revenue":              criteria["revenue"],
        "revenue_confidence":   "low",
        "employees":            criteria["employees"],
        "employees_confidence": "low",
        "geography":            criteria["geography"],
        "geography_confidence": "low",
        "composite":            composite,
        "score_notes":          (
            f"Stub evaluation for {name}. Scoring pipeline failed or was unavailable. "
            "Real data will replace these when scoring is re-run."
        ),
    }


def _get_known_data(firm_name: str) -> dict:
    """
    Look up any pre-existing data for this firm from the DB.
    Returns employees (LinkedIn headcount) only — revenue is excluded because
    the spreadsheet stores sector-specific revenue, not total firm revenue,
    which would score incorrectly. Claude estimates total revenue instead.
    """
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT employees FROM firms WHERE name = ?",
            (firm_name,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "employees": row["employees"],
            }
    except Exception as e:
        logger.debug(f"Could not fetch known data for {firm_name}: {e}")
    return {}


def score_firm(name: str) -> dict:
    """
    Score a firm by name. Runs the real scrape + AI pipeline.
    Returns a dict with all 6 criterion scores, confidence flags,
    composite score, and AI rationale.
    """
    try:
        from scoring.scraper import scrape_firm as do_scrape
        from scoring.ai_scorer import ai_score_firm

        known_data = _get_known_data(name)
        scraped = do_scrape(name)
        result = ai_score_firm(name, scraped, known_data=known_data)
        logger.info(f"Real score for {name}: composite={result['composite']}")
        return result

    except Exception as e:
        logger.error(f"Real scoring failed for {name}: {e}", exc_info=True)
        logger.warning(f"Falling back to stub score for {name}")
        return _stub_score(name)
