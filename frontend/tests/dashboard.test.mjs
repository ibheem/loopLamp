import test from "node:test";
import assert from "node:assert/strict";

import { defaultFormState, getStatusTone } from "../lib/dashboard.js";

test("default form state points at the sample telecom document", () => {
  assert.equal(defaultFormState.documentPath, "test_data/telecom_incident.txt");
  assert.equal(defaultFormState.domain, "telecom_security");
});

test("status tone maps dashboard levels", () => {
  assert.equal(getStatusTone("success"), "pill-success");
  assert.equal(getStatusTone("warning"), "pill-warning");
  assert.equal(getStatusTone("info"), "pill-info");
});
