# {{Project name}} — Technical Blueprint

> **For coding agents and developers.** This is the implementation source of truth. Do not read the discovery material (PRD, transcripts); everything needed is here. Modules and rigour: [MODULES.md](MODULES.md).

| | |
|---|---|
| Version | {{v1.0 — YYYY-MM-DD}} |
| Size class | {{Small / Medium / Large}} (score {{N}}/18) |
| System type | {{Greenfield / Brownfield — one line on what already exists}} |
| Sources | {{PRD v? / adopted PRD `design/sources/<file>`; extra design sources, if any}} |
| Counts | {{N}} requirements · {{N}} acceptance criteria · {{N}} open questions ({{N}} blocking) · {{N}} assumptions |

## How to load this blueprint

| You are about to… | Read |
|---|---|
| Implement anything | §1 Stack & conventions, §3 Roles & permissions, §4 Shared data model |
| Implement module Mx | the above + {{`technical/mNN-<name>.md` / §6.x}} — and its rigour in [MODULES.md](MODULES.md) |
| Pick the next piece of work | [../plan/PLAN.md](../plan/PLAN.md) |
| Check a decision or an open question | {{[DECISIONS.md](DECISIONS.md) / §11}} |
| Trace a requirement | §12 |

<!-- TEMPLATE NOTE — delete before finishing.
Choose the layout BEFORE writing (references/write.md §1).
Single file: everything here; Medium replaces §11 with a one-line pointer to DECISIONS.md.
Core + module files: §6 keeps only the module index table; each module's detail goes to technical/mNN-<name>.md;
§9 keeps a short summary and points to technical/x-cross-cutting.md; §5 keeps only state machines that span modules.
ONLY a module's own heading may name its module ID (`### 6.1 M1 Identity`): gate G2 finds a module's spec by the first
heading containing "M1", so entity, state-machine and flow headings carry no module ID (write "Owner: M1" below the
heading). Never put REQ IDs in a row whose first cell is a module ID.
No work-package table here — the plan is plan/PLAN.md.
Drop any section that does not apply with one line: "None — <reason>." -->

---

## 1. Tech stack & conventions

| Layer | Choice | Reason |
|---|---|---|
| {{Backend}} | {{…}} | {{…}} |
| {{Frontend web}} | | |
| {{Database}} | | |
| {{Hosting}} | | |
| {{Auth}} | | |

**Conventions**
- Repository layout: {{folders; where each module's code lives — the same globs as MODULES.md → Paths}}
- Naming: {{entities, tables, states `snake_case`, events `entity.verb_past`}}
- API style: {{REST JSON / …}}; error format: {{`{ "error": { "code", "message", "details" } }`}}; status codes: {{401 / 403 / 404 / 409 / 422}}
- Dates and money: {{UTC ISO-8601; money as integer minor units + currency code}}
- Testing: {{unit + integration; every acceptance criterion (AC-###) has a test named after it; commands}}
- Branches and commits: put the work package ID first — branch `WP-07-short-title`, commit `WP-07: …`, and "closes WP-07" in the commit that finishes it (Atlas infers progress from these)
- Environments & configuration: {{dev / staging / production; environment variables an implementer must know — never their values}}

## 2. Platforms & architecture

### 2.1 Platforms
| Platform | Users (roles) | Purpose | Talks to |
|---|---|---|---|
| {{Admin web dashboard}} | {{Admin, Finance}} | {{…}} | {{core API}} |

### 2.2 System context
```mermaid
flowchart LR
    %% {{people → platforms → backend → external systems}}
```

### 2.3 Containers / components
```mermaid
flowchart TB
    %% {{deployables, database, jobs, storage, third parties — Medium and Large only}}
```

### 2.4 Architecture decisions
| # | Decision | Reason | Trade-off |
|---|---|---|---|
| AD-1 | {{Modular monolith}} | {{…}} | {{…}} |

### 2.5 Out of scope
{{What this system deliberately does not do: PRD FRs marked out of scope / rejected / deferred (cite the FR IDs), exclusions in PRD §7 — so nobody builds them by mistake.}}

## 3. Roles & permissions

| Action \ Role | {{Role A}} | {{Role B}} | {{Role C}} | REQ |
|---|---|---|---|---|
| {{create order}} | ✅ | ❌ | ✅ own only | REQ-… |

Rules: {{permission checks enforced on the server; "own only" = record.owner_id == user.id; cross-tenant access returns 404}}

## 4. Shared data model

Entities used by more than one module. Module-owned detail lives with the module.

```mermaid
erDiagram
    %% {{ENTITY ||--o{ OTHER : relation}}
```

### 4.1 {{Entity}}
Owner: {{module ID}} · Sensitivity: {{public / internal / personal / restricted}} · Retention: {{…}}

| Field | Type | Constraints | Notes / REQ |
|---|---|---|---|
| id | uuid | PK | |
| {{status}} | enum | see §5.1 | |

## 5. State machines

### 5.1 {{Entity}} lifecycle
```mermaid
stateDiagram-v2
    [*] --> {{initial}}
```

| From | Event / trigger | Actor | Guard | To | Side effects | REQ |
|---|---|---|---|---|---|---|
| {{draft}} | {{submit}} | {{Customer}} | {{all required fields set}} | {{submitted}} | {{notify manager}} | REQ-… |

Invalid transitions return {{409 INVALID_TRANSITION}}. Timed transitions: {{job name, schedule}}.

## 6. Modules

| Module | Name | Rigour | Purpose | Owns (entities) | Depends on | Spec |
|---|---|---|---|---|---|---|
| M1 | {{Identity & roles}} | {{Critical}} | {{…}} | {{User, Role}} | — | {{§6.1 / technical/m01-identity.md}} |

<!-- TEMPLATE NOTE — delete before finishing. Depth per module follows its rigour:
Light → purpose, use cases, acceptance criteria. Standard → + entities, business rules, API, state machines where states exist.
Critical → + errors & edge cases, failure & rollback, threat notes, audit trail. Delete the blocks a level does not need.
The Depends on column feeds the plan seed: list module IDs only. -->

### 6.1 M1 {{Module name}}

**Purpose:** {{one sentence}} · **Rigour:** {{Light / Standard / Critical}} · **Requirements:** {{REQ-001–REQ-012}}

**Entities owned** — {{fields, types and constraints for entities only this module uses; shared ones are in §4}}
| Entity.field | Type | Constraints | Notes / REQ |
|---|---|---|---|

**Use cases**
| UC | Actor | Main flow | Alternates / errors | REQ |
|---|---|---|---|---|
| UC-1 | | 1. … 2. … | {{…}} | |

**Business rules**
| # | Rule | REQ / BR |
|---|---|---|
| 1 | {{…}} | REQ-… (BR-…) |

**API / interfaces**
| Method & path | Auth (roles) | Request | Response | Errors | REQ |
|---|---|---|---|---|---|
| {{POST /orders}} | {{Customer}} | {{`{ items: [{product_id, qty}] }`}} | {{201 Order}} | {{422 VALIDATION, 409 OUT_OF_STOCK}} | REQ-… |

**Screens / dashboards**
| Screen | Platform | Roles | Shows / actions | Data from modules | REQ |
|---|---|---|---|---|---|

**Notifications & jobs**
| Trigger | Channel / schedule | Recipient | Content | REQ |
|---|---|---|---|---|

**Errors & edge cases** *(Critical)*
| Situation | Behaviour | REQ |
|---|---|---|

**Failure & rollback** *(Critical)* — {{what happens when each step or dependency fails; what is rolled back, retried or compensated; what the user sees}}

**Threat notes** *(Critical)*
| Threat / abuse case | Mitigation | REQ |
|---|---|---|

**Audit trail** *(Critical)* — {{which actions are logged, with who / what / when}}

**Acceptance criteria**
| AC | REQ | Given / when / then |
|---|---|---|
| AC-NEW | {{REQ-…}} | {{Given …, when …, then …}} |

## 7. Key cross-module flows
### 7.1 {{Flow name}}
```mermaid
sequenceDiagram
```

## 8. Integrations

| System | Purpose | Direction | Auth | Data | Failure handling | REQ |
|---|---|---|---|---|---|---|
| {{Payment provider}} | | {{out + webhook in}} | {{API key, signed webhooks}} | | {{retry with backoff, idempotency key, reconcile job}} | |

## 9. Non-functional requirements
### 9.1 Security & privacy
### 9.2 Performance & scalability
### 9.3 Reliability
### 9.4 Observability & operations
### 9.5 Usability & accessibility
### 9.6 Test strategy
{{what is unit / integration / end-to-end tested; fakes for third parties; test data; what must never be called in tests}}
### 9.7 Data migration & seed data
{{imports from legacy systems or spreadsheets, cut-over steps, first admin, seed catalogues — or "None — new system with no prior data."}}
### 9.8 Acceptance criteria (cross-cutting)
| AC | REQ | Given / when / then |
|---|---|---|
| AC-NEW | {{REQ-…}} | {{Given …, when …, then …}} |

## 10. Build order

Module dependencies — what must exist before what (an arrow means "before"; labels start with the module ID). Phases and work packages: [../plan/PLAN.md](../plan/PLAN.md).

```mermaid
flowchart TD
    %% {{m1["M1 Identity"] --> m2["M2 Orders"]}}
```

## 11. Decisions, assumptions & open questions

### 11.1 Assumptions
| ID | Assumption | Affects | Confirm with |
|---|---|---|---|
| ASM-T1 | {{…}} | {{…}} | {{…}} |

### 11.2 Open questions
| ID | Question | Affects | Blocking | Recommended default | Owner | Status |
|---|---|---|---|---|---|---|
| OQ-1 | {{…}} | {{…}} | {{yes / no}} | {{…}} | {{Team / Client via Alice}} | {{open / asked (N-##) / answered}} |

## 12. Traceability

Per-requirement table (source → REQ → spec → AC → WP): `_work/traceability.md`. It and the summary below are generated by `register.py trace` — do not edit them by hand.

<!-- trace-summary:start -->
<!-- trace-summary:end -->

## 13. Changelog
| Version | Date | Change |
|---|---|---|
| v1.0 | {{YYYY-MM-DD}} | Initial blueprint from {{PRD vX}} |
