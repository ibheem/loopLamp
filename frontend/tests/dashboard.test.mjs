import test from "node:test";
import assert from "node:assert/strict";

import {
  defaultProviderCatalog,
  defaultFormState,
  filterSourcesByDomain,
  findSourceById,
  formatProviderAvailability,
  formatProviderReachability,
  formatQueryErrorMessage,
  formatSourceIndexStatus,
  formatUploadErrorMessage,
  formatSourceLabel,
  getDomainGraphSections,
  getLlmFallbackWarning,
  getProviderAvailabilityTone,
  getProviderReachabilityTone,
  getProviderById,
  getGraphSectionStatus,
  getSourceIndexTone,
  getPreferredSourceId,
  getStatusTone,
  groupSourcesByDomain,
  isLlmGenerated,
  retrievalModeOptions,
} from "../lib/dashboard.js";

test("default form state starts with telecom domain", () => {
  assert.equal(defaultFormState.domain, "telecom_security");
  assert.equal(defaultFormState.sourceId, "");
  assert.equal(defaultFormState.retrievalMode, "domain");
  assert.equal(defaultFormState.llmProvider, "auto");
  assert.equal(defaultFormState.llmModel, "");
});

test("default provider catalog exposes auto selection", () => {
  assert.equal(defaultProviderCatalog.default_provider_id, "auto");
  assert.equal(defaultProviderCatalog.providers[0].provider_id, "auto");
});

test("retrieval mode options expose domain and source modes", () => {
  assert.deepEqual(
    retrievalModeOptions.map((mode) => mode.value),
    ["domain", "source"]
  );
});

test("status tone maps dashboard levels", () => {
  assert.equal(getStatusTone("success"), "pill-success");
  assert.equal(getStatusTone("warning"), "pill-warning");
  assert.equal(getStatusTone("info"), "pill-info");
});

test("filterSourcesByDomain includes general sources", () => {
  const sources = [
    { source_id: "1", domain: "telecom_security" },
    { source_id: "2", domain: "general" },
    { source_id: "3", domain: "medical_qa" },
  ];

  const filtered = filterSourcesByDomain(sources, "telecom_security");

  assert.deepEqual(
    filtered.map((source) => source.source_id),
    ["1", "2"]
  );
});

test("formatSourceLabel includes origin", () => {
  assert.equal(
    formatSourceLabel({ label: "telecom_incident.txt", origin: "sample" }),
    "telecom_incident.txt · sample"
  );
});

test("groupSourcesByDomain builds grouped options", () => {
  const groups = groupSourcesByDomain([
    { source_id: "2", label: "b.txt", domain: "medical_qa" },
    { source_id: "1", label: "a.txt", domain: "telecom_security" },
    { source_id: "3", label: "c.txt", domain: "medical_qa" },
  ]);

  assert.deepEqual(groups.map((group) => group.domain), ["medical_qa", "telecom_security"]);
  assert.deepEqual(groups[0].sources.map((source) => source.label), ["b.txt", "c.txt"]);
});

test("findSourceById returns matched source", () => {
  const source = findSourceById([{ source_id: "abc", domain: "general" }], "abc");

  assert.equal(source?.source_id, "abc");
});

test("getProviderById returns matched provider", () => {
  const provider = getProviderById(
    {
      providers: [
        { provider_id: "auto", label: "Auto" },
        { provider_id: "openai", label: "OpenAI" },
      ],
    },
    "openai"
  );

  assert.equal(provider?.label, "OpenAI");
});

test("provider availability helpers map configured state", () => {
  assert.equal(formatProviderAvailability({ available: true }), "Configured");
  assert.equal(formatProviderAvailability({ available: false }), "Not configured");
  assert.equal(getProviderAvailabilityTone({ available: true }), "pill-success");
  assert.equal(getProviderAvailabilityTone({ available: false }), "pill-warning");
  assert.equal(formatProviderReachability({ configured: true, reachable: true }), "Reachable");
  assert.equal(formatProviderReachability({ configured: true, reachable: false }), "Unreachable");
  assert.equal(formatProviderReachability({ configured: false, reachable: false }), "Not checked");
  assert.equal(getProviderReachabilityTone({ configured: true, reachable: true }), "pill-success");
  assert.equal(getProviderReachabilityTone({ configured: true, reachable: false }), "pill-warning");
  assert.equal(getProviderReachabilityTone({ configured: false, reachable: false }), "pill-info");
});

test("llm generated helper reflects explicit execution flag", () => {
  assert.equal(isLlmGenerated({ llm_generated: true }), true);
  assert.equal(isLlmGenerated({ llm_generated: false }), false);
});

test("fallback warning explains provider failure clearly", () => {
  assert.match(
    getLlmFallbackWarning({
      used_fallback: true,
      requested_provider: "ollama",
    }),
    /Provider selected but unreachable or unavailable \(ollama\) — deterministic fallback used\./
  );

  assert.match(
    getLlmFallbackWarning({
      used_fallback: true,
      requested_provider: "auto",
    }),
    /Configured provider could not serve this request/
  );

  assert.equal(getLlmFallbackWarning({ used_fallback: false }), "");
});

test("getPreferredSourceId keeps matching current source", () => {
  const sourceId = getPreferredSourceId(
    [
      { source_id: "general-1", domain: "general" },
      { source_id: "telecom-1", domain: "telecom_security" },
    ],
    "telecom_security",
    "telecom-1"
  );

  assert.equal(sourceId, "telecom-1");
});

test("getPreferredSourceId falls back to selected domain", () => {
  const sourceId = getPreferredSourceId(
    [
      { source_id: "general-1", domain: "general" },
      { source_id: "finance-1", domain: "financial_risk" },
      { source_id: "telecom-1", domain: "telecom_security" },
    ],
    "financial_risk",
    "telecom-1"
  );

  assert.equal(sourceId, "finance-1");
});

test("formatUploadErrorMessage explains zip-disguised files clearly", () => {
  const message = formatUploadErrorMessage(
    "Uploaded file content does not match .json and appears to be a ZIP archive."
  );

  assert.match(message, /actually a ZIP archive/i);
  assert.match(message, /extract it first|upload the real file/i);
});

test("formatUploadErrorMessage explains unsupported file types clearly", () => {
  const message = formatUploadErrorMessage("Unsupported file type: .docx");

  assert.match(message, /TXT, MD, PDF, CSV, and JSON/i);
});

test("formatQueryErrorMessage explains missing source selection clearly", () => {
  const message = formatQueryErrorMessage("Unknown source_id: upload:old-file.json");

  assert.match(message, /selected source no longer exists/i);
  assert.match(message, /refresh sources/i);
});

test("formatQueryErrorMessage explains missing source file clearly", () => {
  const message = formatQueryErrorMessage("JSON not found: uploaded_sources/missing.json");

  assert.match(message, /source file could not be found/i);
  assert.match(message, /re-upload/i);
});

test("formatQueryErrorMessage explains unsupported domain clearly", () => {
  const message = formatQueryErrorMessage("Unsupported domain 'foo'. Supported domains: telecom_security");

  assert.match(message, /domain is not supported/i);
});

test("formatQueryErrorMessage explains missing domain sources clearly", () => {
  const message = formatQueryErrorMessage("No saved sources are available for domain 'medical_qa'.");

  assert.match(message, /no saved sources yet for this domain/i);
});

test("formatSourceIndexStatus maps source index states clearly", () => {
  assert.equal(formatSourceIndexStatus("indexed"), "Indexed");
  assert.equal(formatSourceIndexStatus("failed"), "Index failed");
  assert.equal(formatSourceIndexStatus("not_indexed"), "Not indexed");
});

test("getSourceIndexTone maps source index states to pill styles", () => {
  assert.equal(getSourceIndexTone("indexed"), "pill-success");
  assert.equal(getSourceIndexTone("failed"), "pill-danger");
  assert.equal(getSourceIndexTone("not_indexed"), "pill-info");
});

test("getDomainGraphSections returns ecommerce-focused sections", () => {
  const sections = getDomainGraphSections("ecommerce");

  assert.deepEqual(
    sections.map((section) => section.label),
    ["Policy", "Resolution", "Fulfillment"]
  );
});

test("getGraphSectionStatus reports completion counts", () => {
  const section = {
    id: "policy",
    label: "Policy",
    fields: ["comparison.policy_constraints", "evidence_summary.refund_basis"],
  };
  const status = getGraphSectionStatus(section, {
    graph_state_expected_fields: ["comparison.policy_constraints", "evidence_summary.refund_basis"],
    graph_state_missing_fields: ["comparison.policy_constraints"],
  });

  assert.equal(status.expectedCount, 2);
  assert.equal(status.presentCount, 1);
  assert.equal(status.missingCount, 1);
  assert.equal(status.complete, false);
});

test("matched source style inputs can be rendered from dashboard payload shape", () => {
  const payload = {
    execution: {
      agent_type: "ToolCallingReportAgent",
      requested_provider: "auto",
      requested_model: "",
      provider_mode: "openai",
      provider_model: "gpt-5-mini",
      vector_backend: "qdrant_server",
      llm_generated: true,
      workflow_backend: "fallback",
      tool_calls: 1,
      agent_loop: "plan_retrieve_compare_summarize_inspect_generate",
      plan: {
        should_retrieve: true,
        search_query: "refund eligibility delayed shipment review",
        max_results: 2,
        rationale: "Need policy-aware refund evidence.",
        compare_sources: true,
        summarize_evidence: true,
      },
      comparison: {
        summary: "The order event and return policy align on refund eligibility after the delay window.",
        compared_sources: ["orders.csv", "return_policy.md"],
        consensus_points: ["Delayed shipment can qualify for refund review."],
        conflicts: [],
        control_themes: ["refund_governance"],
        obligations: ["Check refund policy window"],
      },
      evidence_summary: {
        summary: "The strongest evidence supports validating delay length against the refund policy window.",
        key_points: ["Check delay duration.", "Match it to the policy window."],
        cited_sources: ["orders.csv", "return_policy.md"],
        decision_basis: ["Order delay exists.", "Policy window defines eligibility."],
        recommended_controls: ["Validate refund window"],
        follow_up_checks: ["Confirm shipment timestamp quality"],
      },
      inspection: {
        grounded: true,
        summary: "The retrieved evidence supports refund validation against delay and policy windows.",
      },
      agent_trace: {
        planned_query: "refund eligibility delayed shipment review",
        plan_rationale: "Need policy-aware refund evidence.",
        comparison_summary: "The order event and return policy align on refund eligibility after the delay window.",
        evidence_summary: "The retrieved evidence supports refund validation against delay and policy windows.",
        summary_digest: "The strongest evidence supports validating delay length against the refund policy window.",
        grounded: true,
        added_sources: ["return_policy.md"],
        steps: [
          {
            label: "Initial Retrieval",
            detail: "Started with 1 retrieved evidence chunk(s).",
            status: "info",
          },
          {
            label: "Retrieve Sources",
            detail: "Retrieve tool added 1 source(s): return_policy.md.",
            status: "success",
          },
        ],
      },
    },
    evaluation: {
      grounded: true,
      has_sources: true,
      has_recommendations: true,
      issues: [],
      graph_state_score: 100,
      graph_state_expected_fields: [
        "comparison.order_signals",
        "comparison.policy_constraints",
        "comparison.customer_resolution_actions",
        "evidence_summary.refund_basis",
        "evidence_summary.resolution_plan",
      ],
      graph_state_present_fields: [
        "comparison.order_signals",
        "comparison.policy_constraints",
        "comparison.customer_resolution_actions",
        "evidence_summary.refund_basis",
        "evidence_summary.resolution_plan",
      ],
      graph_state_missing_fields: [],
    },
    domain_cards: [
      {
        title: "Refund Pressure",
        value: "2",
        detail: "Refund-related evidence appears twice.",
        severity: "high",
      },
    ],
    matched_sources: [
      {
        source: "test_data/telecom_incident.txt",
        source_id: "sample:telecom_security:telecom_incident.txt",
        domain: "telecom_security",
        origin: "sample",
        evidence_count: 2,
        file_type: "text",
        preview: "SS7 routing instability observed.",
      },
    ],
    evidence_cards: [
      {
        title: "SS7 routing evidence",
        detail: "Routing instability was observed on the roaming edge.",
        source: "test_data/telecom_incident.txt",
        source_id: "sample:telecom_security:telecom_incident.txt",
        evidence_count: 1,
        severity: "high",
      },
    ],
  };

  assert.equal(payload.domain_cards[0].title, "Refund Pressure");
  assert.equal(payload.execution.tool_calls, 1);
  assert.equal(payload.execution.agent_loop, "plan_retrieve_compare_summarize_inspect_generate");
  assert.equal(payload.execution.plan.search_query, "refund eligibility delayed shipment review");
  assert.equal(payload.execution.plan.compare_sources, true);
  assert.equal(payload.execution.comparison.compared_sources[1], "return_policy.md");
  assert.equal(payload.execution.comparison.control_themes[0], "refund_governance");
  assert.equal(payload.execution.inspection.grounded, true);
  assert.equal(payload.execution.agent_trace.planned_query, "refund eligibility delayed shipment review");
  assert.equal(payload.execution.agent_trace.comparison_summary, "The order event and return policy align on refund eligibility after the delay window.");
  assert.equal(payload.execution.agent_trace.grounded, true);
  assert.equal(payload.execution.evidence_summary.recommended_controls[0], "Validate refund window");
  assert.equal(payload.execution.agent_trace.added_sources[0], "return_policy.md");
  assert.equal(payload.execution.agent_trace.steps[1].label, "Retrieve Sources");
  assert.equal(payload.execution.requested_provider, "auto");
  assert.equal(payload.execution.provider_mode, "openai");
  assert.equal(payload.execution.vector_backend, "qdrant_server");
  assert.equal(payload.execution.llm_generated, true);
  assert.equal(payload.evaluation.graph_state_score, 100);
  assert.equal(payload.evaluation.graph_state_missing_fields.length, 0);
  assert.equal(payload.evaluation.graph_state_expected_fields[0], "comparison.order_signals");
  assert.equal(payload.evaluation.graph_state_present_fields[4], "evidence_summary.resolution_plan");
  assert.equal(payload.matched_sources[0].evidence_count, 2);
  assert.equal(payload.evidence_cards[0].severity, "high");
});
