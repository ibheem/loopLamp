# loopLamp Domain Roadmap

## Goal

`loopLamp` should evolve as one reusable multi-domain platform, not as separate one-off apps.

Every new domain should reuse:

- the same API contracts
- the same `DomainReport` output schema
- the same dashboard transformation flow
- the same orchestration skeleton

Only these parts should vary by domain:

- prompt / agent instructions
- retrieval sources
- evaluation rules
- domain-specific sample data

## Active Domain Set

### Implemented

1. `telecom_security`
2. `financial_risk`
3. `medical_qa`

### Planned

4. `banking_assistant`
5. `automotive`
6. `manufacturing`
7. `financial_sentiment`
8. `sebi_regulatory`

## Domain Patterns

### `rag_documents`

Domains:

- `telecom_security`
- `financial_risk`
- `medical_qa`
- `sebi_regulatory`

Typical sources:

- PDFs
- text documents
- advisories
- policies
- FAQs

Implementation shape:

- document ingestion
- retrieval
- domain agent
- structured `DomainReport`

### `rag_structured_hybrid`

Domains:

- `banking_assistant`
- `automotive`
- `manufacturing`

Typical sources:

- CSV / tabular operational data
- policy or SOP documents
- notices / manuals / logs

Implementation shape:

- structured data analysis
- document retrieval
- merged domain report

### `api_analytics_llm`

Domains:

- `financial_sentiment`

Typical sources:

- external APIs
- cached JSON payloads
- market data tables

Implementation shape:

- API ingestion
- analytics layer
- LLM summarization
- dashboard trend output

## Recommended Onboarding Order

1. `telecom_security`
2. `financial_risk`
3. `medical_qa`
4. `banking_assistant`
5. `automotive`
6. `manufacturing`
7. `financial_sentiment`
8. `sebi_regulatory`

This order keeps the project from overcomplicating too early:

- first prove reusable RAG across two more domains
- then handle hybrid structured + unstructured data
- then add API-driven analytics
- then add specialized regulatory expansion

## Recommended `test_data/` Layout

```text
test_data/
  telecom_security/
    telecom_incident.txt
    threat_advisory.pdf
    ss7_logs.txt
  finance/
    FInal_GFR_upto_31_07_2024.pdf
    master-circular.pdf
    SEBI Booklet.pdf
  healthcare/
    GENERAL PRINCIPLES OF PHARMACOLOGY.pdf
    Harrison_s Principles of Internal Medicine.pdf
    HealthCareMagic-100k.json
  banking_assistant/
    transactions.csv
    service_charges.pdf
    atm_notice.txt
  automotive/
    service_manual.txt
    dtc_fault_codes.csv
    maintenance_bulletin.pdf
  manufacturing/
    production_log.csv
    sop_guidelines.pdf
    quality_incident.txt
  financial_sentiment/
    news_sample.json
    stock_prices_sample.csv
  sebi_regulatory/
    sebi_faq.pdf
    circular_sample.pdf
```

## Onboarding Checklist For Every New Domain

1. Add sample files under `test_data/<domain>/`
2. Add or configure a domain agent
3. Add at least 3 reference queries
4. Add evaluator rules for unsafe or weak outputs
5. Add `/query` contract tests
6. Add `/dashboard/report` contract tests
7. Confirm output fits the same `DomainReport` schema

## Automotive And Manufacturing

These two domains are now explicitly in scope.

### Automotive

Suggested use cases:

- DTC / fault code interpretation
- maintenance bulletin summarization
- repair recommendation support
- subsystem issue identification

Suggested inputs:

- service manuals
- bulletins
- fault code tables
- workshop logs

### Manufacturing

Suggested use cases:

- production anomaly analysis
- SOP retrieval
- quality incident summarization
- corrective action support

Suggested inputs:

- production logs
- machine metrics
- SOP documents
- quality reports

## Next Recommended Implementation

The next domain to implement should be `banking_assistant`.
