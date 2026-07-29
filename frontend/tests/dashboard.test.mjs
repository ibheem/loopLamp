import test from "node:test";
import assert from "node:assert/strict";

import {
  defaultFormState,
  filterSourcesByDomain,
  findSourceById,
  formatQueryErrorMessage,
  formatSourceIndexStatus,
  formatUploadErrorMessage,
  formatSourceLabel,
  getSourceIndexTone,
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
