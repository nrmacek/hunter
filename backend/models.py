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


class FirmCreate(BaseModel):
    name: str
    tier: Optional[int] = None
    source: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    employees: Optional[int] = None
    revenue_m: Optional[float] = None
    bd_stage: str = "Meet"
    notes: Optional[str] = None


# ── Response Models ───────────────────────────────────────────────────────────

class ScoreDetail(BaseModel):
    cultural_alignment: float
    cultural_confidence: str
    growth_orientation: float
    growth_confidence: str
    industry_services: float
    industry_confidence: str
    revenue: float
    revenue_confidence: str
    employees: float
    employees_confidence: str
    geography: float
    geography_confidence: str
    composite: float
    scored_at: Optional[str] = None
    score_notes: Optional[str] = None


class FirmResponse(BaseModel):
    id: int
    name: str
    tier: Optional[int] = None
    source: Optional[str] = None
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
