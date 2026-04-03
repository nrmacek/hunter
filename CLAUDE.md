# CLAUDE.md — Hunter Project

This file provides guidance to Claude Code when working in this repository.
Read this file at the start of every session before doing anything else.

---

## What This Project Is

**Hunter** is an AI-powered prospect evaluation and ranking tool built for Trelity Inc. — a US-based architecture/engineering outsourcing firm.

The tool takes a list of architecture/engineering firm names as input, scrapes and analyzes publicly available data about each firm, scores them on 6 weighted criteria, and outputs a ranked list via a web dashboard.

**Built by:** Nick Macek (AI consultant)
**Client:** Trelity Inc. (John Mickey, CEO)
**Stage:** Proof of Concept

---

## Folder Structure

```
hunter/
├── docs/               → project documentation and reference files
├── data/
│   ├── raw/            → original scraped data, never modified
│   └── processed/      → cleaned, scored data ready for dashboard
├── backend/
│   ├── scrapers/       → code that pulls data from firm websites, LinkedIn, Glassdoor, etc.
│   ├── scoring/        → code that applies the weighted scoring model
│   └── pipeline/       → orchestrates the full scrape → score → output process
├── dashboard/          → Next.js web dashboard (Trelity brand: navy + chartreuse green)
├── tests/              → automated tests
└── scripts/            → utility and one-off scripts
```

---

## Tech Stack

- **Backend/pipeline:** Python 3.12
- **Dashboard:** Next.js (React)
- **Database:** SQLite (POC phase)
- **Scraping:** Python + Antigravity browser agents
- **Hosting (when ready):** Vercel

---

## The Scoring Model

### 6 Criteria and Weights

| # | Criteria | Weight |
|---|---|---|
| 1 | Cultural Alignment | 10% |
| 2 | Growth Orientation | 30% |
| 3 | Type of Industry & Services | 25% |
| 4 | Total Revenue | 15% |
| 5 | # of Employees | 10% |
| 6 | Geography | 10% |

### Composite Score Formula
```
Score = (C1 × 0.10) + (C2 × 0.30) + (C3 × 0.25) + (C4 × 0.15) + (C5 × 0.10) + (C6 × 0.10)
Max score = 5.0
```

### Scoring Rubric (1–5 per criterion)

**1. Cultural Alignment**
- 1: Minimal cultural alignment
- 5: Strong alignment — quality focus, employee care, client success orientation
- Sources: Firm website, LinkedIn posts, Glassdoor, Google Reviews, news

**2. Growth Orientation**
- 1: Revenue/headcount declining
- 5: >10% Y/Y growth, forward-thinking, actively expanding
- Sources: ENR rankings, LinkedIn job postings, news articles

**3. Type of Industry Served**
- 1: Serves only one of Trelity's sectors
- 3: Serves some Trelity sectors
- 5: Serves all current + future target sectors
- Trelity's sectors: Retail, Restaurant, Multifamily, Industrial, Data Centers, Hospitality

**4. Services Provided**
- 1: One matching service
- 3: Two or more matching services
- 5: Full range — Architecture, Structural, MEP, Electrical, Plumbing, Civil (ASMEP+Civil)

**5. Total Revenue / # of Employees**
- 1: <$20M or >$1B revenue; <100 or >1,000 employees
- 3: $20M–$100M or >$600M; outside sweet spot
- 5 (sweet spot): $200M–$400M revenue; 200–400 employees

**6. Geography**
- 1: At least one East Coast office
- 3: All offices on East Coast or Central time zone
- 5: All offices on East Coast only

---

## Ideal Customer Profile (ICP)

- **Type:** American architecture and/or engineering firm
- **Size sweet spot:** 200–400 employees, $200M–$400M annual revenue
- **Services:** Full-service A/E (Architecture + Structural + MEP + Civil)
- **Geography:** East Coast preferred; Central time zone acceptable
- **Growth:** 10%+ Y/Y growth in revenue and/or headcount
- **Culture:** Quality-focused, collaborative, employee-centric
- **Industry sectors:** Retail, Restaurant, Multifamily, Industrial, Data Centers, Hospitality

---

## Data Sources (Public Only)

- Firm websites (services, office locations, culture)
- LinkedIn (employee count, job postings, posts)
- Glassdoor (employee sentiment)
- Google Reviews
- ENR 500 (Top Design Firms list)
- BDC (Building Design+Construction) rankings
- ICSC CenterBuild conference lists
- News articles

---

## Dashboard Brand Spec

| Element | Value |
|---|---|
| Primary | Navy blue (#1B3A6B) |
| Accent | Chartreuse/lime green (#C5D82E) |
| Background | Off-white / light cream (#F5F4EF) |
| Typography | Clean sans-serif |
| Aesthetic | Professional, minimal, architecture-industry appropriate |

---

## How to Work in This Project

- Nick is not a coder — Claude Code handles all coding, testing, debugging, and iteration
- Always explain what you're doing and why in plain English before doing it
- Keep the folder structure clean — files go in the right folders, no dumping things in root
- After any significant change, remind Nick to commit and push to GitHub
- When something is built and working, update this CLAUDE.md with any new commands or context
- Default to practical and buildable — this is a POC, not a production system

---

## Git Workflow

```bash
git add .
git commit -m "describe what was done"
git push
```

Run this after any meaningful chunk of work is complete.

---

## Current Status

Project scaffold created. Environment set up. No application code yet.
Next step: Phase 5 — tech stack scaffold (Python backend + Next.js dashboard boilerplate).
