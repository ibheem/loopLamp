"use client";

import { getDomainGraphSections, getGraphSectionStatus } from "../lib/dashboard";

import { useEffect, useMemo, useState } from "react";

import {
  defaultProviderCatalog,
  defaultFormState,
  domainOptions,
  findSourceById,
  formatProviderAvailability,
  formatProviderReachability,
  formatQueryErrorMessage,
  formatSourceIndexStatus,
  formatUploadErrorMessage,
  formatSourceLabel,
  getLlmFallbackWarning,
  getProviderAvailabilityTone,
  getProviderReachabilityTone,
  getProviderById,
  getPreferredSourceId,
  getSourceIndexTone,
  getStatusTone,
  groupSourcesByDomain,
  isLlmGenerated,
  retrievalModeOptions,
} from "../lib/dashboard";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function DashboardApp() {
  const [formState, setFormState] = useState(defaultFormState);
  const [sources, setSources] = useState([]);
  const [providerCatalog, setProviderCatalog] = useState(defaultProviderCatalog);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [reindexing, setReindexing] = useState(false);
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
  const selectedProvider = useMemo(
    () =>
      getProviderById(providerCatalog, formState.llmProvider) ||
      getProviderById(providerCatalog, providerCatalog.default_provider_id) ||
      defaultProviderCatalog.providers[0],
    [providerCatalog, formState.llmProvider]
  );
  const configuredProviderCount = useMemo(
    () =>
      providerCatalog.providers.filter(
        (provider) => provider.provider_id !== "auto" && provider.available
      ).length,
    [providerCatalog]
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

    async function loadInitialState() {
      try {
        const [sourcesResponse, providersResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/sources`),
          fetch(`${API_BASE_URL}/llm/providers`),
        ]);
        const [sourcesPayload, providersPayload] = await Promise.all([
          sourcesResponse.json(),
          providersResponse.json(),
        ]);
        if (!sourcesResponse.ok) {
          throw new Error(sourcesPayload.detail || "Unable to load sources.");
        }
        if (active) {
          setSources(sourcesPayload.sources);
          if (providersResponse.ok && providersPayload.providers) {
            setProviderCatalog(providersPayload);
            setFormState((current) => ({
              ...current,
              llmProvider: current.llmProvider || providersPayload.default_provider_id || "auto",
            }));
          }
        }
      } catch (loadError) {
        if (active) {
          setError(loadError.message);
        }
      }
    }

    loadInitialState();
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
          retrieval_mode: formState.retrievalMode,
          source_id: formState.retrievalMode === "source" ? formState.sourceId : null,
          domain: formState.domain,
          llm_provider: formState.llmProvider,
          llm_model: formState.llmModel || null,
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
      setError(formatQueryErrorMessage(submitError.message));
    } finally {
      setLoading(false);
    }
  }

  function updateField(field) {
    return function onChange(event) {
      setFormState((current) => ({ ...current, [field]: event.target.value }));
    };
  }

  function handleProviderChange(event) {
    const providerId = event.target.value;
    const nextProvider = getProviderById(providerCatalog, providerId);

    setFormState((current) => ({
      ...current,
      llmProvider: providerId,
      llmModel:
        nextProvider?.supports_custom_model && nextProvider?.models?.includes(current.llmModel)
          ? current.llmModel
          : "",
    }));
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
      setError(formatUploadErrorMessage(uploadError.message));
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

  async function handleReindexSource() {
    if (!selectedSource) {
      return;
    }

    setReindexing(true);
    setError("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/sources/${encodeURIComponent(selectedSource.source_id)}/reindex`,
        { method: "POST" }
      );
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Reindex failed.");
      }
      await loadSources();
    } catch (reindexError) {
      setError(formatQueryErrorMessage(reindexError.message));
    } finally {
      setReindexing(false);
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
            <span>Search Scope</span>
            <select value={formState.retrievalMode} onChange={updateField("retrievalMode")}>
              {retrievalModeOptions.map((mode) => (
                <option key={mode.value} value={mode.value}>
                  {mode.label}
                </option>
              ))}
            </select>
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
            <span>LLM Provider</span>
            <select value={formState.llmProvider} onChange={handleProviderChange}>
              {providerCatalog.providers.map((provider) => (
                <option key={provider.provider_id} value={provider.provider_id}>
                  {provider.label}
                  {provider.available ? "" : " · not configured"}
                </option>
              ))}
            </select>
            <small className="field-hint">
              {selectedProvider?.description || "Choose how the backend resolves the active LLM."}
            </small>
          </label>
          <label>
            <span>LLM Model</span>
            {selectedProvider?.models?.length ? (
              <select value={formState.llmModel} onChange={updateField("llmModel")}>
                <option value="">Use provider default ({selectedProvider.default_model || "auto"})</option>
                {selectedProvider.models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={formState.llmModel}
                onChange={updateField("llmModel")}
                placeholder={selectedProvider?.default_model || "Use provider default"}
                disabled={!selectedProvider?.supports_custom_model}
              />
            )}
            <small className="field-hint">
              {selectedProvider?.provider_id === "auto"
                ? "Select a concrete provider to choose a specific model, or leave Auto to let the backend resolve it."
                : "Leave this empty to preserve the provider default and fallback chain."}
            </small>
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
            <small className="field-hint">
              Accepted: `.txt`, `.md`, `.pdf`, `.csv`, `.json`. If a file is actually a ZIP/archive, the upload will be rejected with a clear message.
            </small>
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
          <button
            className="secondary-button"
            disabled={!selectedSource || reindexing || loading || uploading}
            type="button"
            onClick={handleReindexSource}
          >
            {reindexing ? "Reindexing..." : "Reindex Source"}
          </button>
        </form>
        {selectedSource ? (
          <div className="source-meta">
            <p className="hero-label">
              Selected source: {selectedSource.label} · {selectedSource.domain} · {selectedSource.origin}
            </p>
            <p className="hero-label">
              Search scope: {formState.retrievalMode === "domain" ? "all saved sources in this domain" : "selected source only"}
            </p>
            <div className="source-meta-row">
              <span className={`status-pill source-status-pill ${getSourceIndexTone(selectedSource.index_status)}`}>
                {formatSourceIndexStatus(selectedSource.index_status)}
              </span>
              {selectedSource.vector_backend ? (
                <span className="hero-label">Backend: {selectedSource.vector_backend}</span>
              ) : null}
              {selectedSource.indexed_document_count !== null && selectedSource.indexed_document_count !== undefined ? (
                <span className="hero-label">Chunks: {selectedSource.indexed_document_count}</span>
              ) : null}
            </div>
          </div>
        ) : null}
        <div className="panel">
          <h3>LLM Provider Status</h3>
          <p className="hero-label">
            Configured providers: {configuredProviderCount} · Selected: {selectedProvider?.label || "Auto"}
          </p>
          <div className="stack">
            {providerCatalog.providers.map((provider) => (
              <div className="note-card" key={provider.provider_id}>
                <div className="note-header">
                  <strong>{provider.label}</strong>
                  <div className="source-meta-row">
                    <span className={`status-pill ${getProviderAvailabilityTone(provider)}`}>
                      {formatProviderAvailability(provider)}
                    </span>
                    <span className={`status-pill ${getProviderReachabilityTone(provider)}`}>
                      {formatProviderReachability(provider)}
                    </span>
                  </div>
                </div>
                <p>{provider.description}</p>
                <p className="hero-label">
                  Default model: {provider.default_model || "auto"}
                  {provider.models?.length ? ` · Choices: ${provider.models.join(", ")}` : ""}
                </p>
                <p className="hero-label">{provider.health_message || "No health details available."}</p>
              </div>
            ))}
          </div>
        </div>
        {uploading ? <p className="hero-label">Uploading source...</p> : null}
        {reindexing ? <p className="hero-label">Refreshing vector index for the selected source...</p> : null}
        {error ? <p className="error-banner">{error}</p> : null}
      </section>

      {dashboard ? (
        <section className="results">
          <header className="results-header">
            <div>
              <p className="eyebrow">Report</p>
              <h2>{dashboard.title}</h2>
              <p className="lede">{dashboard.summary}</p>
              <p className="hero-label">
                LLM resolution: requested {dashboard.execution.requested_provider}
                {dashboard.execution.requested_model ? ` / ${dashboard.execution.requested_model}` : ""}
                {" → "}
                resolved {dashboard.execution.provider_mode}
                {dashboard.execution.provider_model ? ` / ${dashboard.execution.provider_model}` : ""}
                {dashboard.execution.used_fallback ? " · fallback used" : ""}
              </p>
              <p className="hero-label">
                LLM generated: {isLlmGenerated(dashboard.execution) ? "yes" : "no"} ·
                grounded by retrieval: {dashboard.execution.inspection?.grounded ? "yes" : "no"}
              </p>
              {getLlmFallbackWarning(dashboard.execution) ? (
                <p className="error-banner">{getLlmFallbackWarning(dashboard.execution)}</p>
              ) : null}
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
                  <dt>Agent</dt>
                  <dd>{dashboard.execution.agent_type}</dd>
                </div>
                <div>
                  <dt>Requested Provider</dt>
                  <dd>{dashboard.execution.requested_provider}</dd>
                </div>
                <div>
                  <dt>Requested Model</dt>
                  <dd>{dashboard.execution.requested_model || "provider default"}</dd>
                </div>
                <div>
                  <dt>Provider</dt>
                  <dd>{dashboard.execution.provider_mode}</dd>
                </div>
                <div>
                  <dt>Model</dt>
                  <dd>{dashboard.execution.provider_model || "fallback"}</dd>
                </div>
                <div>
                  <dt>LLM Generated</dt>
                  <dd>{isLlmGenerated(dashboard.execution) ? "yes" : "no"}</dd>
                </div>
                <div>
                  <dt>Workflow</dt>
                  <dd>{dashboard.execution.workflow_backend}</dd>
                </div>
                <div>
                  <dt>Agent Loop</dt>
                  <dd>{dashboard.execution.agent_loop || "retrieve_generate"}</dd>
                </div>
                <div>
                  <dt>Tool Calls</dt>
                  <dd>{dashboard.execution.tool_calls ?? 0}</dd>
                </div>
                <div>
                  <dt>Plan Query</dt>
                  <dd>{dashboard.execution.plan?.search_query || "No explicit retrieval refinement."}</dd>
                </div>
                <div>
                  <dt>Plan Needs Tool</dt>
                  <dd>{dashboard.execution.plan ? (dashboard.execution.plan.should_retrieve ? "yes" : "no") : "n/a"}</dd>
                </div>
                <div>
                  <dt>Compare Sources</dt>
                  <dd>{dashboard.execution.plan ? (dashboard.execution.plan.compare_sources ? "yes" : "no") : "n/a"}</dd>
                </div>
                <div>
                  <dt>Summarize Evidence</dt>
                  <dd>{dashboard.execution.plan ? (dashboard.execution.plan.summarize_evidence ? "yes" : "no") : "n/a"}</dd>
                </div>
                <div>
                  <dt>Inspection Grounded</dt>
                  <dd>{dashboard.execution.inspection ? (dashboard.execution.inspection.grounded ? "yes" : "no") : "n/a"}</dd>
                </div>
                <div>
                  <dt>Sources</dt>
                  <dd>{dashboard.source_count}</dd>
                </div>
              </dl>
            </article>

            <article className="panel">
              <h3>Graph Decisions</h3>
              <dl className="meta-list">
                <div>
                  <dt>Plan Rationale</dt>
                  <dd>{dashboard.execution.plan?.rationale || "No explicit plan data available."}</dd>
                </div>
                <div>
                  <dt>Plan Max Results</dt>
                  <dd>{dashboard.execution.plan?.max_results ?? "n/a"}</dd>
                </div>
                <div>
                  <dt>Comparison Summary</dt>
                  <dd>{dashboard.execution.comparison?.summary || "No structured comparison data available."}</dd>
                </div>
                <div>
                  <dt>Control Themes</dt>
                  <dd>
                    {dashboard.execution.comparison?.control_themes?.length
                      ? dashboard.execution.comparison.control_themes.join(", ")
                      : "No structured control themes available."}
                  </dd>
                </div>
                <div>
                  <dt>Evidence Synthesis</dt>
                  <dd>{dashboard.execution.evidence_summary?.summary || "No structured evidence synthesis available."}</dd>
                </div>
                <div>
                  <dt>Recommended Controls</dt>
                  <dd>
                    {dashboard.execution.evidence_summary?.recommended_controls?.length
                      ? dashboard.execution.evidence_summary.recommended_controls.join(", ")
                      : "No structured control recommendations available."}
                  </dd>
                </div>
                <div>
                  <dt>Inspection Summary</dt>
                  <dd>{dashboard.execution.inspection?.summary || "No structured inspection data available."}</dd>
                </div>
              </dl>
            </article>

            <article className="panel">
              <h3>Agent Trace</h3>
              <dl className="meta-list">
                <div>
                  <dt>Planned Query</dt>
                  <dd>{dashboard.execution.agent_trace?.planned_query || "No tool query planned."}</dd>
                </div>
                <div>
                  <dt>Plan Rationale</dt>
                  <dd>{dashboard.execution.agent_trace?.plan_rationale || "No retrieval refinement was needed."}</dd>
                </div>
                <div>
                  <dt>Comparison</dt>
                  <dd>{dashboard.execution.agent_trace?.comparison_summary || "No comparison summary available."}</dd>
                </div>
                <div>
                  <dt>Evidence Synthesis</dt>
                  <dd>{dashboard.execution.agent_trace?.summary_digest || "No evidence synthesis summary available."}</dd>
                </div>
                <div>
                  <dt>Evidence Review</dt>
                  <dd>{dashboard.execution.agent_trace?.evidence_summary || "No evidence review summary available."}</dd>
                </div>
                <div>
                  <dt>Grounded</dt>
                  <dd>{dashboard.execution.agent_trace?.grounded ? "yes" : "no"}</dd>
                </div>
                <div>
                  <dt>Added Sources</dt>
                  <dd>
                    {dashboard.execution.agent_trace?.added_sources?.length
                      ? dashboard.execution.agent_trace.added_sources.join(", ")
                      : "No additional sources were added."}
                  </dd>
                </div>
              </dl>
              <div className="stack timeline-stack">
                {(dashboard.execution.agent_trace?.steps || []).length ? (
                  dashboard.execution.agent_trace.steps.map((step, index) => (
                    <div className="note-card" key={`${step.label}-${index}`}>
                      <div className="note-header">
                        <strong>{step.label}</strong>
                        <span className={`severity severity-${step.status}`}>{step.status}</span>
                      </div>
                      <p>{step.detail}</p>
                    </div>
                  ))
                ) : (
                  <p className="hero-label">No agent timeline available.</p>
                )}
              </div>
            </article>

            <article className="panel">
              <h3>Evaluation</h3>
              {(() => {
                const graphScore = dashboard.evaluation?.graph_state_score ?? 0;
                const missingFieldCount = dashboard.evaluation?.graph_state_missing_fields?.length ?? 0;
                const contractMet = missingFieldCount === 0;
                const toneClass = contractMet ? "evaluation-card-success" : "evaluation-card-warning";
                const pillClass = contractMet ? "pill-success" : "pill-warning";
                const domainSections = getDomainGraphSections(dashboard.domain);

                return (
                  <>
                    <div className={`evaluation-banner ${toneClass}`}>
                      <div className="note-header">
                        <strong>Graph Contract Status</strong>
                        <span className={`status-pill evaluation-pill ${pillClass}`}>
                          {graphScore}%
                        </span>
                      </div>
                      <p>
                        {contractMet
                          ? "All expected graph-state fields were populated for this domain."
                          : `${missingFieldCount} graph field(s) still need review for this domain.`}
                      </p>
                    </div>
                    <dl className="meta-list">
                      <div>
                        <dt>Graph-State Score</dt>
                        <dd>
                          <span className={`status-pill evaluation-pill ${pillClass}`}>{graphScore}%</span>
                        </dd>
                      </div>
                      <div>
                        <dt>Contract Met</dt>
                        <dd>
                          <span className={`status-pill evaluation-pill ${pillClass}`}>
                            {contractMet ? "yes" : "no"}
                          </span>
                        </dd>
                      </div>
                      <div>
                        <dt>Expected Fields</dt>
                        <dd>{dashboard.evaluation?.graph_state_expected_fields?.length ?? 0}</dd>
                      </div>
                      <div>
                        <dt>Present Fields</dt>
                        <dd>{dashboard.evaluation?.graph_state_present_fields?.length ?? 0}</dd>
                      </div>
                      <div>
                        <dt>Missing Fields</dt>
                        <dd>{missingFieldCount}</dd>
                      </div>
                    </dl>
                    <div className="stack">
                      {domainSections.length ? (
                        <div className="note-card">
                          <div className="note-header">
                            <strong>Domain Graph Sections</strong>
                            <span className="hero-label">{domainSections.length} sections</span>
                          </div>
                          <div className="evaluation-section-grid">
                            {domainSections.map((section) => {
                              const status = getGraphSectionStatus(section, dashboard.evaluation || {});
                              const sectionPillClass = status.complete ? "pill-success" : "pill-warning";
                              return (
                                <div
                                  key={section.id}
                                  className={`evaluation-section-card ${
                                    status.complete ? "evaluation-card-success" : "evaluation-card-warning"
                                  }`}
                                >
                                  <div className="note-header">
                                    <strong>{section.label}</strong>
                                    <span className={`status-pill evaluation-pill ${sectionPillClass}`}>
                                      {status.presentCount}/{status.expectedCount}
                                    </span>
                                  </div>
                                  <p>
                                    {status.missingCount === 0
                                      ? "All expected fields are present."
                                      : `${status.missingCount} field(s) still missing in this section.`}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                      <div className={`note-card ${toneClass}`}>
                        <div className="note-header">
                          <strong>Missing Graph Fields</strong>
                          <span className={`status-pill evaluation-pill ${pillClass}`}>
                            {contractMet ? "complete" : "needs review"}
                          </span>
                        </div>
                        <p>
                          {missingFieldCount
                            ? dashboard.evaluation.graph_state_missing_fields.join(", ")
                            : "All expected graph-state fields were populated for this domain."}
                        </p>
                      </div>
                      <details className={`note-card evaluation-details ${toneClass}`}>
                        <summary>
                          {`${dashboard.domain.replace(/_/g, " ")} graph contract`}
                        </summary>
                    <div className="stack">
                      {domainSections.length ? (
                        <div className="note-card">
                          <div className="note-header">
                            <strong>Section Breakdown</strong>
                            <span className="hero-label">{dashboard.domain.replace(/_/g, " ")}</span>
                          </div>
                          <div className="stack">
                            {domainSections.map((section) => {
                              const status = getGraphSectionStatus(section, dashboard.evaluation || {});
                              const sectionFields = section.fields.filter((field) =>
                                (dashboard.evaluation?.graph_state_expected_fields || []).includes(field)
                              );

                              return (
                                <div key={section.id} className="note-card">
                                  <div className="note-header">
                                    <strong>{section.label}</strong>
                                    <span
                                      className={`status-pill evaluation-pill ${
                                        status.complete ? "pill-success" : "pill-warning"
                                      }`}
                                    >
                                      {status.complete ? "complete" : "needs review"}
                                    </span>
                                  </div>
                                  {sectionFields.length ? (
                                    <ul className="warning-list">
                                      {sectionFields.map((field) => {
                                        const isMissing = (dashboard.evaluation?.graph_state_missing_fields || []).includes(field);
                                        return (
                                          <li
                                            key={`${section.id}-${field}`}
                                            className={isMissing ? "evaluation-item-missing" : "evaluation-item-present"}
                                          >
                                            {field}
                                            {isMissing ? " · missing" : " · present"}
                                          </li>
                                        );
                                      })}
                                    </ul>
                                  ) : (
                                    <p>No expected fields are defined for this section.</p>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                      <div className="note-card">
                        <div className="note-header">
                          <strong>Expected Fields</strong>
                              <span className="hero-label">
                                {dashboard.evaluation?.graph_state_expected_fields?.length ?? 0}
                              </span>
                            </div>
                            {(dashboard.evaluation?.graph_state_expected_fields || []).length ? (
                              <ul className="warning-list">
                                {dashboard.evaluation.graph_state_expected_fields.map((field) => {
                                  const isMissing = (dashboard.evaluation?.graph_state_missing_fields || []).includes(field);
                                  return (
                                    <li key={field} className={isMissing ? "evaluation-item-missing" : "evaluation-item-present"}>
                                      {field}
                                      {isMissing ? " · missing" : " · present"}
                                    </li>
                                  );
                                })}
                              </ul>
                            ) : (
                              <p>No domain-specific graph contract is defined for this response.</p>
                            )}
                          </div>
                          <div className="note-card">
                            <div className="note-header">
                              <strong>Present Fields</strong>
                              <span className="hero-label">
                                {dashboard.evaluation?.graph_state_present_fields?.length ?? 0}
                              </span>
                            </div>
                            {(dashboard.evaluation?.graph_state_present_fields || []).length ? (
                              <ul className="warning-list">
                                {dashboard.evaluation.graph_state_present_fields.map((field) => (
                                  <li key={field} className="evaluation-item-present">{field}</li>
                                ))}
                              </ul>
                            ) : (
                              <p>No graph-state fields were populated.</p>
                            )}
                          </div>
                        </div>
                      </details>
                    </div>
                  </>
                );
              })()}
            </article>
          </div>

          <section className="panel">
            <h3>Domain Cards</h3>
            <div className="metric-grid">
              {dashboard.domain_cards.length ? (
                dashboard.domain_cards.map((card) => (
                  <div className="metric-card" key={`${card.title}-${card.value}`}>
                    <span>{card.title}</span>
                    <strong>{card.value}</strong>
                    <p className="hero-label">{card.detail}</p>
                  </div>
                ))
              ) : (
                <p className="hero-label">No domain-specific cards available.</p>
              )}
            </div>
          </section>

          <section className="panel">
            <h3>Matched Sources</h3>
            <div className="stack">
              {dashboard.matched_sources.length ? (
                dashboard.matched_sources.map((source) => (
                  <div className="note-card" key={`${source.source_id || source.source}-${source.evidence_count}`}>
                    <div className="note-header">
                      <strong>{source.source.split("/").pop()}</strong>
                      <span className="hero-label">{source.evidence_count} evidence hit(s)</span>
                    </div>
                    <p>{source.preview || "No preview available."}</p>
                    <p className="hero-label">
                      {source.domain || "unknown"} · {source.origin || "unknown"} · {source.file_type || "n/a"}
                    </p>
                  </div>
                ))
              ) : (
                <p className="hero-label">No matched source summaries available.</p>
              )}
            </div>
          </section>

          <section className="panel">
            <h3>Evidence Cards</h3>
            <div className="stack">
              {dashboard.evidence_cards.length ? (
                dashboard.evidence_cards.map((card, index) => (
                  <div className="note-card" key={`${card.source_id || card.source}-${index}`}>
                    <div className="note-header">
                      <strong>{card.title}</strong>
                      <span className={`severity severity-${card.severity}`}>{card.severity}</span>
                    </div>
                    <p>{card.detail}</p>
                    <p className="hero-label">
                      {card.source.split("/").pop()} · {card.evidence_count} evidence unit(s)
                    </p>
                  </div>
                ))
              ) : (
                <p className="hero-label">No evidence cards available.</p>
              )}
            </div>
          </section>

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
