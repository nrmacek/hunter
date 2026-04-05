"use client";

import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

// ── Helpers ────────────────────────────────────────────────────────────────

function getScoreTier(score) {
  if (score >= 4.5) return 5;
  if (score >= 3.5) return 4;
  if (score >= 2.5) return 3;
  if (score >= 1.5) return 2;
  return 1;
}

function getRankClass(rank) {
  if (rank === 1) return "rank-1";
  if (rank === 2) return "rank-2";
  if (rank === 3) return "rank-3";
  return "rank-default";
}

function getBdStageClass(stage) {
  if (!stage) return "bd-stage--meet";
  const slug = stage.toLowerCase().replace(/\s+/g, "-");
  return `bd-stage--${slug}`;
}

// ── Score Badge Component ──────────────────────────────────────────────────

function ScoreBadge({ value, confidence, isComposite = false }) {
  const tier = getScoreTier(value);
  const classes = [
    "score-badge",
    `score-${tier}`,
    isComposite ? "composite-badge" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className="score-cell">
      <span className={classes}>{value.toFixed(1)}</span>
      {confidence === "low" && (
        <span
          className="low-confidence"
          title="Low confidence — data may be incomplete"
        />
      )}
    </span>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function HomePage() {
  const [firms, setFirms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchFirms();
  }, []);

  async function fetchFirms() {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/firms`);
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const data = await res.json();
      setFirms(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // ── Filtering ──

  const filtered = firms.filter((f) => {
    if (filter === "all") return true;
    if (filter === "tier1") return f.tier === 1;
    if (filter === "centerbuild") return f.source === "CenterBuild";
    if (filter === "top") return f.score?.composite >= 4.0;
    return true;
  });

  // ── Stats ──

  const totalFirms = firms.length;
  const realScored = firms.filter((f) => f.score?.is_real_score === 1).length;
  const avgComposite =
    totalFirms > 0
      ? (
          firms.reduce((sum, f) => sum + (f.score?.composite || 0), 0) /
          totalFirms
        ).toFixed(2)
      : "—";
  const topScore =
    totalFirms > 0
      ? Math.max(...firms.map((f) => f.score?.composite || 0)).toFixed(2)
      : "—";

  // ── Render ──

  return (
    <>
      {/* Header */}
      <header className="app-header" id="app-header">
        <div className="app-logo">
          <img
            src="/TrelityLogo.png"
            alt="Trelity"
            className="app-logo-img"
          />
          <span className="app-logo-text">Trelity Prospect Scout</span>

        </div>
        <div className="header-actions">
          <button className="btn btn-ghost" onClick={fetchFirms} id="btn-refresh">
            ↻ Refresh
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="main-content">
        {/* Stats Bar */}
        <div className="stats-bar" id="stats-bar">
          <div className="stat-card">
            <div className="stat-label">AI Scored</div>
            <div className="stat-value">
              {realScored}
              <span style={{ fontSize: "0.7em", color: "var(--color-text-muted)", fontWeight: 400 }}>
                /{totalFirms}
              </span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Avg. Score</div>
            <div className="stat-value stat-value--accent">{avgComposite}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Top Score</div>
            <div className="stat-value">{topScore}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Showing</div>
            <div className="stat-value">{filtered.length}</div>
          </div>
        </div>

        {/* Table Card */}
        <div className="table-card" id="firms-table-card">
          <div className="table-toolbar">
            <span className="table-title">Ranked Prospects</span>
            <div className="table-filters">
              {[
                { key: "all", label: "All" },
                { key: "tier1", label: "Tier 1" },
                { key: "centerbuild", label: "CenterBuild" },
                { key: "top", label: "≥ 4.0" },
              ].map((f) => (
                <button
                  key={f.key}
                  id={`filter-${f.key}`}
                  className={`filter-btn ${
                    filter === f.key ? "filter-btn--active" : ""
                  }`}
                  onClick={() => setFilter(f.key)}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner" />
              <span>Loading firms…</span>
            </div>
          ) : error ? (
            <div className="error-state">
              <p>⚠ Failed to load: {error}</p>
              <p style={{ fontSize: "0.8rem", marginTop: 8 }}>
                Make sure the backend is running on port 8000
              </p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="empty-state">
              <p>No firms match this filter.</p>
            </div>
          ) : (
            <table className="data-table" id="firms-table">
              <thead>
                <tr>
                  <th className="col-center" style={{ width: 56 }}>
                    Rank
                  </th>
                  <th className="col-center">Score</th>
                  <th>Firm</th>
                  <th>Source</th>
                  <th className="col-center">Growth</th>
                  <th className="col-center">Industry</th>
                  <th className="col-center">Revenue</th>
                  <th className="col-center">Culture</th>
                  <th className="col-center">Employees</th>
                  <th className="col-center">Geography</th>
                  <th>BD Stage</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((firm, idx) => (
                  <tr key={firm.id} id={`firm-row-${firm.id}`}>
                    <td className="col-center">
                      <span className={`rank-badge ${getRankClass(idx + 1)}`}>
                        {idx + 1}
                      </span>
                    </td>
                    <td className="col-center">
                      {firm.score && (
                        <ScoreBadge
                          value={firm.score.composite}
                          confidence="high"
                          isComposite
                        />
                      )}
                    </td>
                    <td>
                      <div className="firm-name">{firm.name}</div>
                      {(firm.city || firm.state) && (
                        <div className="firm-location">
                          {[firm.city, firm.state].filter(Boolean).join(", ")}
                        </div>
                      )}
                    </td>
                    <td>
                      {firm.source && (
                        <span className="source-tag">{firm.source}</span>
                      )}
                    </td>
                    <td className="col-center">
                      {firm.score && (
                        <ScoreBadge
                          value={firm.score.growth_orientation}
                          confidence={firm.score.growth_confidence}
                        />
                      )}
                    </td>
                    <td className="col-center">
                      {firm.score && (
                        <ScoreBadge
                          value={firm.score.industry_services}
                          confidence={firm.score.industry_confidence}
                        />
                      )}
                    </td>
                    <td className="col-center">
                      {firm.score && (
                        <ScoreBadge
                          value={firm.score.revenue}
                          confidence={firm.score.revenue_confidence}
                        />
                      )}
                    </td>
                    <td className="col-center">
                      {firm.score && (
                        <ScoreBadge
                          value={firm.score.cultural_alignment}
                          confidence={firm.score.cultural_confidence}
                        />
                      )}
                    </td>
                    <td className="col-center">
                      {firm.score && (
                        <ScoreBadge
                          value={firm.score.employees}
                          confidence={firm.score.employees_confidence}
                        />
                      )}
                    </td>
                    <td className="col-center">
                      {firm.score && (
                        <ScoreBadge
                          value={firm.score.geography}
                          confidence={firm.score.geography_confidence}
                        />
                      )}
                    </td>
                    <td>
                      {firm.bd_stage && (
                        <span
                          className={`bd-stage ${getBdStageClass(
                            firm.bd_stage
                          )}`}
                        >
                          {firm.bd_stage}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </>
  );
}
