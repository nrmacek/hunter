"""
Stub scoring engine for Phase 5.

Generates plausible mock scores for a firm. This module will be replaced
with real scraping + AI evaluation in a later phase.
"""

import random
from models import WEIGHTS, compute_composite


def score_firm(name: str) -> dict:
    """
    Score a firm by name. Returns a dict with all 6 criterion scores,
    confidence flags, composite score, and a rationale string.

    Phase 5: uses deterministic-ish random scores seeded by firm name
    so repeated calls return the same scores for the same firm.
    """
    # Seed by firm name so scores are stable across calls
    seed = sum(ord(c) for c in name)
    rng = random.Random(seed)

    criteria = {}
    confidences = {}

    for key in WEIGHTS:
        # Generate a score between 1.0 and 5.0, rounded to 1 decimal
        criteria[key] = round(rng.uniform(1.0, 5.0), 1)
        # All stub scores are low confidence
        confidences[key] = "low"

    composite = compute_composite(criteria)

    rationale = (
        f"Stub evaluation for {name}. Scores are placeholder values "
        f"generated for Phase 5 scaffolding. Real data will replace these "
        f"when scraping and AI scoring are implemented."
    )

    return {
        "cultural_alignment": criteria["cultural_alignment"],
        "cultural_confidence": confidences["cultural_alignment"],
        "growth_orientation": criteria["growth_orientation"],
        "growth_confidence": confidences["growth_orientation"],
        "industry_services": criteria["industry_services"],
        "industry_confidence": confidences["industry_services"],
        "revenue": criteria["revenue"],
        "revenue_confidence": confidences["revenue"],
        "employees": criteria["employees"],
        "employees_confidence": confidences["employees"],
        "geography": criteria["geography"],
        "geography_confidence": confidences["geography"],
        "composite": composite,
        "score_notes": rationale,
    }
