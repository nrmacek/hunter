"""
SQLite database setup for Hunter.
Creates firms and scores tables matching the schema in CLAUDE.md.
Database file lives at data/hunter.db (relative to project root).
"""

import sqlite3
import os
from pathlib import Path

# Database path: <project_root>/data/hunter.db
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "hunter.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database. Creates data/ dir if needed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return dicts instead of tuples
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS firms (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            tier            INTEGER,
            source          TEXT,
            city            TEXT,
            state           TEXT,
            employees       INTEGER,
            revenue_m       REAL,
            bd_stage        TEXT    DEFAULT 'Meet',
            notes           TEXT,
            last_contacted  DATE,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_id                 INTEGER NOT NULL,
            cultural_alignment      REAL,
            cultural_confidence     TEXT    DEFAULT 'low',
            growth_orientation      REAL,
            growth_confidence       TEXT    DEFAULT 'low',
            industry_services       REAL,
            industry_confidence     TEXT    DEFAULT 'low',
            revenue                 REAL,
            revenue_confidence      TEXT    DEFAULT 'low',
            employees               REAL,
            employees_confidence    TEXT    DEFAULT 'low',
            geography               REAL,
            geography_confidence    TEXT    DEFAULT 'low',
            composite               REAL,
            scored_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score_notes             TEXT,
            is_real_score           INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (firm_id) REFERENCES firms(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraped_cache (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            firm_id     INTEGER NOT NULL UNIQUE,
            scraped_json TEXT NOT NULL,
            scraped_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (firm_id) REFERENCES firms(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Migrate: add recommendation column to scores
    try:
        cursor.execute("ALTER TABLE scores ADD COLUMN recommendation TEXT")
    except Exception:
        pass

    # Migrate: add website column to firms
    try:
        cursor.execute("ALTER TABLE firms ADD COLUMN website TEXT")
    except Exception:
        pass

    # Migrate: add per-criterion detail columns (safe — no-ops if already present)
    prefixes = ["cultural", "growth", "industry", "revenue", "employees", "geography"]
    suffixes = ["_rationale TEXT", "_sources TEXT",
                "_override REAL", "_override_note TEXT", "_override_at TIMESTAMP"]
    for prefix in prefixes:
        for suffix in suffixes:
            try:
                cursor.execute(f"ALTER TABLE scores ADD COLUMN {prefix}{suffix}")
            except Exception:
                pass  # Column already exists

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
