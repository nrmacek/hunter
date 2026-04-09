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
   "East Coast" means all Eastern time zone states: ME, NH, VT, MA, RI, CT, NY, NJ, PA, DE, MD, DC, VA, WV, NC, SC, GA, FL.
   "Central" means all Central time zone states: OH, MI, IN, IL, WI, MN, IA, MO, ND, SD, NE, KS, TX, OK, AR, LA, MS, AL, TN, KY.
   Central time zone offices are acceptable and do NOT reduce the score.
   Only Mountain time zone (MT, WY, CO, NM, AZ, UT, ID) or Pacific time zone (WA, OR, CA, NV, HI, AK) offices reduce the score.
   International/offshore offices (e.g. Mexico, India) are IGNORED entirely — do not count them for or against the score.

   HQ location is the primary factor. Score using two steps:

   Step 1 — HQ sets the base:
     East Coast HQ → base 4
     Central time zone HQ → base 3
     Mountain / West Coast HQ → base 1

   Step 2 — US satellite offices adjust (ignore any international/offshore offices):
     All US offices East Coast only → +1
     East Coast + Central mix → 0
     Any Mountain or Pacific time zone US office → −1

   Final = HQ base + modifier, clamped to 1–5.
   Examples: NJ HQ all East Coast = 5 | FL HQ all East Coast = 5 | NJ HQ + Central offices = 4 | NJ HQ + one West Coast = 3 | TX HQ all Central = 3 | Seattle HQ = 1
   If office locations unknown, score 2 and mark confidence low

MISSING DATA RULE: If you cannot find data for a criterion, score it 2 and set confidence to "low".

CONSISTENCY RULE: The ai_summary MUST be consistent with the numeric scores you assign. Do not flag something as a concern or weakness in the summary if it scored 4 or 5. Do not praise something in the summary if it scored 1 or 2. The summary should reflect and explain the scores, not contradict them.

AI SUMMARY FORMAT: Write exactly three short paragraphs separated by \\n\\n:
  Paragraph 1 — Firm overview and fit signal (2–3 sentences): Who the firm is and headline fit assessment.
  Paragraph 2 — Strengths (2–3 sentences): What scored well and why it matters for Trelity's outsourcing model.
  Paragraph 3 — Concerns and next step (2–3 sentences): What scored lower, flags worth noting, and a concrete BD action.
Total length: roughly 6–9 sentences. Punchy and scannable. No exhaustive criterion walkthrough.

Return this exact JSON structure:
{
  "cultural_alignment": <float 1.0–5.0>,
  "cultural_confidence": "<high|low>",
  "cultural_rationale": "<1–2 sentences explaining the cultural alignment score>",
  "cultural_sources": "<comma-separated list of sources used, e.g. 'Firm website About page, Glassdoor reviews'>",
  "growth_orientation": <float 1.0–5.0>,
  "growth_confidence": "<high|low>",
  "growth_rationale": "<1–2 sentences explaining the growth orientation score>",
  "growth_sources": "<sources used>",
  "industry_services": <float 1.0–5.0>,
  "industry_confidence": "<high|low>",
  "industry_rationale": "<1–2 sentences explaining the industry/services score>",
  "industry_sources": "<sources used>",
  "revenue": <float 1.0–5.0>,
  "revenue_confidence": "<high|low>",
  "revenue_rationale": "<1–2 sentences explaining the revenue score>",
  "revenue_sources": "<sources used>",
  "employees": <float 1.0–5.0>,
  "employees_confidence": "<high|low>",
  "employees_rationale": "<1–2 sentences explaining the employees score>",
  "employees_sources": "<sources used>",
  "geography": <float 1.0–5.0>,
  "geography_confidence": "<high|low>",
  "geography_rationale": "<1–2 sentences explaining the geography score>",
  "geography_sources": "<sources used>",
  "ai_summary": "<three short paragraphs per the format above, separated by \\n\\n>",
  "recommendation": "<2–3 sentences advising Trelity's BD team on the most logical next action for this prospect. Consider: any low-confidence scores that need research, the firm's BD stage, strongest alignment areas to lead with, and the best channel for first contact. Be specific and actionable.>"
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


CRITERION_LABELS = {
    "cultural_alignment": "Cultural Alignment",
    "growth_orientation": "Growth Orientation",
    "industry_services": "Industry & Services",
    "revenue": "Revenue",
    "employees": "Employees",
    "geography": "Geography",
}


def ai_rescore_criterion(
    firm_name: str,
    scraped: dict,
    existing_scores: dict,
    criterion: str,
    known_data: dict | None = None,
) -> dict:
    """
    Re-score a single criterion while keeping all others locked.
    Returns a complete score dict with the targeted criterion updated
    and a regenerated ai_summary consistent with all scores.
    """
    client = _get_client()

    # Build locked scores display for the prompt
    locked_lines = []
    for key in WEIGHTS:
        if key == criterion:
            continue
        conf_key = f"{key}_confidence"
        rat_key = f"{key}_rationale"
        locked_lines.append(
            f"  {key}: {existing_scores[key]} "
            f"(confidence: {existing_scores.get(conf_key, 'high')}, "
            f"rationale: \"{existing_scores.get(rat_key, '')}\")"
        )
    locked_block = "\n".join(locked_lines)

    label = CRITERION_LABELS.get(criterion, criterion)

    user_msg = _build_user_message(firm_name, scraped, known_data)
    user_msg += (
        f"\n\n--- TARGETED RE-SCORE ---\n"
        f"You are re-scoring ONLY the \"{criterion}\" criterion for this firm.\n"
        f"The following scores are LOCKED and must NOT be changed:\n"
        f"{locked_block}\n\n"
        f"Re-score ONLY \"{criterion}\" using the rubric above.\n"
        f"Also regenerate the ai_summary paragraph to be consistent with ALL scores "
        f"(the locked ones above plus your new {criterion} score).\n\n"
        f"Return this JSON:\n"
        f"{{\n"
        f"  \"{criterion}\": <float 1.0–5.0>,\n"
        f"  \"{criterion}_confidence\": \"<high|low>\",\n"
        f"  \"{criterion}_rationale\": \"<1–2 sentences>\",\n"
        f"  \"ai_summary\": \"<one paragraph, BD-oriented>\"\n"
        f"}}"
    )

    logger.info(f"Calling Claude API for targeted re-score ({criterion}): {firm_name}")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = message.content[0].text
    logger.debug(f"Claude targeted re-score response for {firm_name}:\n{raw}")

    parsed = _parse_response(raw)

    # Validate the targeted criterion is present
    if criterion not in parsed:
        raise ValueError(f"Missing targeted criterion '{criterion}' in Claude response")
    parsed[criterion] = max(1.0, min(5.0, float(parsed[criterion])))

    # Build result: start from existing, overlay targeted criterion
    result = dict(existing_scores)
    result[criterion] = parsed[criterion]
    result[f"{criterion}_confidence"] = parsed.get(f"{criterion}_confidence", "low")
    result[f"{criterion}_rationale"] = parsed.get(f"{criterion}_rationale", "")
    result["score_notes"] = parsed.get("ai_summary", existing_scores.get("score_notes", ""))
    result["recommendation"] = parsed.get("recommendation", existing_scores.get("recommendation", ""))

    # Recompute composite with the updated criterion
    criteria = {k: result[k] for k in WEIGHTS}
    result["composite"] = compute_composite(criteria)

    return result


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
        max_tokens=2048,
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
        "cultural_rationale":   parsed.get("cultural_rationale", ""),
        "cultural_sources":     parsed.get("cultural_sources", ""),
        "growth_orientation":   parsed["growth_orientation"],
        "growth_confidence":    parsed["growth_confidence"],
        "growth_rationale":     parsed.get("growth_rationale", ""),
        "growth_sources":       parsed.get("growth_sources", ""),
        "industry_services":    parsed["industry_services"],
        "industry_confidence":  parsed["industry_confidence"],
        "industry_rationale":   parsed.get("industry_rationale", ""),
        "industry_sources":     parsed.get("industry_sources", ""),
        "revenue":              parsed["revenue"],
        "revenue_confidence":   parsed["revenue_confidence"],
        "revenue_rationale":    parsed.get("revenue_rationale", ""),
        "revenue_sources":      parsed.get("revenue_sources", ""),
        "employees":            parsed["employees"],
        "employees_confidence": parsed["employees_confidence"],
        "employees_rationale":  parsed.get("employees_rationale", ""),
        "employees_sources":    parsed.get("employees_sources", ""),
        "geography":            parsed["geography"],
        "geography_confidence": parsed["geography_confidence"],
        "geography_rationale":  parsed.get("geography_rationale", ""),
        "geography_sources":    parsed.get("geography_sources", ""),
        "composite":            composite,
        "score_notes":          ai_summary,
        "recommendation":       parsed.get("recommendation", ""),
    }
