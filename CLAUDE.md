# CLAUDE.md — Hunter by Trelity
*Last updated: April 4, 2026*

---

## What This Project Is

**Hunter** is an AI-powered prospect evaluation and ranking tool built for Trelity Inc. — a US-based architecture/engineering outsourcing firm. It takes a list of A/E firm names, scrapes publicly available data, scores each firm against 6 weighted criteria, and displays a ranked list in a visual dashboard.

**Built by:** Nick Macek (AI consultant)  
**For:** John Mickey (CEO) and Jason (Principal BD Lead)  
**Type:** Proof of Concept  
**Repo:** github.com/nrmacek/hunter

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 (FastAPI) |
| Database | SQLite |
| Frontend | Next.js (React) |
| Hosting | Vercel (when ready to share) |
| Scraping | Python + Antigravity browser agents |

---

## Dev Environment

| Item | Value |
|---|---|
| Machine | MacBook Air M1, macOS Tahoe |
| IDE | Google Antigravity |
| Agent | Claude Opus 4.6 (in Antigravity) |
| Terminal agent | Claude Code |
| Python | 3.12.3 via pyenv |
| Node | v22.18.0 |
| Version control | Git + GitHub |

---

## Phase Status

- ✅ Phase 1 — Mac environment (Python 3.12, Homebrew, Node, Git)
- ✅ Phase 2 — GitHub connected, repo created
- ✅ Phase 3 — Folder structure created and pushed
- ✅ Phase 4 — Antigravity configured, Claude Code installed, CLAUDE.md in place
- 🔲 **Phase 5 — Tech stack scaffold (current)**

### Phase 5 is done when:
1. Python backend (FastAPI) can accept a firm name and return a scored JSON object with all 6 criterion scores and a composite score
2. Next.js dashboard renders a ranked list of firms pulled from SQLite
3. Both are running locally and talking to each other

Nothing more is required to call Phase 5 done.

---

## Scoring Model (Confirmed April 2, 2026 — Do Not Change)

### Weights

| # | Criteria | Weight |
|---|---|---|
| 1 | Cultural Alignment | 10% |
| 2 | Growth Orientation | 30% |
| 3 | Type of Industry & Services | 25% |
| 4 | Total Revenue | 15% |
| 5 | # of Employees | 10% |
| 6 | Geography | 10% |
| | **Total** | **100%** |

### Composite Score Formula
```
Score = (C1 × 0.10) + (C2 × 0.30) + (C3 × 0.25) + (C4 × 0.15) + (C5 × 0.10) + (C6 × 0.10)
Max score = 5.0
```

### Scoring Rubric (1–5 per criterion)

**1. Cultural Alignment (10%)**
- 1: Minimal cultural alignment
- 5: Strong alignment — quality focus, employee care, client success orientation
- Sources: Firm website, LinkedIn, Glassdoor, Google Reviews, news

**2. Growth Orientation (30%)**
- 1: Revenue/headcount declining
- 5: >10% Y/Y growth, forward-thinking, actively expanding
- Sources: ENR rankings, LinkedIn job postings, news articles

**3. Type of Industry & Services (25%)**
- Industry score: 1 = serves one Trelity sector; 3 = serves some; 5 = serves all
- Services score: 1 = one matching service; 3 = two or more; 5 = full A/E suite
- Trelity's target sectors: Retail, Restaurant, Multifamily, Industrial, Data Centers, Hospitality
- Full service suite: Architecture, Structural, MEP, Electrical, Plumbing, Civil
- Sources: Firm website

**4. Total Revenue (15%)**
- 1: <$20M or >$1B
- 3: $20M–$100M or $600M–$1B
- 5 (sweet spot): $200M–$400M
- Sources: ENR 500, BDC rankings, Glassdoor, company announcements

**5. # of Employees (10%)**
- 1: <100 or >1,000
- 3: 100–200 or 400–600
- 5 (sweet spot): 200–400
- Sources: LinkedIn, Glassdoor, ENR

**6. Geography (10%)**
- 1: At least one East Coast office (minimum threshold)
- 3: All offices on East Coast or Central time zone
- 5: All offices on East Coast only
- Sources: Firm website office locations

---

## Missing Data Protocol

When a data point cannot be found during scraping or AI evaluation:
- Default score for that criterion: **2**
- Flag the criterion in the database: `data_confidence: "low"`
- Surface the flag visually in the dashboard (muted indicator next to the score)
- Never skip a firm due to missing data — partial scores are valid

---

## Database Schema (SQLite)

### firms
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| name | TEXT | Firm name |
| tier | INTEGER | 1, 2, or 3 |
| source | TEXT | ENR, CenterBuild, BDC, etc. |
| city | TEXT | HQ city |
| state | TEXT | HQ state |
| employees | INTEGER | Headcount |
| revenue_m | REAL | Revenue in millions |
| bd_stage | TEXT | Meet / Met / Get Pilot / Develop / Expand / Maintain |
| notes | TEXT | Free-text BD notes |
| last_contacted | DATE | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### scores
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| firm_id | INTEGER | Foreign key → firms |
| cultural_alignment | REAL | 1–5 |
| cultural_confidence | TEXT | high / low |
| growth_orientation | REAL | 1–5 |
| growth_confidence | TEXT | high / low |
| industry_services | REAL | 1–5 |
| industry_confidence | TEXT | high / low |
| revenue | REAL | 1–5 |
| revenue_confidence | TEXT | high / low |
| employees | REAL | 1–5 |
| employees_confidence | TEXT | high / low |
| geography | REAL | 1–5 |
| geography_confidence | TEXT | high / low |
| composite | REAL | Weighted composite 0–5 |
| scored_at | TIMESTAMP | |
| score_notes | TEXT | AI rationale summary |

---

## API Endpoints (FastAPI Backend)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/score` | Accept firm name, trigger scrape + AI score, return JSON |
| GET | `/firms` | Return all firms with scores, sorted by composite |
| GET | `/firms/{id}` | Return single firm with full score breakdown |
| POST | `/firms` | Add a new firm (single entry) |
| POST | `/firms/bulk` | Bulk import firms from CSV/Excel upload |
| PATCH | `/firms/{id}` | Update BD stage, notes, last contacted |
| GET | `/export` | Return full dataset as CSV download |

---

## Dashboard UX (Confirmed April 4, 2026)

### Access
- Hosted on Vercel — accessible via URL, no install required
- No login required for POC

### Firm Input Methods
1. **Single firm form** — Enter firm name + source tag, submit, system scrapes and scores
2. **Bulk CSV/Excel upload** — Upload a spreadsheet of firm names for batch ingestion (e.g. full CenterBuild list)

### Ranked Table Columns
Rank | Composite Score | Firm Name | Source Tag | Growth | Industry | Revenue | Culture | Employees | Geography | BD Stage

### Filters
- All / Tier 1 / CenterBuild / ≥4.0 score

### Detail Drawer (click any firm)
- Firm name, location, headcount, revenue
- Composite score + rank
- BD stage selector
- AI summary paragraph
- Per-criterion score with rationale and confidence flag
- Notes field with timestamps
- Last contacted date

### CSV Export
One button exports all firms with:
Firm Name | Tier | Source | BD Stage | Last Contacted | Notes | Growth Score | Industry Score | Revenue Score | Culture Score | Employees Score | Geography Score | Composite Score | [Confidence flags per criterion]

---

## Brand Spec

| Element | Value |
|---|---|
| Primary | Navy blue `#1B3A6B` |
| Accent | Chartreuse/lime `#C5D82E` |
| Background | Off-white `#F5F4EF` |
| Typography | Clean sans-serif |
| Aesthetic | Professional, minimal, architecture-appropriate |

Score badge colors: 5 = bright green → 1 = light coral/red

---

## POC Boundaries — Stay Lean

- Public data only. No paid APIs.
- No microservices, queues, or complex infra. FastAPI + SQLite is correct.
- No features not explicitly listed above. When uncertain, do the simpler thing.
- If two valid approaches exist, pick one and note the tradeoff briefly.

---

## Resolved Decisions (Do Not Re-Ask)

| Question | Decision |
|---|---|
| Input mode | Score a provided list — not autonomous discovery |
| n8n integration | Skip for POC — standalone only |
| Data refresh | On-demand per firm |
| Output | Dashboard + CSV export |
| Competitor flag | Display only — do not score |
| Conference scope | CenterBuild only for POC |
| Hosting | Vercel |
| Auth | None for POC |
| BD tracking | Stage + notes + last contacted per firm |

---

## BD Pipeline Stages

1. Meet — Not yet heard of Trelity
2. Met — Introduced, interest unclear
3. Get Pilot — Showed interest
4. Develop — First project done, pursuing repeat work
5. Expand — Finding other divisions/PMs/sectors
6. Maintain — Keep them happy

---

## About Nick

Nick is a product manager and AI consultant — not a coder. Claude Code handles all code execution, debugging, and testing. When communicating:
- Lead with what to do and why
- Explain architectural decisions in plain language
- State assumptions and proceed rather than asking clarifying questions
- Keep responses focused
