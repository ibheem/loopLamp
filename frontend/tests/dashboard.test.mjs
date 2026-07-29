import test from "node:test";
import assert from "node:assert/strict";

import {
  defaultFormState,
  filterSourcesByDomain,
  findSourceById,
  formatSourceLabel,
  getPreferredSourceId,
  getStatusTone,
  groupSourcesByDomain,
} from "../lib/dashboard.js";

test("default form state starts with telecom domain", () => {
  assert.equal(defaultFormState.domain, "telecom_security");
  assert.equal(defaultFormState.sourceId, "");
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
