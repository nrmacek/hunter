# CLAUDE.md — Hunter by Trelity
*Last updated: April 4, 2026*

---

## What This Project Is

**Hunter** is an AI-powered prospect evaluation and ranking tool built for Trelity Inc. — a US-based architecture/engineering outsourcing firm. It takes a list of A/E firm names, scrapes publicly available data, scores each firm against 6 weighted criteria, and displays a ranked list in a visual dashboard.

**Built by:** Nick Macek (AI consultant, Armatura)
**For:** John Mickey (CEO) and Jason (Principal BD Lead), Trelity Inc.
**Type:** Proof of Concept
**Repo:** github.com/nrmacek/hunter

---

## Repo Structure

```
hunter/
├── CLAUDE.md          ← this file, always in repo root
├── README.md
├── backend/           ← Python FastAPI + SQLite
├── dashboard/         ← Next.js frontend
│   ├── public/
│   │   └── TrelityLogo.png   ← Trelity logo, already in place
│   └── src/
├── data/
├── docs/
├── scripts/
└── tests/
```

Note: There may be additional CLAUDE.md files inside `backend/` or `dashboard/` from earlier setup. Those should be deleted — this root-level file is the single source of truth.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 (FastAPI) |
| Database | SQLite |
| Frontend | Next.js (React) — lives in `dashboard/` |
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
- ✅ Phase 5 — Tech stack scaffold (FastAPI backend + SQLite + Next.js dashboard running locally)
- ✅ Phase 6 — Real firm data in (120 firms: 34 Tier 1 + 72 Tier 2 + 14 Tier 3, stub scores)
- 🔲 **Phase 7 — Real scraping and AI scoring (current)**
- 🔲 Phase 8 — Full UX (drawer, BD tracking, bulk upload, CSV export)
- 🔲 Phase 9 — Vercel deploy

---

## Phase Definitions

### Phase 6 — Real Firm Data
Replace the 5 seed firms with real firm names from the Master Target List Excel file (`data/Master_Target_List_2_0.xlsx`). Scores remain stub values for now. Done when all Tier 1, Tier 2, and Tier 3 firms are in the database.

### Phase 7 — Real Scraping and AI Scoring
Replace stub scorer with real data collection and AI evaluation. Done when each firm has scores derived from actual public data sources, with confidence flags on any criterion where data could not be found.

### Phase 8 — Full UX
Phase 8 is complete when all of the following are built and working:

#### 1. Firm Detail Drawer
Clicking any row in the ranked table opens a right-side panel containing:
- Firm name, location, headcount, revenue
- Composite score badge + rank (e.g. "Rank #1 of 120 prospects")
- BD stage selector (dropdown: Meet / Met / Get Pilot / Develop / Expand / Maintain)
- AI summary paragraph — one paragraph, BD-oriented, explains why this firm fits Trelity
- Per-criterion score breakdown:
  - Score badge (1–5, color coded)
  - Criterion name and weight
  - Rationale text (1–2 sentences from AI)
  - Confidence indicator if low confidence
- Timestamped notes field — free text, each entry logged with date/time
- Last contacted date picker
- Close button returns to full table view

#### 2. Single Firm Add Form
A form in the dashboard to add one firm at a time:
- Input: firm name + source tag
- On submit: queues firm for scraping and AI scoring
- Firm appears in ranked table when scoring completes

#### 3. Bulk CSV/Excel Upload
Upload a spreadsheet of firm names for batch ingestion:
- Accepts .csv or .xlsx
- Maps firm name and source tag columns
- Triggers batch scoring on all uploaded firms

#### 4. CSV Export
One button exports the full ranked list as a CSV with these columns:
Firm Name | Tier | Source | BD Stage | Last Contacted | Notes | Growth Score | Industry Score | Revenue Score | Culture Score | Employees Score | Geography Score | Composite Score | Confidence flags per criterion

### Phase 9 — Vercel Deploy
Push to Vercel. Done when Jason and John can access the dashboard via URL without Nick's machine running.

---

## Branding & Header Spec (Confirmed April 4, 2026)

### Tool Name
**Trelity Prospect Hunter**
Subtext: **BY ARMATURA** — lighter gray, smaller font, all caps, same line or directly below

### Header Layout
- Logo: `TrelityLogo.png` from `dashboard/public/TrelityLogo.png`
  - Render as `<img src="/TrelityLogo.png" />` in the header component
  - Height: 32–36px, width auto, vertically centered in header
  - Replaces any placeholder grid or "H" icon entirely
- Title: "Trelity Prospect Hunter" in white, clean sans-serif, medium weight
- Subtext: "BY ARMATURA" in lighter gray (#A0A8B8 or similar), smaller (11–12px), all caps, letter-spaced
- Header background: Navy `#1B3A6B`

### Brand Colors
| Element | Value |
|---|---|
| Primary | Navy blue `#1B3A6B` |
| Accent | Chartreuse/lime `#C5D82E` |
| Background | Off-white `#F5F4EF` |
| Header text | White |
| Subtext | Light gray `#A0A8B8` |
| Typography | Clean sans-serif |

Score badge colors: 5 = bright green → 1 = light coral/red

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

## Phase 7 — Data Collection Spec

For each firm, the scraper fetches from these sources and extracts the following signals. This is the blueprint for what each browser agent call must return before the scoring engine evaluates it.

### Sources Per Firm

| Source | Method | Used For |
|---|---|---|
| Firm website | Direct fetch | Industry sectors, services, office locations, culture cues |
| Google Search | Search query | ENR/BDC revenue mentions, press releases, news |
| Google News | Search query | Growth signals, expansions, new offices, awards, layoffs |
| Glassdoor | Browser agent | Employee sentiment, headcount, revenue estimate |
| LinkedIn (via Google) | Google search | Employee count, job posting volume, growth signals |

### What to Extract Per Criterion

**Growth Orientation (30%)**
- YoY ENR ranking change (this year vs. last year)
- LinkedIn headcount trend and active job posting count
- News mentions of: new office openings, acquisitions, new market entries, layoffs, downsizing
- Forward-looking language in press releases or news

Score signal: Numeric ranking change is strongest. Job posting volume and expansion news are supporting signals. Layoff or decline news overrides positive signals.

**Industry & Services (25%)**
- Firm website project portfolio pages — which of Trelity's 6 sectors appear: Retail, Restaurant, Multifamily, Industrial, Data Centers, Hospitality
- Firm website services pages — which disciplines offered: Architecture, Structural, MEP, Electrical, Plumbing, Civil

Score signal: Count of Trelity sectors represented + count of matching services. Both feed into the score.

**Total Revenue (15%)**
- ENR 500 ranking and revenue figure
- BDC Top 50 listing
- Press releases mentioning annual revenue
- Glassdoor revenue estimate
- News articles referencing firm size or revenue

Score signal: A dollar figure. $200M–$400M = 5. Score lower per rubric outside that range.

**Cultural Alignment (10%)**
- Glassdoor overall rating and recurring themes in reviews
- Firm website About/Culture/Values pages
- LinkedIn posts — what they celebrate, share, and promote
- Awards: Best Places to Work, AIA recognition, industry honors
- Google Reviews where applicable

Score signal: AI reads sentiment and themes. Green flags: quality, collaboration, client success, employee development. Red flags: high turnover mentions, cost-cutting culture, chaotic or negative review patterns.

**# of Employees (10%)**
- LinkedIn company page employee count
- ENR 500 headcount figure
- Glassdoor company profile
- Press releases mentioning team size

Score signal: A headcount number. 200–400 = 5. Objective once number is found.

**Geography (10%)**
- Firm website Offices or Locations page
- List of all office cities and states
- Map each office city to its time zone

Score signal: All East Coast = 5. Mix of East + Central = 3. Any West Coast office = 1.

### Scoring Engine Input Format
After scraping, all collected text is passed to Claude via the Anthropic API with the full rubric. Claude returns a structured JSON object:

```json
{
  "cultural_alignment": { "score": 4, "confidence": "high", "rationale": "..." },
  "growth_orientation": { "score": 5, "confidence": "high", "rationale": "..." },
  "industry_services": { "score": 3, "confidence": "low", "rationale": "..." },
  "revenue": { "score": 5, "confidence": "high", "rationale": "..." },
  "employees": { "score": 4, "confidence": "high", "rationale": "..." },
  "geography": { "score": 3, "confidence": "high", "rationale": "..." },
  "composite": 4.15,
  "ai_summary": "One paragraph BD-oriented summary of the firm's fit for Trelity."
}
```

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
All / Tier 1 / CenterBuild / ≥4.0 score

### Firm Detail Drawer (Phase 8)
Clicking any row in the ranked table opens a right-side panel. The drawer contains:
- Firm name, location, headcount, revenue
- Composite score badge + rank (e.g. "Rank #1 of 283 prospects")
- BD stage selector (dropdown: Meet / Met / Get Pilot / Develop / Expand / Maintain)
- AI summary paragraph (one paragraph, BD-oriented, explains why this firm fits Trelity)
- Per-criterion score breakdown:
  - Score badge (1–5, color coded)
  - Criterion name and weight
  - Rationale text (1–2 sentences from AI)
  - Confidence flag if data_confidence is low
- Notes field — free text, timestamped entries
- Last contacted date picker
- Close button returns to full table view

### CSV Export
One button exports all firms with:
Firm Name | Tier | Source | BD Stage | Last Contacted | Notes | Growth Score | Industry Score | Revenue Score | Culture Score | Employees Score | Geography Score | Composite Score | Confidence flags per criterion

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
| Scoring execution | Synchronous for POC — firm submitted, user waits for score |
| Frontend folder | `dashboard/` (not `frontend/`) |
| Logo | TrelityLogo.png in `dashboard/public/` |

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

Nick is a product manager and AI consultant (Armatura) — not a coder. Claude Code handles all code execution, debugging, and testing. When communicating:
- Lead with what to do and why
- Explain architectural decisions in plain language
- State assumptions and proceed rather than asking clarifying questions
- Keep responses focused
