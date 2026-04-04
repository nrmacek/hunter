"""
Phase 7 AI scorer — calls Claude API with scraped text and the full rubric,
returns a structured score dict matching Hunter's DB schema.
"""

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import anthropic

from models import WEIGHTS, compute_composite

# Load .env from backend/
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in backend/.env")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ── Rubric prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a business development analyst evaluating architecture and engineering firms as potential outsourcing partners for Trelity Inc., a US-based A/E outsourcing firm.

Trelity's target sectors: Retail, Restaurant, Multifamily, Industrial, Data Centers, Hospitality
Trelity's service suite: Architecture, Structural, MEP, Electrical, Plumbing, Civil

You will receive scraped public data about a firm. Score it on 6 criteria using a 1–5 scale per the rubric below. Then return ONLY a valid JSON object — no prose, no markdown, no explanation outside the JSON.

SCORING RUBRIC:

1. cultural_alignment (weight 10%)
   1 = Minimal cultural alignment
   3 = Some alignment
   5 = Strong alignment — quality focus, employee care, client success orientation
   Sources: website About/Values, Glassdoor themes, LinkedIn posts, awards

2. growth_orientation (weight 30%)
   1 = Revenue/headcount declining
   3 = Stable, modest growth
   5 = >10% Y/Y growth, actively expanding, forward-thinking
   Sources: ENR ranking change YoY, job postings, office openings, acquisition news
   Note: Layoff or decline news overrides positive signals

3. industry_services (weight 25%)
   Industry score: 1 = serves 1 Trelity sector; 3 = serves 3; 5 = serves all 6
   Services score: 1 = 1 matching discipline; 3 = 2–3; 5 = full suite
   Combined: average of both sub-scores
   Trelity sectors: Retail, Restaurant, Multifamily, Industrial, Data Centers, Hospitality
   Matching disciplines: Architecture, Structural, MEP, Electrical, Plumbing, Civil

4. revenue (weight 15%)
   1 = <$20M or >$1B
   2 = $20M–$50M or $750M–$1B
   3 = $50M–$100M or $500M–$750M
   4 = $100M–$200M or $400M–$500M
   5 = $200M–$400M (sweet spot)
   If revenue unknown, score 2 and mark confidence low

5. employees (weight 10%)
   1 = <100 or >1,000
   2 = 100–150 or 600–1,000
   3 = 150–200 or 400–600
   4 = 200–250 or 300–400
   5 = 250–350 (sweet spot)
   If headcount unknown, score 2 and mark confidence low

6. geography (weight 10%)
   1 = Any West Coast or international offices (outside US East/Central)
   3 = All offices East Coast + Central time zone mix
   5 = All offices East Coast only
   If office locations unknown, score 2 and mark confidence low

MISSING DATA RULE: If you cannot find data for a criterion, score it 2 and set confidence to "low".

Return this exact JSON structure:
{
  "cultural_alignment": <float 1.0–5.0>,
  "cultural_confidence": "<high|low>",
  "growth_orientation": <float 1.0–5.0>,
  "growth_confidence": "<high|low>",
  "industry_services": <float 1.0–5.0>,
  "industry_confidence": "<high|low>",
  "revenue": <float 1.0–5.0>,
  "revenue_confidence": "<high|low>",
  "employees": <float 1.0–5.0>,
  "employees_confidence": "<high|low>",
  "geography": <float 1.0–5.0>,
  "geography_confidence": "<high|low>",
  "ai_summary": "<one paragraph, BD-oriented, explains why this firm fits or doesn't fit Trelity>"
}"""


def _build_user_message(firm_name: str, scraped: dict, known_data: dict | None = None) -> str:
    parts = [f"FIRM: {firm_name}\n"]

    # Known facts from database (pre-verified, use directly for revenue/employees)
    if known_data:
        if known_data.get("revenue_m") is not None:
            parts.append(f"KNOWN REVENUE: ${known_data['revenue_m']:.1f}M (use this to score the revenue criterion — do not default to 2)\n")
        if known_data.get("employees") is not None:
            parts.append(f"KNOWN HEADCOUNT: {known_data['employees']} employees (use this to score the employees criterion — do not default to 2)\n")

    if scraped.get("website_url"):
        parts.append(f"Website: {scraped['website_url']}\n")

    if scraped.get("overview"):
        parts.append(f"--- OVERVIEW & LOCATION SIGNALS ---\n{scraped['overview'][:2000]}\n")

    if scraped.get("growth"):
        parts.append(f"--- GROWTH & NEWS SIGNALS ---\n{scraped['growth'][:2500]}\n")

    if scraped.get("geography"):
        parts.append(f"--- OFFICE LOCATIONS ---\n{scraped['geography'][:1500]}\n")

    if scraped.get("industry_services"):
        parts.append(f"--- SERVICES & SECTORS (website) ---\n{scraped['industry_services'][:3000]}\n")

    parts.append("\nScore this firm using the rubric. Return only the JSON object.")
    return "\n".join(parts)


def _parse_response(text: str) -> dict:
    """Extract JSON from Claude's response, tolerating minor formatting noise."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    # Find the outermost JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in response: {text[:200]}")
    return json.loads(text[start:end])


def ai_score_firm(firm_name: str, scraped: dict, known_data: dict | None = None) -> dict:
    """
    Call Claude API with scraped data. Returns a score dict matching the DB schema.
    Falls back to stub scores if the API call fails.
    """
    client = _get_client()
    user_msg = _build_user_message(firm_name, scraped, known_data)

    logger.info(f"Calling Claude API for: {firm_name}")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = message.content[0].text
    logger.debug(f"Claude raw response for {firm_name}:\n{raw}")

    parsed = _parse_response(raw)

    # Validate all required keys are present
    required = ["cultural_alignment", "growth_orientation", "industry_services",
                "revenue", "employees", "geography"]
    for key in required:
        if key not in parsed:
            raise ValueError(f"Missing key in Claude response: {key}")
        # Clamp scores to 1.0–5.0
        parsed[key] = max(1.0, min(5.0, float(parsed[key])))
        conf_key = f"{key}_confidence"
        if conf_key not in parsed:
            parsed[conf_key] = "low"

    criteria = {k: parsed[k] for k in required}
    composite = compute_composite(criteria)

    ai_summary = parsed.get("ai_summary", "")

    return {
        "cultural_alignment":   parsed["cultural_alignment"],
        "cultural_confidence":  parsed["cultural_confidence"],
        "growth_orientation":   parsed["growth_orientation"],
        "growth_confidence":    parsed["growth_confidence"],
        "industry_services":    parsed["industry_services"],
        "industry_confidence":  parsed["industry_confidence"],
        "revenue":              parsed["revenue"],
        "revenue_confidence":   parsed["revenue_confidence"],
        "employees":            parsed["employees"],
        "employees_confidence": parsed["employees_confidence"],
        "geography":            parsed["geography"],
        "geography_confidence": parsed["geography_confidence"],
        "composite":            composite,
        "score_notes":          ai_summary,
    }
