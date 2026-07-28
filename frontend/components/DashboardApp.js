"use client";

import { useMemo, useState } from "react";

import { defaultFormState, getStatusTone } from "../lib/dashboard";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function DashboardApp() {
  const [formState, setFormState] = useState(defaultFormState);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const statusTone = useMemo(
    () => getStatusTone(dashboard?.status?.level || "info"),
    [dashboard]
  );

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
          document_path: formState.documentPath,
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
            <span>Document Path</span>
            <input value={formState.documentPath} onChange={updateField("documentPath")} />
          </label>
          <label>
            <span>Domain</span>
            <select value={formState.domain} onChange={updateField("domain")}>
              <option value="telecom_security">telecom_security</option>
              <option value="financial_risk">financial_risk</option>
              <option value="medical_qa">medical_qa</option>
              <option value="general">general</option>
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
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? "Generating..." : "Generate Dashboard"}
          </button>
        </form>
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
