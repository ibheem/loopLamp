# loopLamp Maturity Roadmap

## Purpose

This roadmap turns the current `loopLamp` state into a practical delivery path:

1. `prototype`
2. `internal_pilot`
3. `production_ready`

The goal is to avoid overengineering while still making progress toward a dynamic, domain-aware dashboard platform with true agentic workflows.

## Current Position

`loopLamp` is currently in a **strong prototype / early pilot foundation** state.

What already exists:

- multi-domain backend and lightweight frontend
- persistent local source storage
- persistent local vector storage
- domain-wide retrieval
- dashboard-ready response contract
- explicit workflow graph in `backend/workflows/query_graph.py`
- tool-calling agent loop with observable plan / inspection / trace data

What that means in practice:

- good for architecture validation
- good for internal demos
- good for dataset and retrieval experimentation
- not yet ready for broad internal adoption without hardening

---

## Phase 1 — Prototype

### Goal

Prove that the system can ingest domain data, retrieve grounded evidence, and generate a useful dynamic dashboard response.

### Success Criteria

- API works end to end for all active domains
- dashboard UI shows structured output consistently
- source upload, source selection, and domain retrieval work reliably
- vector persistence survives restarts
- graph workflow produces observable execution metadata

### What is already done

- domain agents exist across active domains
- uploaded source registry exists
- local SQLite source metadata exists
- local Qdrant-backed persistence path exists
- dashboard includes:
  - matched sources
  - evidence cards
  - domain cards
  - execution metadata
  - graph decisions
  - agent trace

### Remaining gaps inside prototype

- more reliable domain datasets
- stronger benchmark queries per domain
- more consistent answer-quality checks
- richer UI visualization beyond the current simple dashboard layout

### Exit Criteria

Move beyond prototype when:

- each active domain has representative sample data
- each active domain has at least a small validation query set
- retrieval quality is acceptable for repeated demo scenarios
- graph metadata is stable and understandable to team members

---

## Phase 2 — Internal Pilot

### Goal

Make `loopLamp` trustworthy for a small internal user group.

### Focus Areas

#### Product usability

- make source management easier for non-technical users
- reduce need for manual dataset path handling
- improve dashboard readability and drill-down behavior

#### Data reliability

- define approved sample datasets per domain
- add domain-level data hygiene checks
- support versioning or refresh guidance for sources

#### Evaluation

- define domain-specific evaluation prompts or test suites
- add repeatable benchmark queries for each domain
- track grounding, action usefulness, and evidence quality

#### Operations

- shared deployment path for backend and frontend
- better runtime logging and error visibility
- indexing health visibility
- query failure visibility

#### Governance

- record who uploaded a source
- record when a source was indexed or refreshed
- make source deletion / refresh behavior predictable

### Recommended Deliverables

- `EVALS.md` or equivalent evaluation harness documentation
- per-domain benchmark queries and expected behaviors
- source governance workflow
- internal deployment instructions
- admin-facing source health view

### Exit Criteria

Move beyond internal pilot when:

- a small internal team can use the app without developer handholding
- source ingestion and reindex flows are stable
- core evaluation queries pass consistently
- dashboard outputs are trusted for exploratory internal use

---

## Phase 3 — Production Ready

### Goal

Make `loopLamp` durable, secure, and supportable as a real multi-user application.

### Focus Areas

#### Infrastructure

- replace local-only assumptions with deployed services
- move uploaded source storage to object/cloud storage
- use deployed Qdrant or a managed vector platform
- move app state beyond local-only SQLite where needed

#### Security

- authentication
- authorization
- role-based access
- audit logging
- secret management

#### Reliability

- backup and restore plan
- dataset recovery plan
- health checks and alerting
- performance and load testing
- failure-mode testing for ingestion and retrieval

#### Quality and release control

- CI/CD gates
- regression evaluation
- prompt and model version control
- release checklist for agent workflow changes

#### Multi-user product readiness

- tenant or workspace separation if needed
- source ownership visibility
- user-safe upload and delete controls
- admin tools for index repair and data cleanup

### Exit Criteria

Production readiness means:

- infrastructure is deployable and recoverable
- evaluation is part of release flow
- access is controlled
- data persistence is durable
- observability is sufficient for support and debugging

---

## Cross-Phase Workstreams

These should progress continuously rather than waiting for a single phase.

### 1. Domain Quality

- improve sample data
- improve benchmark queries
- improve response usefulness per domain

### 2. Agent Capability

- expand from single retrieval tool behavior
- add multiple explicit tool nodes
- support richer branching in the graph

### 3. Retrieval and Storage

- keep embeddings persistent
- improve indexing reliability
- introduce managed persistence when needed

### 4. Dashboard Evolution

- richer cards and charts
- cross-source comparisons
- deeper evidence drill-down
- user-friendly filtering

### 5. Observability

- graph decision visibility
- source-level retrieval visibility
- failure and latency metrics

---

## Recommended Next Order

This is the most practical order from today’s state:

1. build an evaluation harness per domain
2. harden source governance and persistence behavior
3. add more explicit tool nodes to the graph
4. improve dashboard UX for real internal users
5. prepare internal deployment and shared environment setup
6. add auth and production controls

---

## Immediate Next Milestones

### Milestone A — Better evaluation

- define 5 to 10 benchmark queries per domain
- capture expected grounding and action quality
- add a lightweight evaluation runner

### Milestone B — Stronger graph workflows

- introduce separate tool nodes like:
  - `retrieve_sources`
  - `compare_sources`
  - `summarize_evidence`
- keep the current `DomainReport` contract stable

### Milestone C — Internal pilot UX

- better source management UI
- clearer indexing state
- stronger dashboard visual polish

---

## Short Honest Summary

Today, `loopLamp` is:

- beyond a toy
- usable for internal demos and controlled exploration
- architecturally sound enough to continue investing in
- not yet production-ready

The right next mindset is:

- **do not rewrite**
- **do not overcomplicate**
- **harden what already works**
- **grow the graph and evaluation story deliberately**
