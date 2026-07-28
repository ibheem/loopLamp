"use client";

import { useEffect, useMemo, useState } from "react";

import {
  defaultFormState,
  domainOptions,
  findSourceById,
  formatSourceLabel,
  getPreferredSourceId,
  getStatusTone,
  groupSourcesByDomain,
} from "../lib/dashboard";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function DashboardApp() {
  const [formState, setFormState] = useState(defaultFormState);
  const [sources, setSources] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const statusTone = useMemo(
    () => getStatusTone(dashboard?.status?.level || "info"),
    [dashboard]
  );
  const groupedSources = useMemo(() => groupSourcesByDomain(sources), [sources]);
  const selectedSource = useMemo(
    () => findSourceById(sources, formState.sourceId),
    [sources, formState.sourceId]
  );

  async function loadSources({ showRefreshing = false } = {}) {
    if (showRefreshing) {
      setRefreshing(true);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/sources`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to load sources.");
      }
      setSources(payload.sources);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      if (showRefreshing) {
        setRefreshing(false);
      }
    }
  }

  useEffect(() => {
    let active = true;

    async function loadInitialSources() {
      try {
        const response = await fetch(`${API_BASE_URL}/sources`);
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.detail || "Unable to load sources.");
        }
        if (active) {
          setSources(payload.sources);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError.message);
        }
      }
    }

    loadInitialSources();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!sources.length) {
      return;
    }

    const preferredSourceId = getPreferredSourceId(sources, formState.domain, formState.sourceId);
    if (preferredSourceId && preferredSourceId !== formState.sourceId) {
      setFormState((current) => ({ ...current, sourceId: preferredSourceId }));
    }
  }, [sources, formState.domain, formState.sourceId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: formState.query,
          source_id: formState.sourceId,
          domain: formState.domain,
          max_results: Number(formState.maxResults),
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Dashboard request failed.");
      }

      setDashboard(payload);
    } catch (submitError) {
      setDashboard(null);
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  }

  function updateField(field) {
    return function onChange(event) {
      setFormState((current) => ({ ...current, [field]: event.target.value }));
    };
  }

  function handleSourceChange(event) {
    const sourceId = event.target.value;
    const nextSource = findSourceById(sources, sourceId);

    setFormState((current) => ({
      ...current,
      sourceId,
      domain:
        nextSource && nextSource.domain !== "general"
          ? nextSource.domain
          : current.domain,
    }));
  }

  async function handleRefresh() {
    setError("");
    await loadSources({ showRefreshing: true });
  }

  async function handleUpload(event) {
    const [file] = event.target.files || [];
    if (!file) {
      return;
    }

    setUploading(true);
    setError("");
    try {
      const bytes = await file.arrayBuffer();
      const contentBase64 = window.btoa(
        Array.from(new Uint8Array(bytes))
          .map((byte) => String.fromCharCode(byte))
          .join("")
      );
      const response = await fetch(`${API_BASE_URL}/sources/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          domain: formState.domain,
          content_base64: contentBase64,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Upload failed.");
      }
      setSources((current) => [...current, payload.source]);
      setFormState((current) => ({
        ...current,
        domain: payload.source.domain !== "general" ? payload.source.domain : current.domain,
        sourceId: payload.source.source_id,
      }));
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleDeleteSource() {
    if (!selectedSource || selectedSource.origin !== "upload") {
      return;
    }
    if (!window.confirm(`Delete uploaded source "${selectedSource.label}"?`)) {
      return;
    }

    setDeleting(true);
    setError("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/sources/${encodeURIComponent(selectedSource.source_id)}`,
        { method: "DELETE" }
      );
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Delete failed.");
      }

      setSources((current) =>
        current.filter((source) => source.source_id !== selectedSource.source_id)
      );
      setDashboard(null);
    } catch (deleteError) {
      setError(deleteError.message);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">loopLamp</p>
          <h1>Domain Dashboard</h1>
          <p className="lede">
            Query a local document, generate a structured report, and preview the
            dashboard-ready payload from the backend.
          </p>
        </div>
        <div className="hero-card">
          <p className="hero-label">API Endpoint</p>
          <code>{API_BASE_URL}/dashboard/report</code>
        </div>
      </section>

      <section className="panel">
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            <span>Question</span>
            <textarea
              rows="4"
              value={formState.query}
              onChange={updateField("query")}
            />
          </label>
          <label>
            <span>Saved Source</span>
            <select value={formState.sourceId} onChange={handleSourceChange}>
              {groupedSources.length ? (
                groupedSources.map((group) => (
                  <optgroup key={group.domain} label={group.label}>
                    {group.sources.map((source) => (
                      <option key={source.source_id} value={source.source_id}>
                        {formatSourceLabel(source)}
                      </option>
                    ))}
                  </optgroup>
                ))
              ) : (
                <option value="">No saved sources yet</option>
              )}
            </select>
          </label>
          <label>
            <span>Domain</span>
            <select value={formState.domain} onChange={updateField("domain")}>
              {domainOptions.map((domain) => (
                <option key={domain} value={domain}>
                  {domain}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Max Results</span>
            <input
              type="number"
              min="1"
              max="10"
              value={formState.maxResults}
              onChange={updateField("maxResults")}
            />
          </label>
          <label>
            <span>Upload New Source</span>
            <input type="file" accept=".txt,.md,.pdf,.csv,.json" onChange={handleUpload} />
          </label>
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? "Generating..." : "Generate Dashboard"}
          </button>
          <button
            className="secondary-button"
            disabled={refreshing || loading || uploading}
            type="button"
            onClick={handleRefresh}
          >
            {refreshing ? "Refreshing..." : "Refresh Sources"}
          </button>
          <button
            className="secondary-button"
            disabled={!selectedSource || selectedSource.origin !== "upload" || deleting}
            type="button"
            onClick={handleDeleteSource}
          >
            {deleting ? "Deleting..." : "Delete Uploaded Source"}
          </button>
        </form>
        {selectedSource ? (
          <p className="hero-label">
            Selected source: {selectedSource.label} · {selectedSource.domain} · {selectedSource.origin}
          </p>
        ) : null}
        {uploading ? <p className="hero-label">Uploading source...</p> : null}
        {error ? <p className="error-banner">{error}</p> : null}
      </section>

      {dashboard ? (
        <section className="results">
          <header className="results-header">
            <div>
              <p className="eyebrow">Report</p>
              <h2>{dashboard.title}</h2>
              <p className="lede">{dashboard.summary}</p>
            </div>
            <span className={`status-pill ${statusTone}`}>
              {dashboard.status.level}
            </span>
          </header>

          <div className="card-grid">
            <article className="panel">
              <h3>Metrics</h3>
              <div className="metric-grid">
                {dashboard.metrics.map((metric) => (
                  <div className="metric-card" key={metric.label}>
                    <span>{metric.label}</span>
                    <strong>
                      {metric.value}
                      {metric.unit ? ` ${metric.unit}` : ""}
                    </strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <h3>Highlights</h3>
              <div className="stack">
                {dashboard.highlights.map((highlight) => (
                  <div className="note-card" key={`${highlight.title}-${highlight.severity}`}>
                    <div className="note-header">
                      <strong>{highlight.title}</strong>
                      <span className={`severity severity-${highlight.severity}`}>
                        {highlight.severity}
                      </span>
                    </div>
                    <p>{highlight.detail}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <h3>Actions</h3>
              <ol className="action-list">
                {dashboard.actions.map((action) => (
                  <li key={`${action.priority}-${action.action}`}>
                    <span className="priority">{action.priority}</span>
                    <span>{action.action}</span>
                  </li>
                ))}
              </ol>
            </article>

            <article className="panel">
              <h3>Execution</h3>
              <dl className="meta-list">
                <div>
                  <dt>Provider</dt>
                  <dd>{dashboard.execution.provider_mode}</dd>
                </div>
                <div>
                  <dt>Model</dt>
                  <dd>{dashboard.execution.provider_model || "fallback"}</dd>
                </div>
                <div>
                  <dt>Workflow</dt>
                  <dd>{dashboard.execution.workflow_backend}</dd>
                </div>
                <div>
                  <dt>Sources</dt>
                  <dd>{dashboard.source_count}</dd>
                </div>
              </dl>
            </article>
          </div>

          <section className="panel">
            <h3>Warnings</h3>
            <ul className="warning-list">
              {dashboard.status.issues.length ? (
                dashboard.status.issues.map((issue) => <li key={issue}>{issue}</li>)
              ) : (
                <li>No evaluation issues detected.</li>
              )}
            </ul>
          </section>
        </section>
      ) : null}
    </main>
  );
}
