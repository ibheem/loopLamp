# loopLamp API Usage Guide

## Purpose

This guide gives you copy-paste request bodies and a simple order of operations for testing the app from Swagger at `http://127.0.0.1:8000/docs`.

Use this when you want to:

- verify the backend is running
- test with sample sources already registered by the app
- upload a new file and query it
- generate the dashboard payload used by the frontend

## Before you start

Make sure the backend is running:

```bash
cd loopLamp
source .venv/bin/activate
uvicorn backend.app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Recommended Swagger test flow

Use the endpoints in this order:

1. `GET /`
2. `GET /sources`
3. `POST /dashboard/report` with a sample `source_id`
4. `POST /sources/upload`
5. `GET /sources` again
6. `POST /query` or `POST /dashboard/report` with the uploaded `source_id`
7. `DELETE /sources/{source_id}` if you want to clean up an uploaded file

## 1. Health check

Open `GET /` and click `Try it out` → `Execute`.

Expected response:

```json
{
  "message": "Agentic System Backend Ready",
  "workflow": "query_pipeline"
}
```

## 2. List saved sources

Open `GET /sources` and click `Execute`.

You should see sample records similar to:

```json
{
  "sources": [
    {
      "source_id": "sample:telecom_security:telecom_incident.txt",
      "label": "telecom_incident.txt",
      "domain": "telecom_security",
      "path": "test_data/telecom_incident.txt",
      "file_type": ".txt",
      "origin": "sample",
      "uploaded_at": null
    }
  ]
}
```

Use a `source_id` from this response in the next steps.

## 3. Generate a dashboard from a sample source

Open `POST /dashboard/report`, click `Try it out`, and paste this body:

```json
{
  "query": "What action is recommended for the SS7 issue?",
  "source_id": "sample:telecom_security:telecom_incident.txt",
  "domain": "telecom_security",
  "max_results": 2
}
```

You should get a structured dashboard payload with:

- `title`
- `summary`
- `status`
- `metrics`
- `highlights`
- `actions`
- `execution`
- `evaluation`

## 4. Upload a new source

Open `POST /sources/upload`, click `Try it out`, and paste:

```json
{
  "filename": "field_notes.txt",
  "domain": "general",
  "content_base64": "U1M3IG1pdGlnYXRpb24gYWN0aW9ucyBmb3IgdGhlIG9wZXJhdGlvbnMgdGVhbS4="
}
```

That base64 decodes to a short text payload, so you can test uploads immediately from Swagger without preparing a file first.

Expected response shape:

```json
{
  "source": {
    "source_id": "upload:20260728061500_field_notes.txt",
    "label": "field_notes.txt",
    "domain": "general",
    "path": "uploaded_sources/20260728061500_field_notes.txt",
    "file_type": ".txt",
    "origin": "upload",
    "uploaded_at": "2026-07-28T06:15:00+00:00"
  }
}
```

Copy the returned `source.source_id` for the next step.

## 5. Query with an uploaded source

Open `POST /query`, click `Try it out`, and paste:

```json
{
  "query": "Summarize the uploaded mitigation note.",
  "source_id": "upload:20260728061500_field_notes.txt",
  "domain": "general",
  "max_results": 2
}
```

Replace the `source_id` with the actual value returned by your upload call.

This endpoint returns the full `QueryResponse`, including:

- `answer`
- `report`
- `sources`
- `execution`
- `evaluation`

## 6. Generate a dashboard from an uploaded source

Open `POST /dashboard/report` again and paste:

```json
{
  "query": "What mitigation action is described in the uploaded note?",
  "source_id": "upload:20260728061500_field_notes.txt",
  "domain": "general",
  "max_results": 2
}
```

Again, replace the `source_id` with your real uploaded source identifier.

This is the same payload shape the Next.js frontend uses.

## 7. Delete an uploaded source

Open `DELETE /sources/{source_id}`, click `Try it out`, and set:

```text
upload:20260728061500_field_notes.txt
```

Replace it with your real uploaded source id if needed.

Expected response:

```json
{
  "source_id": "upload:20260728061500_field_notes.txt",
  "deleted": true
}
```

Notes:

- only uploaded sources can be deleted
- sample sources like `sample:telecom_security:telecom_incident.txt` are read-only

## Common test payloads by domain

### Telecom

```json
{
  "query": "What action is recommended for the SS7 issue?",
  "source_id": "sample:telecom_security:telecom_incident.txt",
  "domain": "telecom_security",
  "max_results": 2
}
```

### Finance

```json
{
  "query": "Summarize financial accountability rules.",
  "source_id": "sample:financial_risk:FInal_GFR_upto_31_07_2024.pdf",
  "domain": "financial_risk",
  "max_results": 3
}
```

### Medical

Use `GET /sources` first and pick the sample `medical_qa` `source_id` shown by your local environment, then run:

```json
{
  "query": "What is the recommended next step for this medical case?",
  "source_id": "sample:medical_qa:<your-medical-source-file>",
  "domain": "medical_qa",
  "max_results": 3
}
```

If your local medical sample filename is different, keep the same structure and replace only the `source_id`.

### Banking

```json
{
  "query": "What should be done for a failed ATM debit complaint?",
  "source_id": "sample:banking_assistant:atm_notice.txt",
  "domain": "banking_assistant",
  "max_results": 2
}
```

You can also test banking service policy retrieval with:

```json
{
  "query": "What service charge guidance is mentioned?",
  "source_id": "sample:banking_assistant:service_charges.md",
  "domain": "banking_assistant",
  "max_results": 2
}
```

### Automotive

```json
{
  "query": "What does the fault-code guidance recommend for brake inspection?",
  "source_id": "sample:automotive:service_manual.txt",
  "domain": "automotive",
  "max_results": 2
}
```

You can also test DTC-oriented retrieval with:

```json
{
  "query": "What action is associated with DTC P0420?",
  "source_id": "sample:automotive:dtc_fault_codes.csv",
  "domain": "automotive",
  "max_results": 2
}
```

### Manufacturing

```json
{
  "query": "What should happen after a quality defect is reported?",
  "source_id": "sample:manufacturing:quality_incident.txt",
  "domain": "manufacturing",
  "max_results": 2
}
```

You can also test production and SOP retrieval with:

```json
{
  "query": "What process guidance applies before restarting the line?",
  "source_id": "sample:manufacturing:sop_guidelines.md",
  "domain": "manufacturing",
  "max_results": 2
}
```

### Ecommerce

```json
{
  "query": "What should be done for a delayed order with a refund request?",
  "source_id": "sample:ecommerce:customer_issue.txt",
  "domain": "ecommerce",
  "max_results": 2
}
```

You can also test returns and catalog retrieval with:

```json
{
  "query": "What return policy guidance applies for an opened product?",
  "source_id": "sample:ecommerce:return_policy.md",
  "domain": "ecommerce",
  "max_results": 2
}
```

## How to create your own base64 content quickly

If you want to test another text payload from terminal:

```bash
printf 'New contextual note for testing.' | base64
```

Then paste the output into `content_base64` for `POST /sources/upload`.

## Troubleshooting

### `400 Unsupported file type`

Only these upload types are accepted:

- `.txt`
- `.md`
- `.pdf`
- `.csv`
- `.json`

### `400 Either document_path or source_id must be provided`

For Swagger testing, prefer `source_id`.

`source_id` is safer than raw `document_path` because it uses a source already known to the backend registry.

### `404 Unknown source_id`

Run `GET /sources` again and copy the exact `source_id` value.

### Frontend works but Swagger fails

Make sure you are using the backend docs at exactly:

```text
http://127.0.0.1:8000/docs
```

and not the frontend app at `http://localhost:3000`.
