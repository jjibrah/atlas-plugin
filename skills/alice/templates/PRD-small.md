# {{Client}} — {{Project name}} · Product Requirements Document

<!-- legend:start -->
> **Internal — not for the client.** The source of truth for what the client needs and what we will build. Every fact is traceable: `[M02@00:14:32]` = said in meeting M02 at that time · `[d3-002]` = client document · `[U-03]` = clarified by our team · `[D-05]` = agreed decision · `[P-04]` = our proposal · `[RS-03]` = research · `[ASM-02]` = assumption our team approved · `[Q-007]` = waiting on the client. Client-facing: [PROPOSAL.md](PROPOSAL.md) and [QUESTIONS.md](QUESTIONS.md).
<!-- legend:end -->

| | |
|---|---|
| Version | {{v0.1 — YYYY-MM-DD}} |
| Status | {{Draft — discovery in progress / Approved by client}} |
| Prepared by | {{author}} |
| Based on | {{N}} meetings ({{M01}}), {{N}} client documents — see §10 |
| Requirements | {{N}} functional ({{N}} confirmed · {{N}} proposed · {{N}} to confirm) |
| Open questions | {{N}} for the client ({{N}} needed before we start) · {{N}} waiting on our team |

<!-- TEMPLATE NOTE — delete before finishing. Short layout for a Small project. Every fact still carries its tag; keep
the client's own words. A part that does not apply says "None identified." — never delete a heading, never pad.
Tables keep their columns (scripts read them). If the project grows, add sections; never renumber IDs. -->

---

## 1. Summary

{{A few lines: who the client is, the core problem, what we will build, the main risk, where discovery stands.}}

## 2. The client and the people

- **Business:** {{what they do, size, locations, volumes — numbers with tags}}
- **Tools today:** {{paper, spreadsheets, chat groups, software}}
- **Constraints:** {{budget, dates, devices, connectivity, staff skills}}

| Person / role | At the client | Uses the system to | Met in |
|---|---|---|---|
| {{name — Owner (decides)}} | {{…}} | {{…}} | {{M01}} |

## 3. How they work today

### WF-01 — {{workflow name}}
- **Trigger / how often / who:** {{…}}
- **Steps today:**
  1. {{step — who — tool — time}} {{[M01@00:05:10]}}
- **Where it goes wrong:** {{exceptions}} → {{PP-01}}

## 4. Problems and pain points

| ID | Pain point | Who is affected | Impact (time, money, errors, customers) | Source |
|---|---|---|---|---|
| PP-01 | {{…}} | {{…}} | {{in their terms, with a short quote}} | {{[M01@00:12:40]}} |

## 5. Goals and scope

| Goal | Measure | Today | Target | Source |
|---|---|---|---|---|
| {{…}} | {{…}} | {{…}} | {{…}} | {{[M01]}} |

- **In scope:** {{…}}
- **Out of scope:** {{… — including anything the client excluded}}
- **Later / nice to have:** {{…}}

## 6. Solution and proposals

{{What we will build, who uses each part, and how their day changes — one or two paragraphs.}}

| Pain point | How the solution addresses it | Requirements |
|---|---|---|
| {{short name (PP-01)}} | {{…}} | {{FR-001, FR-002}} |

<!-- TEMPLATE NOTE — delete before finishing. Proposals are ours, 'proposed' until the client agrees. Kind: core = our
recommended answer to what they asked for (shapes the solution); optional = an extra they did not ask for.
Status: proposed · accepted · partly accepted (say which part) · rejected · deferred. -->
| ID | Proposal | Kind | Why we suggest it | Source | Status |
|---|---|---|---|---|---|
| P-01 | {{…}} | {{core / optional}} | {{benefit, the pain point it solves}} | {{[RS-01]}} | proposed |

## 7. Functional requirements

Status: `confirmed` (the client said or agreed it) · `proposed` (our suggestion) · `to confirm` (waiting on a question or assumption) · `deferred` · `rejected` · `out of scope`. Priority: Must / Should / Could.

| ID | Requirement | Role | Priority | Source | Status |
|---|---|---|---|---|---|
| FR-001 | {{One testable statement of what the system must do}} | {{…}} | Must | {{[M01@00:08:15]}} | confirmed |

## 8. Rules, data and integrations

### 8.1 Business rules
| ID | Rule | Source | Status |
|---|---|---|---|
| BR-01 | {{…}} | {{[d2-001]}} | confirmed |

### 8.2 Data, reports and notifications
- **Records the system keeps:** {{…, with the fields the client mentioned}}
- **Existing data to bring in:** {{what, how much, in what shape — or "None identified."}}
- **Reports and notifications:** {{what, for whom, how often, by which channel — with tags}}

### 8.3 Integrations and outside services
| System | Purpose | What we learned (capabilities, limits, cost model) | Client's account | Source |
|---|---|---|---|---|

### 8.4 Regulations and compliance
{{Internal. Laws and rules that apply (data protection, tax, sector) and what each means for the system, citing research — or "None identified."}}

### 8.5 Devices, access and other needs
{{Devices and connectivity, languages, who may see what, sensitive data, availability — or "None identified."}}

## 9. Risks, phases, assumptions and decisions

### 9.1 Risks and dependencies
| Risk / dependency | Impact | Mitigation | Owner |
|---|---|---|---|

### 9.2 Delivery phases
| Phase | What is delivered | Depends on |
|---|---|---|
| 1 | {{…}} | |

### 9.3 Assumptions
Only defaults our team approved (`[U-..]`) or the client agreed (`[D-..]`).

| ID | Assumption | Approved by | Status | Source |
|---|---|---|---|---|
| ASM-01 | {{…}} | {{our team, YYYY-MM-DD}} | {{open / confirmed / rejected}} | {{[U-02]}} |

### 9.4 Decisions
| ID | Decision | Agreed by | When | Source |
|---|---|---|---|---|
| D-01 | {{…}} | {{client role}} | {{date}} | {{[M01@00:31:02] / answer to Q-002}} |

## 10. Sources, clarifications and changelog

### 10.1 Meetings
| ID | Date | Topic | Attendees | Digest |
|---|---|---|---|---|
| M01 | {{YYYY-MM-DD}} | {{Kick-off}} | {{names and roles}} | `_work/meetings/M01-….md` |

### 10.2 Client documents
| Doc | File | What it is |
|---|---|---|
| {{d2}} | {{file name}} | {{…}} |

### 10.3 Research
| ID | Source | What it supports | Accessed |
|---|---|---|---|
| RS-01 | {{title — URL}} | {{…}} | {{YYYY-MM-DD}} |

### 10.4 Clarifications from our team
| ID | What was unclear | Answer from our team | Date | Status |
|---|---|---|---|---|
| U-01 | {{…}} | {{…}} | {{YYYY-MM-DD}} | {{answered / sent to client (Q-004) / pending}} |

### 10.5 Changelog
| Version | Date | Change | Triggered by |
|---|---|---|---|
| v0.1 | {{YYYY-MM-DD}} | First draft | {{M01}} |
