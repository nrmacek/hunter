# CLAUDE.md — Trelity Prospect Scout
*Last updated: April 8, 2026*

---

## What This Project Is

**Trelity Prospect Scout** is an AI-powered prospect evaluation and ranking tool built for Trelity Inc. — a US-based architecture/engineering outsourcing firm. It takes a list of A/E firm names, scrapes publicly available data, scores each firm against 6 weighted criteria, and displays a ranked list in a visual dashboard.

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
│   └── scoring/
│       ├── scraper.py
│       ├── ai_scorer.py
│       └── engine.py
├── dashboard/         ← Next.js frontend
│   ├── public/
│   │   └── TrelityLogo.png
│   └── src/app/
│       └── page.js
├── data/              ← Excel source files
├── docs/              ← SCORING_PLAYBOOK.md lives here
├── scripts/           ← batch_score.py, import_firms.py, audit_firm.py, rescore_growth.py
└── tests/
```

Note: CLAUDE.md belongs in the repo root only. Delete any copies inside backend/ or dashboard/.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 (FastAPI) |
| Database | SQLite |
| Frontend | Next.js (React) — lives in `dashboard/` |
| Hosting | Vercel (when ready to share) |
| Scraping | Python HTTP fetching + DDG search |

---

## Dev Environment

| Item | Value |
|---|---|
| Machine | MacBook Air M1, macOS Tahoe |
| IDE | Google Antigravity |
| Agent | Claude Opus 4.6 (in Antigravity) |
| Terminal agent | Claude Code (Claude Pro subscription) |
| Python | 3.12.3 via pyenv |
| Node | v22.18.0 |
| Version control | Git + GitHub |

---

## Phase Status

- ✅ Phase 1 — Mac environment
- ✅ Phase 2 — GitHub connected, repo created
- ✅ Phase 3 — Folder structure created and pushed
- ✅ Phase 4 — Antigravity configured, Claude Code installed, CLAUDE.md in place
- ✅ Phase 5 — Tech stack scaffold (FastAPI + SQLite + Next.js running locally)
- ✅ Phase 6 — Real firm data loaded (120 firms from Master Target List)
- ✅ Phase 7 — Real scraping and AI scoring (120/120 firms AI-scored)
- 🔲 **Phase 8 — Full UX (current)**
- 🔲 Phase 9 — Vercel deploy

---

## Phase 8 — Full UX

Phase 8 is complete when all of the following are built and working:

### 1. Firm Detail Drawer ✅ (partially complete)
Clicking any row in the ranked table opens a right-side panel. The following are confirmed built:
- Firm name, location, headcount, revenue
- Composite score badge + rank
- BD stage selector (saves immediately)
- Last contacted date picker (saves immediately)
- AI summary (see format spec below)
- Per-criterion score breakdown with badge, name, weight, rationale, confidence dot
- Timestamped notes field
- Close button

The following still need to be added to the drawer:

**Expandable criterion rationale:**
Each criterion row in the drawer is clickable. Clicking it expands to show:
- The AI's rationale text for that score
- Specific data points found (e.g. "629 employees — source: LinkedIn")
- Source name or URL where data was found
- Confidence level

**Manual score override:**
A pencil icon sits next to each criterion score badge. Clicking it allows the user to:
- Change the score from 1–5
- Add a short note explaining why (e.g. "Miami office is small delivery team, not a true geographic expansion")
- Save — composite recalculates instantly
- Original AI score remains visible alongside the override for reference
- Override is stored in the database with timestamp and note

### 2. AI Summary Format (updated)
The AI summary in the drawer must follow this format — three short paragraphs, not one long block:

**Paragraph 1 — Firm overview and fit signal** (2–3 sentences)
Who the firm is and the headline assessment of their fit for Trelity.

**Paragraph 2 — Strengths** (2–3 sentences)
What scored well and why it matters specifically for Trelity's outsourcing model.

**Paragraph 3 — Concerns and recommended next step** (2–3 sentences)
What scored lower or is uncertain, any flags worth noting, and a concrete BD action recommendation.

Total length: roughly half the length of a single dense paragraph. Punchy and scannable. No run-on lists. No exhaustive criterion-by-criterion walkthrough — that's what the score breakdown is for.

### 3. Single Firm Add Form
- Input: firm name + source tag
- On submit: queues firm for scraping and AI scoring
- Firm appears in ranked table when scoring completes

### 4. Bulk CSV/Excel Upload
- Accepts .csv or .xlsx
- Maps firm name and source tag columns
- Triggers batch scoring on all uploaded firms

### 5. CSV Export
One button exports the full ranked list as CSV:
Firm Name | Tier | Source | BD Stage | Last Contacted | Notes | Growth Score | Industry Score | Revenue Score | Culture Score | Employees Score | Geography Score | Composite Score | Confidence flags per criterion

---

## Scoring Model (Confirmed April 2, 2026 — Do Not Change Weights)

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

---

## Scoring Rubric — Complete 1–5 Scale (Updated April 8, 2026)

### 1. Cultural Alignment (10%)
- **1:** Minimal alignment or no concern for corporate culture
- **2:** Limited cultural signals — generic corporate language, no evidence of employee care or quality focus
- **3:** Some cultural alignment visible — quality or employee focus mentioned but not central to firm identity
- **4:** Clear cultural alignment — quality and employee focus evident but not a defining characteristic of the firm's identity
- **5:** Strong cultural alignment with Trelity. Focused on providing top quality services and deliverables. Focused on care for their employees and care for their client's success.
- **Sources:** Firm website, LinkedIn posts, Glassdoor, Google Reviews, news articles

### 2. Growth Orientation (30%)
- **1:** Steady decline in annual revenue and employee size
- **2:** Flat or inconsistent growth — some years up, some down, no clear trajectory
- **3:** Modest but consistent growth of 1–5% Y/Y, stable hiring, no major expansion signals
- **4:** Consistent growth of 5–10% Y/Y, forward-thinking, some expansion activity but not aggressive
- **5:** Focused on fast growth. Forward thinking. Proven record of >10% growth Y/Y.
- **Sources:** ENR 500 list, news articles, job posting websites, LinkedIn, firm's /news or /press page, DDG News search

### 3. Type of Industry Served (combined with Services = 25% total)
- **1:** Firm serves within only one of Trelity's target industries
- **2:** Firm works in one or two of Trelity's current sectors but limited overlap
- **3:** Firm works in some of the industry sectors Trelity currently works in
- **4:** Firm works in most of Trelity's current sectors with some future target sectors represented
- **5:** Firm services all of Trelity's current industry sectors and the ones Trelity wants to target in the future
- **Target sectors:** Retail, Restaurant, Multifamily, Industrial, Data Centers, Hospitality
- **Sources:** Client's website, project portfolio pages

### 4. Services Provided (combined with Industry = 25% total)
- **1:** Firm provides only one of the services Trelity provides
- **2:** Firm provides one matching service with limited scope
- **3:** Firm provides two or more professional services that match Trelity's
- **4:** Firm provides three or more matching services, close to but not quite the full ASMEP+Civil suite
- **5:** Firm provides a full range of services (Architecture, Structural, MEP, Electrical, Plumbing, Civil)
- **Sources:** Client's website, services pages

### 5. Total Revenue (15%)
- **1:** Less than $20M or more than $1 billion
- **2:** $20M–$100M or $600M–$1B — outside sweet spot
- **3:** Less than $100M or greater than $600M
- **4:** $150M–$200M or $400M–$450M — approaching or just outside sweet spot
- **5:** Between $200M and $400M (sweet spot)
- **Sources:** ENR 500 list, company announcements, Glassdoor

### 6. # of Employees (10%)
- **1:** Less than 100 employees or more than 1,000 employees
- **2:** 100–200 or 400–600 employees — adjacent to sweet spot
- **3:** Outside sweet spot but not extreme
- **4:** 150–200 or 400–500 employees — approaching or just outside sweet spot
- **5:** Between 200 and 400 employees (sweet spot)
- **Sources:** ENR 500 list, company announcements, Glassdoor, LinkedIn

### 7. Geography (10%)
- **1:** Default score — no East Coast presence confirmed
- **2:** At least one office on East Coast
- **3:** All offices located on East Coast or in Central time zone
- **4:** Majority of offices on East Coast with one or two Central time zone offices
- **5:** All offices located on East Coast only
- **East Coast states (Eastern time zone):** FL, GA, SC, NC, VA, MD, DE, NJ, NY, CT, RI, MA, VT, NH, ME — all count as East Coast
- **Central time zone states** are acceptable and score 3–4 depending on mix
- **Mountain and Pacific time zone offices** reduce the Geography score
- **Offshore/international offices** are ignored entirely — do not count for or against Geography
- **Sources:** Client's website /offices or /locations page — always fetch this page specifically, do not rely on homepage alone
- **Consistency rule:** The Geography score and the AI summary narrative must use the same definition. If Geography scores 4 or 5, the summary must not flag geography as a concern.

---

## Missing Data Protocol

When a data point cannot be found during scraping or AI evaluation:
- Default score for that criterion: **2**
- Flag the criterion in the database: `data_confidence: "low"`
- Surface the flag visually in the dashboard (orange dot next to score badge)
- No dot = high confidence; orange dot = low confidence
- Never skip a firm due to missing data — partial scores are valid

---

## Data Collection Spec

### Sources Per Firm

| Source | Method | Used For |
|---|---|---|
| Firm website homepage | Direct HTTP fetch | Initial content, services overview, culture cues |
| Firm /services page | Direct HTTP fetch | Services provided scoring |
| Firm /offices or /locations page | Direct HTTP fetch | Geography scoring — always fetch this specifically |
| Firm /news or /press page | Direct HTTP fetch | Growth signals, expansion announcements |
| DDG Search | Query + "architecture firm" | ENR/BDC mentions, general firm info |
| DDG News Search | "Firm Name architecture growth OR expansion OR acquisition OR revenue" | Growth orientation signals |
| LinkedIn job postings via DDG | "site:linkedin.com/jobs Firm Name" | Active hiring as growth proxy |
| Glassdoor via DDG | DDG search | Employee sentiment, headcount estimate |

### Scraper Rules
- Always append "architecture firm" or "AE firm" to DDG search queries to avoid name collisions
- Always fetch /offices or /locations page specifically for Geography
- Always fetch /news or /press page for Growth signals
- If DDG rate-limits, add delay and retry — do not default to stub scores
- Offshore/international offices do not count for Geography scoring
- Scraped data is cached per firm — re-scoring uses cached data unless refresh=true is passed

### Score Caching and Targeted Re-scoring
- POST /score {"name": "Firm"} — full score, uses cached scrape if available
- POST /score {"name": "Firm", "criterion": "geography"} — re-score only geography, all other scores stay locked
- POST /score {"name": "Firm", "refresh": true} — force fresh scrape + full re-score

### Scoring Engine Output Format
```json
{
  "cultural_alignment": { "score": 4, "confidence": "high", "rationale": "...", "sources": ["..."] },
  "growth_orientation": { "score": 5, "confidence": "high", "rationale": "...", "sources": ["..."] },
  "industry_services": { "score": 3, "confidence": "low", "rationale": "...", "sources": ["..."] },
  "revenue": { "score": 5, "confidence": "high", "rationale": "...", "sources": ["..."] },
  "employees": { "score": 4, "confidence": "high", "rationale": "...", "sources": ["..."] },
  "geography": { "score": 3, "confidence": "high", "rationale": "...", "sources": ["..."] },
  "composite": 4.15,
  "ai_summary": "Three short paragraphs per the summary format spec."
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
| cultural_rationale | TEXT | AI explanation |
| cultural_sources | TEXT | Sources cited |
| cultural_override | REAL | Manual override value if set |
| cultural_override_note | TEXT | Note explaining override |
| cultural_override_at | TIMESTAMP | When override was set |
| growth_orientation | REAL | 1–5 |
| growth_confidence | TEXT | high / low |
| growth_rationale | TEXT | AI explanation |
| growth_sources | TEXT | Sources cited |
| growth_override | REAL | |
| growth_override_note | TEXT | |
| growth_override_at | TIMESTAMP | |
| industry_services | REAL | 1–5 |
| industry_confidence | TEXT | high / low |
| industry_rationale | TEXT | AI explanation |
| industry_sources | TEXT | Sources cited |
| industry_override | REAL | |
| industry_override_note | TEXT | |
| industry_override_at | TIMESTAMP | |
| revenue | REAL | 1–5 |
| revenue_confidence | TEXT | high / low |
| revenue_rationale | TEXT | AI explanation |
| revenue_sources | TEXT | Sources cited |
| revenue_override | REAL | |
| revenue_override_note | TEXT | |
| revenue_override_at | TIMESTAMP | |
| employees | REAL | 1–5 |
| employees_confidence | TEXT | high / low |
| employees_rationale | TEXT | AI explanation |
| employees_sources | TEXT | Sources cited |
| employees_override | REAL | |
| employees_override_note | TEXT | |
| employees_override_at | TIMESTAMP | |
| geography | REAL | 1–5 |
| geography_confidence | TEXT | high / low |
| geography_rationale | TEXT | AI explanation |
| geography_sources | TEXT | Sources cited |
| geography_override | REAL | |
| geography_override_note | TEXT | |
| geography_override_at | TIMESTAMP | |
| composite | REAL | Weighted composite 0–5 |
| scored_at | TIMESTAMP | |
| score_notes | TEXT | AI summary (3 paragraphs) |
| is_real_score | BOOLEAN | True = AI scored, False = stub |

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
| PATCH | `/firms/{id}/scores/{criterion}` | Manual override for a single criterion |
| GET | `/export` | Return full dataset as CSV download |

---

## Dashboard UX

### Access
- Hosted on Vercel — accessible via URL, no install required
- No login required for POC

### Header
- Logo: TrelityLogo.png from `dashboard/public/`
- Title: "Trelity Prospect Scout" in white
- Subtext: "BY ARMATURA" in light gray (#A0A8B8), smaller, all caps
- Background: Navy #1B3A6B

### Ranked Table Columns
Rank | Composite Score | Firm Name | Source Tag | Growth | Industry | Revenue | Culture | Employees | Geography | BD Stage

### Filters
All / Tier 1 / CenterBuild / ≥4.0 score

### Stat Cards
AI Scored (X/120) | Avg Score | Top Score | Showing

---

## Brand Spec

| Element | Value |
|---|---|
| Primary | Navy blue `#1B3A6B` |
| Accent | Chartreuse/lime `#C5D82E` |
| Background | Off-white `#F5F4EF` |
| Subtext | Light gray `#A0A8B8` |
| Typography | Clean sans-serif |

Score badge colors: 5 = bright green → 1 = light coral/red
Confidence: orange dot (#E8820C) = low confidence; no dot = high confidence

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
| Scoring execution | Synchronous for POC |
| Frontend folder | `dashboard/` (not `frontend/`) |
| Logo | TrelityLogo.png in `dashboard/public/` |
| Tool name | Trelity Prospect Scout (not Hunter) |
| Revenue data | Ignore spreadsheet revenue figures — let Claude estimate from scraped data and training knowledge |
| Offshore offices | Do not penalize Geography score for offshore delivery offices |
| Confidence display | Orange dot in table for low confidence; rationale in drawer explains reasoning |
| AI summary format | Three short paragraphs (overview, strengths, concerns/next step) — not one long block |
| Score consistency | Scores and AI summary must use same definitions — no contradictions between score and narrative |

---

## Future Features Backlog (Post-POC)

1. **Weight adjustment** — Let users tune criterion weights and have all firms re-rank instantly
2. **Shareable drawer links** — Unique URL per firm that can be emailed to team members
3. **Feedback loop / model learning** — Overrides, weight changes, and BD pipeline outcomes feed back into scoring prompt refinement over time
4. **Column filtering** — Filter ranked table by BD Stage, Source, score thresholds per criterion
5. **Column sorting** — Click any column header to re-sort the table by that criterion

---

## BD Pipeline Stages

1. Meet — Not yet heard of Trelity
2. Met — Introduced, interest unclear
3. Get Pilot — Showed interest
4. Develop — First project done, pursuing repeat work
5. Expand — Finding other divisions/PMs/sectors
6. Maintain — Keep them happy

---

## Audit Tool

```bash
cd ~/Projects/hunter/backend
source venv/bin/activate

# Full audit with live re-scrape
python ../scripts/audit_firm.py "Firm Name"

# Stored scores only (instant)
python ../scripts/audit_firm.py "Firm Name" --stored-only

# List all firms ranked
python ../scripts/audit_firm.py --list
```

---

## Growth Re-Score Tool

```bash
cd ~/Projects/hunter/backend
source venv/bin/activate

# Re-score only firms with low-confidence Growth scores
python ../scripts/rescore_growth.py

# Re-score all firms
python ../scripts/rescore_growth.py --all

# Test on N firms first
python ../scripts/rescore_growth.py --limit 5
```

---

## About Nick

Nick Macek is a product manager and AI consultant (Armatura) — not a coder. Claude Code handles all code execution, debugging, and testing. When communicating:
- Lead with what to do and why
- Explain architectural decisions in plain language
- State assumptions and proceed rather than asking clarifying questions
- Keep responses focused
