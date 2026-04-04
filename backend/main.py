"""
Hunter API — FastAPI backend.

Run with: python main.py
Server starts on http://localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db, get_connection
from models import ScoreRequest, ScoreResponse, ScoreDetail, FirmResponse
from scoring.engine import score_firm


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Hunter by Trelity",
    description="AI-powered prospect evaluation and ranking",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── POST /score ──────────────────────────────────────────────────────────────

@app.post("/score", response_model=ScoreResponse)
def score_endpoint(req: ScoreRequest):
    """
    Accept a firm name, score it, store results in DB, return scored JSON.
    If the firm already exists, re-scores and updates.
    """
    scores = score_firm(req.name)
    conn = get_connection()
    cursor = conn.cursor()

    # Check if firm already exists
    cursor.execute("SELECT id FROM firms WHERE name = ?", (req.name,))
    row = cursor.fetchone()

    if row:
        firm_id = row["id"]
        # Update the existing score
        cursor.execute("DELETE FROM scores WHERE firm_id = ?", (firm_id,))
    else:
        # Insert new firm
        cursor.execute(
            "INSERT INTO firms (name) VALUES (?)",
            (req.name,),
        )
        firm_id = cursor.lastrowid

    # Insert score
    cursor.execute(
        """INSERT INTO scores (
            firm_id,
            cultural_alignment, cultural_confidence,
            growth_orientation, growth_confidence,
            industry_services, industry_confidence,
            revenue, revenue_confidence,
            employees, employees_confidence,
            geography, geography_confidence,
            composite, score_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            firm_id,
            scores["cultural_alignment"], scores["cultural_confidence"],
            scores["growth_orientation"], scores["growth_confidence"],
            scores["industry_services"], scores["industry_confidence"],
            scores["revenue"], scores["revenue_confidence"],
            scores["employees"], scores["employees_confidence"],
            scores["geography"], scores["geography_confidence"],
            scores["composite"], scores["score_notes"],
        ),
    )

    conn.commit()
    conn.close()

    return ScoreResponse(
        firm_id=firm_id,
        name=req.name,
        score=ScoreDetail(**scores),
    )


# ── GET /firms ───────────────────────────────────────────────────────────────

@app.get("/firms", response_model=list[FirmResponse])
def list_firms():
    """Return all firms with their latest scores, sorted by composite descending."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.*, s.cultural_alignment, s.cultural_confidence,
               s.growth_orientation, s.growth_confidence,
               s.industry_services, s.industry_confidence,
               s.revenue AS score_revenue, s.revenue_confidence,
               s.employees AS score_employees, s.employees_confidence,
               s.geography, s.geography_confidence,
               s.composite, s.scored_at, s.score_notes
        FROM firms f
        LEFT JOIN scores s ON s.firm_id = f.id
        ORDER BY s.composite DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        firm = FirmResponse(
            id=row["id"],
            name=row["name"],
            tier=row["tier"],
            source=row["source"],
            city=row["city"],
            state=row["state"],
            employees=row["employees"],
            revenue_m=row["revenue_m"],
            bd_stage=row["bd_stage"],
            notes=row["notes"],
            last_contacted=row["last_contacted"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            score=ScoreDetail(
                cultural_alignment=row["cultural_alignment"],
                cultural_confidence=row["cultural_confidence"],
                growth_orientation=row["growth_orientation"],
                growth_confidence=row["growth_confidence"],
                industry_services=row["industry_services"],
                industry_confidence=row["industry_confidence"],
                revenue=row["score_revenue"],
                revenue_confidence=row["revenue_confidence"],
                employees=row["score_employees"],
                employees_confidence=row["employees_confidence"],
                geography=row["geography"],
                geography_confidence=row["geography_confidence"],
                composite=row["composite"],
                scored_at=row["scored_at"],
                score_notes=row["score_notes"],
            ) if row["composite"] is not None else None,
        )
        results.append(firm)

    return results


# ── GET /firms/{id} ──────────────────────────────────────────────────────────

@app.get("/firms/{firm_id}", response_model=FirmResponse)
def get_firm(firm_id: int):
    """Return a single firm with full score breakdown."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT f.*, s.cultural_alignment, s.cultural_confidence,
               s.growth_orientation, s.growth_confidence,
               s.industry_services, s.industry_confidence,
               s.revenue AS score_revenue, s.revenue_confidence,
               s.employees AS score_employees, s.employees_confidence,
               s.geography, s.geography_confidence,
               s.composite, s.scored_at, s.score_notes
        FROM firms f
        LEFT JOIN scores s ON s.firm_id = f.id
        WHERE f.id = ?
    """, (firm_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Firm not found")

    return FirmResponse(
        id=row["id"],
        name=row["name"],
        tier=row["tier"],
        source=row["source"],
        city=row["city"],
        state=row["state"],
        employees=row["employees"],
        revenue_m=row["revenue_m"],
        bd_stage=row["bd_stage"],
        notes=row["notes"],
        last_contacted=row["last_contacted"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        score=ScoreDetail(
            cultural_alignment=row["cultural_alignment"],
            cultural_confidence=row["cultural_confidence"],
            growth_orientation=row["growth_orientation"],
            growth_confidence=row["growth_confidence"],
            industry_services=row["industry_services"],
            industry_confidence=row["industry_confidence"],
            revenue=row["score_revenue"],
            revenue_confidence=row["revenue_confidence"],
            employees=row["score_employees"],
            employees_confidence=row["employees_confidence"],
            geography=row["geography"],
            geography_confidence=row["geography_confidence"],
            composite=row["composite"],
            scored_at=row["scored_at"],
            score_notes=row["score_notes"],
        ) if row["composite"] is not None else None,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
