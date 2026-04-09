"""
Pydantic models for Hunter API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Weights (from CLAUDE.md — do not change) ─────────────────────────────────

WEIGHTS = {
    "cultural_alignment": 0.10,
    "growth_orientation": 0.30,
    "industry_services": 0.25,
    "revenue": 0.15,
    "employees": 0.10,
    "geography": 0.10,
}

CRITERION_KEYS = list(WEIGHTS.keys())


def compute_composite(scores: dict) -> float:
    """
    Compute weighted composite score.
    scores dict must have keys matching WEIGHTS keys, values 1–5.
    Returns float rounded to 2 decimal places, max 5.0.
    """
    total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    return round(total, 2)


# ── Request Models ────────────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    name: str = Field(..., description="Firm name to score")
    criterion: Optional[str] = Field(None, description="Single criterion to re-score (e.g. 'geography'). Omit for full re-score.")
    refresh: bool = Field(False, description="Force fresh scrape even if cached data exists")


class FirmCreate(BaseModel):
    name: str
    source: Optional[str] = None
    website: Optional[str] = None


class FirmUpdate(BaseModel):
    bd_stage: Optional[str] = None
    last_contacted: Optional[str] = None
    note_text: Optional[str] = None  # Appended as a timestamped entry


class ScoreOverride(BaseModel):
    score: float = Field(..., ge=1.0, le=5.0)
    note: Optional[str] = None


# ── Response Models ───────────────────────────────────────────────────────────

class ScoreDetail(BaseModel):
    cultural_alignment: float
    cultural_confidence: str
    cultural_rationale: Optional[str] = None
    cultural_sources: Optional[str] = None
    cultural_override: Optional[float] = None
    cultural_override_note: Optional[str] = None
    cultural_override_at: Optional[str] = None
    growth_orientation: float
    growth_confidence: str
    growth_rationale: Optional[str] = None
    growth_sources: Optional[str] = None
    growth_override: Optional[float] = None
    growth_override_note: Optional[str] = None
    growth_override_at: Optional[str] = None
    industry_services: float
    industry_confidence: str
    industry_rationale: Optional[str] = None
    industry_sources: Optional[str] = None
    industry_override: Optional[float] = None
    industry_override_note: Optional[str] = None
    industry_override_at: Optional[str] = None
    revenue: float
    revenue_confidence: str
    revenue_rationale: Optional[str] = None
    revenue_sources: Optional[str] = None
    revenue_override: Optional[float] = None
    revenue_override_note: Optional[str] = None
    revenue_override_at: Optional[str] = None
    employees: float
    employees_confidence: str
    employees_rationale: Optional[str] = None
    employees_sources: Optional[str] = None
    employees_override: Optional[float] = None
    employees_override_note: Optional[str] = None
    employees_override_at: Optional[str] = None
    geography: float
    geography_confidence: str
    geography_rationale: Optional[str] = None
    geography_sources: Optional[str] = None
    geography_override: Optional[float] = None
    geography_override_note: Optional[str] = None
    geography_override_at: Optional[str] = None
    composite: float
    scored_at: Optional[str] = None
    score_notes: Optional[str] = None
    is_real_score: int = 0


class FirmResponse(BaseModel):
    id: int
    name: str
    tier: Optional[int] = None
    source: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    employees: Optional[int] = None
    revenue_m: Optional[float] = None
    bd_stage: Optional[str] = None
    notes: Optional[str] = None
    last_contacted: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    score: Optional[ScoreDetail] = None


class ScoreResponse(BaseModel):
    firm_id: int
    name: str
    score: ScoreDetail
