"use client";

import { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000";

const BD_STAGES = ["Meet", "Met", "Get Pilot", "Develop", "Expand", "Maintain"];

const CRITERIA = [
  { key: "growth_orientation", prefix: "growth", label: "Growth Orientation", weight: "30%" },
  { key: "industry_services", prefix: "industry", label: "Industry & Services", weight: "25%" },
  { key: "revenue", prefix: "revenue", label: "Total Revenue", weight: "15%" },
  { key: "cultural_alignment", prefix: "cultural", label: "Cultural Alignment", weight: "10%" },
  { key: "employees", prefix: "employees", label: "Employees", weight: "10%" },
  { key: "geography", prefix: "geography", label: "Geography", weight: "10%" },
];

// ── Helpers ────────────────────────────────────────────────────────────────

function getScoreTier(score) {
  if (score >= 4.5) return 5;
  if (score >= 3.5) return 4;
  if (score >= 2.5) return 3;
  if (score >= 1.5) return 2;
  return 1;
}

function getRankClass(composite) {
  return `rank-score-${getScoreTier(composite)}`;
}

function getBdStageClass(stage) {
  if (!stage) return "bd-stage--meet";
  const slug = stage.toLowerCase().replace(/\s+/g, "-");
  return `bd-stage--${slug}`;
}

function parseNotes(raw) {
  if (!raw) return [];
  try {
    const arr = JSON.parse(raw);
    if (Array.isArray(arr)) return arr;
  } catch {}
  return [{ ts: "", text: raw }];
}

function formatNoteTs(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  }) + " " + d.toLocaleTimeString("en-US", {
    hour: "numeric", minute: "2-digit",
  });
}

// ── Score Badge ────────────────────────────────────────────────────────────

function ScoreBadge({ value, confidence, isComposite = false, small = false }) {
  const tier = getScoreTier(value);
  const classes = [
    "score-badge",
    `score-${tier}`,
    isComposite ? "composite-badge" : "",
    small ? "score-badge--small" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className="score-cell">
      <span className={classes}>{value.toFixed(1)}</span>
      {confidence === "low" && (
        <span className="low-confidence" title="Low confidence — data may be incomplete" />
      )}
    </span>
  );
}

// ── Override Inline Editor ─────────────────────────────────────────────────

function OverrideEditor({ criterion, firmId, currentOverride, onSave, onCancel }) {
  const [score, setScore] = useState(currentOverride || 3);
  const [note, setNote] = useState("");

  async function handleSave() {
    const res = await fetch(`${API_BASE}/firms/${firmId}/scores/${criterion}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ score: parseFloat(score), note: note.trim() || null }),
    });
    if (res.ok) {
      const updated = await res.json();
      onSave(updated);
    }
  }

  return (
    <div className="override-editor">
      <div className="override-row">
        <label className="override-label">Score:</label>
        <select className="override-select" value={score} onChange={(e) => setScore(e.target.value)}>
          {[1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5].map((v) => (
            <option key={v} value={v}>{v.toFixed(1)}</option>
          ))}
        </select>
      </div>
      <input
        className="override-note-input"
        placeholder="Reason for override (optional)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <div className="override-actions">
        <button className="btn btn-primary btn-sm" onClick={handleSave}>Save</button>
        <button className="btn btn-ghost-dark btn-sm" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

// ── Criterion Row (expandable + override) ──────────────────────────────────

function CriterionRow({ c, s, firmId, onUpdate }) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);

  const conf = s[`${c.prefix}_confidence`];
  const rationale = s[`${c.prefix}_rationale`];
  const sources = s[`${c.prefix}_sources`];
  const override = s[`${c.prefix}_override`];
  const overrideNote = s[`${c.prefix}_override_note`];
  const overrideAt = s[`${c.prefix}_override_at`];
  const aiScore = s[c.key];
  const effectiveScore = override != null ? override : aiScore;

  return (
    <div className={`drawer-criterion${expanded ? " drawer-criterion--expanded" : ""}`}>
      <div className="drawer-criterion-header" onClick={() => setExpanded(!expanded)}>
        <ScoreBadge value={effectiveScore} confidence={conf} />
        {override != null && (
          <span className="override-badge" title={`AI score: ${aiScore.toFixed(1)}`}>
            AI: {aiScore.toFixed(1)}
          </span>
        )}
        <span className="drawer-criterion-name">{c.label}</span>
        <span className="drawer-criterion-weight">{c.weight}</span>
        <button
          className="override-pencil"
          title="Override score"
          onClick={(e) => { e.stopPropagation(); setEditing(!editing); setExpanded(true); }}
        >
          &#9998;
        </button>
        <span className={`expand-chevron${expanded ? " expand-chevron--open" : ""}`}>&#9662;</span>
      </div>

      {expanded && (
        <div className="drawer-criterion-detail">
          <p className="drawer-criterion-rationale">
            {rationale || "No rationale available \u2014 rescore this firm to generate."}
          </p>
          <p className="drawer-criterion-sources">
            <strong>Sources:</strong> {sources || "None cited"}
          </p>
          <p className="drawer-criterion-conf">
            <strong>Confidence:</strong>{" "}
            <span className={conf === "low" ? "conf-low" : "conf-high"}>
              {conf === "low" ? "Low" : "High"}
            </span>
          </p>
          {override != null && overrideNote && (
            <p className="drawer-criterion-override-info">
              <strong>Override note:</strong> {overrideNote}
              {overrideAt && <> ({formatNoteTs(overrideAt)})</>}
            </p>
          )}
          {editing && (
            <OverrideEditor
              criterion={c.key}
              firmId={firmId}
              currentOverride={override || aiScore}
              onSave={(updated) => { onUpdate(updated); setEditing(false); }}
              onCancel={() => setEditing(false)}
            />
          )}
        </div>
      )}
    </div>
  );
}

// ── Firm Detail Drawer ────────────────────────────────────────────────────

function FirmDrawer({ firm, rank, totalFirms, onClose, onUpdate }) {
  const [bdStage, setBdStage] = useState(firm.bd_stage || "Meet");
  const [lastContacted, setLastContacted] = useState(firm.last_contacted || "");
  const [noteText, setNoteText] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setBdStage(firm.bd_stage || "Meet");
    setLastContacted(firm.last_contacted || "");
    setNoteText("");
  }, [firm.id]);

  async function patchFirm(body) {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/firms/${firm.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`PATCH failed: ${res.status}`);
      const updated = await res.json();
      onUpdate(updated);
    } finally {
      setSaving(false);
    }
  }

  function handleStageChange(e) {
    const newStage = e.target.value;
    setBdStage(newStage);
    patchFirm({ bd_stage: newStage });
  }

  function handleDateChange(e) {
    const newDate = e.target.value;
    setLastContacted(newDate);
    patchFirm({ last_contacted: newDate });
  }

  function handleAddNote() {
    if (!noteText.trim()) return;
    patchFirm({ note_text: noteText.trim() });
    setNoteText("");
  }

  const s = firm.score;
  const notes = parseNotes(firm.notes);

  // Split AI summary into paragraphs
  const summaryParagraphs = s?.score_notes
    ? s.score_notes.split(/\n\n+/).filter(Boolean)
    : [];

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-header">
          <div>
            <h2 className="drawer-firm-name">{firm.name}</h2>
            <div className="drawer-meta">
              {[firm.city, firm.state].filter(Boolean).join(", ")}
              {firm.employees && <> &middot; {firm.employees.toLocaleString()} employees</>}
              {firm.revenue_m && <> &middot; ${firm.revenue_m}M revenue</>}
            </div>
          </div>
          <button className="drawer-close" onClick={onClose} title="Close">&times;</button>
        </div>

        <div className="drawer-body">
          {/* Rank + composite */}
          {s && (
            <div className="drawer-rank-row">
              <ScoreBadge value={s.composite} confidence="high" isComposite />
              <span className="drawer-rank-text">
                Rank #{rank} of {totalFirms} prospects
              </span>
            </div>
          )}

          {/* BD Stage */}
          <div className="drawer-field">
            <label className="drawer-label">BD Stage</label>
            <select
              className="drawer-select"
              value={bdStage}
              onChange={handleStageChange}
              disabled={saving}
            >
              {BD_STAGES.map((st) => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>

          {/* Last Contacted */}
          <div className="drawer-field">
            <label className="drawer-label">Last Contacted</label>
            <input
              type="date"
              className="drawer-input"
              value={lastContacted}
              onChange={handleDateChange}
              disabled={saving}
            />
          </div>

          {/* AI Summary — rendered as multiple paragraphs */}
          {summaryParagraphs.length > 0 && (
            <div className="drawer-section">
              <h3 className="drawer-section-title">AI Summary</h3>
              {summaryParagraphs.map((p, i) => (
                <p key={i} className="drawer-summary">{p}</p>
              ))}
            </div>
          )}

          {/* Score Breakdown — expandable rows with override */}
          {s && (
            <div className="drawer-section">
              <h3 className="drawer-section-title">Score Breakdown</h3>
              <div className="drawer-criteria">
                {CRITERIA.map((c) => (
                  <CriterionRow
                    key={c.key}
                    c={c}
                    s={s}
                    firmId={firm.id}
                    onUpdate={onUpdate}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          <div className="drawer-section">
            <h3 className="drawer-section-title">Notes</h3>
            <div className="drawer-note-input">
              <textarea
                className="drawer-textarea"
                placeholder="Add a note..."
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                rows={2}
              />
              <button
                className="btn btn-primary btn-sm"
                onClick={handleAddNote}
                disabled={saving || !noteText.trim()}
              >
                Add Note
              </button>
            </div>
            {notes.length > 0 && (
              <div className="drawer-notes-list">
                {notes.map((n, i) => (
                  <div key={i} className="drawer-note">
                    {n.ts && <span className="drawer-note-ts">{formatNoteTs(n.ts)}</span>}
                    <span className="drawer-note-text">{n.text}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

// ── Add Firm Modal ────────────────────────────────────────────────────────

function AddFirmModal({ onClose, onAdded }) {
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [source, setSource] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim() || !website.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/firms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          website: website.trim(),
          source: source.trim() || null,
        }),
      });
      if (res.ok) {
        onAdded();
        onClose();
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="modal">
        <h3 className="modal-title">Add Firm</h3>
        <form onSubmit={handleSubmit}>
          <div className="modal-field">
            <label className="drawer-label">Firm Name</label>
            <input
              className="drawer-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Gresham Smith"
              autoFocus
            />
          </div>
          <div className="modal-field">
            <label className="drawer-label">Website</label>
            <input
              className="drawer-input"
              type="url"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              placeholder="e.g. https://www.greshamsmith.com"
            />
          </div>
          <div className="modal-field">
            <label className="drawer-label">Source Tag</label>
            <input
              className="drawer-input"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="e.g. ENR, CenterBuild"
            />
          </div>
          <div className="modal-actions">
            <button type="submit" className="btn btn-primary" disabled={submitting || !name.trim() || !website.trim()}>
              {submitting ? "Adding..." : "Add Firm"}
            </button>
            <button type="button" className="btn btn-ghost-dark" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </>
  );
}

// ── Bulk Upload Modal ─────────────────────────────────────────────────────

function BulkUploadModal({ onClose, onUploaded }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const fileRef = useRef();

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/firms/bulk`, { method: "POST", body: form });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        onUploaded();
      }
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className="modal">
        <h3 className="modal-title">Bulk Upload</h3>
        <p className="modal-desc">Upload a CSV or Excel file with columns: <strong>name</strong> (required), <strong>source</strong> (optional).</p>
        <div className="modal-field">
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx"
            className="drawer-input"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </div>
        {result && (
          <div className="upload-result">
            Added {result.added} firms. {result.skipped > 0 && `Skipped ${result.skipped} duplicates.`}
          </div>
        )}
        <div className="modal-actions">
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading || !file}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
          <button className="btn btn-ghost-dark" onClick={onClose}>{result ? "Done" : "Cancel"}</button>
        </div>
      </div>
    </>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function HomePage() {
  const [firms, setFirms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [selectedFirmId, setSelectedFirmId] = useState(null);
  const [showAddFirm, setShowAddFirm] = useState(false);
  const [showBulkUpload, setShowBulkUpload] = useState(false);

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

  function handleFirmUpdate(updated) {
    setFirms((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
  }

  function handleExport() {
    window.open(`${API_BASE}/export`, "_blank");
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
      ? (firms.reduce((sum, f) => sum + (f.score?.composite || 0), 0) / totalFirms).toFixed(2)
      : "\u2014";
  const topScore =
    totalFirms > 0
      ? Math.max(...firms.map((f) => f.score?.composite || 0)).toFixed(2)
      : "\u2014";

  const selectedFirm = selectedFirmId ? firms.find((f) => f.id === selectedFirmId) : null;
  const selectedRank = selectedFirm ? firms.indexOf(selectedFirm) + 1 : 0;

  // ── Render ──

  return (
    <>
      {/* Header */}
      <header className="app-header" id="app-header">
        <div className="app-logo">
          <img src="/TrelityLogo.png" alt="Trelity" className="app-logo-img" />
          <span className="app-logo-scout">Prospect Scout</span>
        </div>
        <div className="topbar-stats">
          <div className="topbar-stat">
            <span className="topbar-stat-value">
              {realScored}<span className="topbar-stat-value--sub">/{totalFirms}</span>
            </span>
            <span className="topbar-stat-label">AI Scored</span>
          </div>
          <span className="topbar-stat-divider" />
          <div className="topbar-stat">
            <span className="topbar-stat-value">{avgComposite}</span>
            <span className="topbar-stat-label">Avg Score</span>
          </div>
          <span className="topbar-stat-divider" />
          <div className="topbar-stat">
            <span className="topbar-stat-value">{topScore}</span>
            <span className="topbar-stat-label">Top Score</span>
          </div>
          <span className="topbar-stat-divider" />
          <div className="topbar-stat">
            <span className="topbar-stat-value">{filtered.length}</span>
            <span className="topbar-stat-label">Showing</span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn btn-ghost" onClick={() => setShowBulkUpload(true)}>Upload</button>
          <button className="btn btn-ghost" onClick={() => setShowAddFirm(true)}>+ Add Firm</button>
          <button className="btn btn-accent" onClick={handleExport}>Export CSV</button>
          <button className="btn btn-ghost" onClick={fetchFirms} id="btn-refresh">&#8635; Refresh</button>
        </div>
      </header>

      {/* Main */}
      <main className="main-content">

        {/* Table Card */}
        <div className="table-card" id="firms-table-card">
          <div className="table-toolbar">
            <span className="table-title">Ranked Prospects</span>
            <div className="table-filters">
              {[
                { key: "all", label: "All" },
                { key: "tier1", label: "Tier 1" },
                { key: "centerbuild", label: "CenterBuild" },
                { key: "top", label: "\u2265 4.0" },
              ].map((f) => (
                <button
                  key={f.key}
                  id={`filter-${f.key}`}
                  className={`filter-btn ${filter === f.key ? "filter-btn--active" : ""}`}
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
              <span>Loading firms&hellip;</span>
            </div>
          ) : error ? (
            <div className="error-state">
              <p>&#9888; Failed to load: {error}</p>
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
                  <th className="col-center" style={{ width: 56 }}>Rank</th>
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
                  <tr
                    key={firm.id}
                    id={`firm-row-${firm.id}`}
                    className={`firm-row${selectedFirmId === firm.id ? " firm-row--selected" : ""}`}
                    onClick={() => setSelectedFirmId(firm.id)}
                  >
                    <td className="col-center">
                      <span className={`rank-badge ${getRankClass(firm.score?.composite || 0)}`}>{idx + 1}</span>
                    </td>
                    <td className="col-center">
                      {firm.score && <ScoreBadge value={firm.score.composite} confidence="high" isComposite />}
                    </td>
                    <td>
                      <div className="firm-name">{firm.name}</div>
                      {(firm.city || firm.state) && (
                        <div className="firm-location">
                          {[firm.city, firm.state].filter(Boolean).join(", ")}
                        </div>
                      )}
                    </td>
                    <td>{firm.source && <span className="source-tag">{firm.source}</span>}</td>
                    <td className="col-center">
                      {firm.score && <ScoreBadge value={firm.score.growth_orientation} confidence={firm.score.growth_confidence} />}
                    </td>
                    <td className="col-center">
                      {firm.score && <ScoreBadge value={firm.score.industry_services} confidence={firm.score.industry_confidence} />}
                    </td>
                    <td className="col-center">
                      {firm.score && <ScoreBadge value={firm.score.revenue} confidence={firm.score.revenue_confidence} />}
                    </td>
                    <td className="col-center">
                      {firm.score && <ScoreBadge value={firm.score.cultural_alignment} confidence={firm.score.cultural_confidence} />}
                    </td>
                    <td className="col-center">
                      {firm.score && <ScoreBadge value={firm.score.employees} confidence={firm.score.employees_confidence} />}
                    </td>
                    <td className="col-center">
                      {firm.score && <ScoreBadge value={firm.score.geography} confidence={firm.score.geography_confidence} />}
                    </td>
                    <td>
                      {firm.bd_stage && (
                        <span className={`bd-stage ${getBdStageClass(firm.bd_stage)}`}>{firm.bd_stage}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Firm Detail Drawer */}
      {selectedFirm && (
        <FirmDrawer
          firm={selectedFirm}
          rank={selectedRank}
          totalFirms={totalFirms}
          onClose={() => setSelectedFirmId(null)}
          onUpdate={handleFirmUpdate}
        />
      )}

      {/* Add Firm Modal */}
      {showAddFirm && (
        <AddFirmModal onClose={() => setShowAddFirm(false)} onAdded={fetchFirms} />
      )}

      {/* Bulk Upload Modal */}
      {showBulkUpload && (
        <BulkUploadModal onClose={() => setShowBulkUpload(false)} onUploaded={fetchFirms} />
      )}
    </>
  );
}
