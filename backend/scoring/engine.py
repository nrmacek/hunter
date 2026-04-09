"""
Scoring engine for Hunter.

Phase 7+: real pipeline — scrape public data, score with Claude AI.
Supports scraped data caching and targeted single-criterion re-scoring.
Falls back to stub scores if scraping or AI call fails.
"""

import json
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
            "SELECT employees, website FROM firms WHERE name = ?",
            (firm_name,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            data = {"employees": row["employees"]}
            if row["website"]:
                data["website"] = row["website"]
            return data
    except Exception as e:
        logger.debug(f"Could not fetch known data for {firm_name}: {e}")
    return {}


def _get_cached_scrape(firm_name: str) -> dict | None:
    """Return cached scraped data for a firm, or None if not cached."""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sc.scraped_json FROM scraped_cache sc
            JOIN firms f ON f.id = sc.firm_id
            WHERE f.name = ?
        """, (firm_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row["scraped_json"])
    except Exception as e:
        logger.debug(f"Could not fetch cached scrape for {firm_name}: {e}")
    return None


def _save_scraped_cache(firm_name: str, scraped: dict) -> None:
    """Store scraped data in the cache, replacing any existing entry."""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM firms WHERE name = ?", (firm_name,))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                INSERT INTO scraped_cache (firm_id, scraped_json, scraped_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(firm_id) DO UPDATE SET
                    scraped_json = excluded.scraped_json,
                    scraped_at = excluded.scraped_at
            """, (row["id"], json.dumps(scraped)))
            conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"Could not save scraped cache for {firm_name}: {e}")


def _get_existing_scores(firm_name: str) -> dict | None:
    """Load the current scores from the DB for a firm. Returns None if not scored."""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.* FROM scores s
            JOIN firms f ON f.id = s.firm_id
            WHERE f.name = ?
        """, (firm_name,))
        row = cursor.fetchone()
        conn.close()
        if row and row["composite"] is not None:
            return {
                "cultural_alignment":   row["cultural_alignment"],
                "cultural_confidence":  row["cultural_confidence"],
                "cultural_rationale":   row["cultural_rationale"],
                "growth_orientation":   row["growth_orientation"],
                "growth_confidence":    row["growth_confidence"],
                "growth_rationale":     row["growth_rationale"],
                "industry_services":    row["industry_services"],
                "industry_confidence":  row["industry_confidence"],
                "industry_rationale":   row["industry_rationale"],
                "revenue":              row["revenue"],
                "revenue_confidence":   row["revenue_confidence"],
                "revenue_rationale":    row["revenue_rationale"],
                "employees":            row["employees"],
                "employees_confidence": row["employees_confidence"],
                "employees_rationale":  row["employees_rationale"],
                "geography":            row["geography"],
                "geography_confidence": row["geography_confidence"],
                "geography_rationale":  row["geography_rationale"],
                "composite":            row["composite"],
                "score_notes":          row["score_notes"],
            }
    except Exception as e:
        logger.debug(f"Could not fetch existing scores for {firm_name}: {e}")
    return None


def score_firm(name: str, criterion: str | None = None, refresh: bool = False) -> dict:
    """
    Score a firm by name.

    Args:
        name: Firm name to score.
        criterion: If set, only re-score this single criterion (e.g. 'geography').
                   All other scores are kept from the existing DB record.
        refresh: If True, force a fresh scrape even if cached data exists.

    Returns a dict with all 6 criterion scores, confidence flags,
    composite score, and AI rationale.
    """
    try:
        from scoring.scraper import scrape_firm as do_scrape
        from scoring.ai_scorer import ai_score_firm, ai_rescore_criterion

        known_data = _get_known_data(name)

        # ── Resolve scraped data: use cache unless refreshing ──
        scraped = None
        if not refresh:
            scraped = _get_cached_scrape(name)
            if scraped:
                logger.info(f"Using cached scrape for {name}")

        if scraped is None:
            website = known_data.get("website")
            scraped = do_scrape(name, website_url=website)
            _save_scraped_cache(name, scraped)
            logger.info(f"Fresh scrape completed and cached for {name}")

        # ── Targeted single-criterion re-score ──
        if criterion:
            existing = _get_existing_scores(name)
            if not existing:
                logger.warning(f"No existing scores for {name} — falling back to full score")
            else:
                result = ai_rescore_criterion(name, scraped, existing, criterion, known_data=known_data)
                logger.info(f"Targeted re-score ({criterion}) for {name}: composite={result['composite']}")
                return result

        # ── Full score ──
        result = ai_score_firm(name, scraped, known_data=known_data)
        logger.info(f"Full score for {name}: composite={result['composite']}")
        return result

    except Exception as e:
        logger.error(f"Real scoring failed for {name}: {e}", exc_info=True)
        logger.warning(f"Falling back to stub score for {name}")
        return _stub_score(name)
