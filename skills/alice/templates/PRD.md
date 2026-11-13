# {{Client}} — {{Project name}} · Product Requirements Document

<!-- legend:start -->
> **Internal — not for the client.** The detailed source of truth for what the client needs and what we will build. Everything here is traceable: `[M02@00:14:32]` = said in meeting M02 at that time · `[d3-002]` = from a client document · `[U-03]` = clarified by our team · `[D-05]` = agreed decision · `[P-04]` = our proposal · `[RS-03]` = research · `[ASM-02]` = assumption approved by our team · `[Q-007]` = waiting on the client. The client-facing version is [PROPOSAL.md](PROPOSAL.md); open questions are in [QUESTIONS.md](QUESTIONS.md).
<!-- legend:end -->

| | |
|---|---|
| Version | {{v0.1 — YYYY-MM-DD}} |
| Status | {{Draft — discovery in progress / Ready for build}} |
| Prepared by | {{author}} |
| Based on | {{N}} meetings ({{M01–M03}}), {{N}} client documents — see §21 |
| Requirements | {{N}} functional ({{N}} confirmed · {{N}} proposed · {{N}} to confirm) |
| Open questions | {{N}} for the client ({{N}} needed before we start) · {{N}} waiting on our team |

<!-- TEMPLATE NOTE — delete before finishing. Be detailed: this is the knowledge base the team builds from and comes
back to. Every factual statement carries a provenance tag. Quote the client's own words where they matter.
Scale to the project: a small client keeps short sections, diagrams only for the one or two workflows that matter, and
writes "None identified yet." for sections that do not apply — never padding. -->

---

## 1. Executive summary

{{Half a page: who the client is, the core problem, what we will build, the main risks, and where discovery stands.}}

## 2. The client and their business

- **Who they are:** {{business, sector, what they sell, to whom}}
- **Size and footprint:** {{staff, branches/locations, customers, volumes — with numbers and tags}}
- **How they make money:** {{revenue model}}
- **Current tools and systems:** {{spreadsheets, paper, WhatsApp groups, existing software — what each is used for}}
- **Constraints they told us about:** {{budget, deadlines, devices, connectivity, staff skills}}

## 3. People

### 3.1 Stakeholders we met
| Name | Role at the client | Interest / influence | Met in |
|---|---|---|---|
| {{…}} | {{Owner — final decision-maker}} | | {{M01, M03}} |

### 3.2 User roles of the system
| Role | Who they are today | What they need from the system | Approx. number |
|---|---|---|---|

## 4. How they work today (current operations)

<!-- TEMPLATE NOTE — delete before finishing. One WF block per real workflow, from meetings and SOPs. Capture who does
each step, with which tool, how long it takes, how often, and where it goes wrong. This is what the solution replaces. -->

### WF-01 — {{workflow name}}
- **Trigger:** {{what starts it}} · **Frequency / volume:** {{…}} · **People:** {{…}}
- **Steps today:**
  1. {{step — who — tool — time}} {{[M01@00:05:10]}}
- **Exceptions:** {{what happens when it goes wrong}}
- **Problems in this workflow:** {{PP-01, PP-03}}

```mermaid
flowchart LR
    %% {{optional: the workflow as it is today}}
```

## 5. Problems and pain points

| ID | Pain point | Who is affected | Impact (time, money, errors, customers) | Evidence | Source |
|---|---|---|---|---|---|
| PP-01 | {{…}} | {{…}} | {{e.g. ~2 hours a day of manual reconciliation}} | {{"short client quote"}} | {{[M01@00:12:40]}} |

## 6. Goals and how success will be measured

| Goal | Measure | Today | Target | Source |
|---|---|---|---|---|
| {{Reduce no-shows}} | {{no-show rate}} | {{~20%}} | {{to be agreed — Q-004}} | {{[M01]}} |

## 7. Scope

- **In scope:** {{…}}
- **Out of scope:** {{… — including anything the client explicitly excluded or that a document marks superseded}}
- **Later phases / nice to have:** {{…}}

## 8. Proposed solution

### 8.1 Overview
{{What we will build, in a few paragraphs: the platforms (web app, mobile, admin portal…), who uses each, and how they fit together.}}

```mermaid
flowchart LR
    %% {{people → parts of the system → outside services}}
```

### 8.2 How each pain point is solved
| Pain point | How the solution addresses it | Requirements |
|---|---|---|
| {{short name (PP-01)}} | {{…}} | {{FR-003, FR-004}} |

### 8.3 How they will work after (future workflows)
{{For each WF that changes: the new steps, who does them, what the system now does automatically.}}

### 8.4 Our proposals
<!-- TEMPLATE NOTE — delete before finishing. Two kinds, both 'proposed' until the client agrees:
CORE — our recommended answer to what the client asked for (e.g. "a phone app for shop orders"); it shapes the solution
and appears in the proposal's main sections as our recommended approach. Requirements the core solution needs but nobody
said (logins, a product list) cite the core proposal.
OPTIONAL — extras the client did not ask for; they appear only under the proposal's "Our suggestions".
Status: proposed · accepted · partly accepted (say which part, with the decision) · rejected · deferred. -->
| ID | Proposal | Kind | Why we suggest it | Source | Status |
|---|---|---|---|---|---|
| P-01 | {{…}} | {{core / optional}} | {{benefit, the pain point it solves}} | {{[RS-02]}} | proposed |

## 9. Functional requirements

Status: `confirmed` (the client said or agreed it) · `proposed` (our suggestion) · `to confirm` (waiting on a question or assumption) · `deferred` · `rejected` · `out of scope`. Priority: Must / Should / Could.

### 9.1 {{Area — e.g. Accounts and access}}
| ID | Requirement | Role | Priority | Source | Status |
|---|---|---|---|---|---|
| FR-001 | {{One testable statement of what the system must do}} | {{…}} | Must | {{[M01@00:08:15]}} | confirmed |

## 10. Business rules

| ID | Rule | Source | Status |
|---|---|---|---|
| BR-01 | {{e.g. A patient may hold at most 2 future appointments}} | {{[d2-001]}} | confirmed |

## 11. Data, reports and dashboards

- **Main records the system keeps:** {{…, with the fields the client mentioned}}
- **Existing data to bring in:** {{spreadsheets, old systems — volume, format, quality}}
- **Reports and dashboards:**

| Report / dashboard | For whom | Shows | How often | Source |
|---|---|---|---|---|

## 12. Notifications and communication

| Trigger | Channel (SMS, email, WhatsApp, in-app) | To whom | Source |
|---|---|---|---|

## 13. Integrations

| System | Purpose | What we learned (capabilities, limits, cost model) | Client's account / access | Source |
|---|---|---|---|---|
| {{e.g. payment provider}} | | | {{they already have one / to set up}} | {{[M02] [RS-04]}} |

## 14. Non-functional requirements

- **Users and volume:** {{…}}
- **Devices and connectivity:** {{phones, desktops, poor network, offline needs}}
- **Languages:** {{…}}
- **Availability and support:** {{business hours, who supports it}}
- **Security and privacy:** {{who may see what; sensitive data}}
- **Performance:** {{…}}

## 15. Regulations and compliance

<!-- TEMPLATE NOTE — delete before finishing. Internal only. Laws and rules that apply to this business in this country:
data protection, tax/e-invoicing, sector rules. Cite research sources; flag anything that needs legal advice. -->
| Area | Rule / law | What it means for the system | Source |
|---|---|---|---|

## 16. Technical notes and recommendations

{{Our early technical view: likely architecture and stack (or constraints on it), the hardest parts, integration risks, data migration effort, and anything an engineer should know before estimating.}}

## 17. Risks and dependencies

| Risk / dependency | Likelihood / impact | Mitigation | Owner |
|---|---|---|---|

## 18. Delivery phases

| Phase | What is delivered | Why in this order | Depends on |
|---|---|---|---|
| 1 | {{…}} | | |

## 19. Assumptions

Only defaults our team approved (`[U-..]`) or the client agreed (`[D-..]`). ALICE never assumes on her own.

| ID | Assumption | Approved by | Status | Source |
|---|---|---|---|---|
| ASM-01 | {{…}} | {{our team, YYYY-MM-DD}} | {{open / confirmed / rejected}} | {{[U-02]}} |

## 20. Decisions

| ID | Decision | Agreed by | When | Source |
|---|---|---|---|---|
| D-01 | | {{client role}} | {{date}} | {{[M02@00:31:02] / answer to Q-002}} |

Open questions are not repeated here — see [QUESTIONS.md](QUESTIONS.md).

## 21. Sources

### 21.1 Meetings
| ID | Date | Topic | Attendees | Digest |
|---|---|---|---|---|
| M01 | {{YYYY-MM-DD}} | {{Kick-off}} | {{names and roles}} | `_work/meetings/M01-….md` |

### 21.2 Client documents
| Doc | File | What it is |
|---|---|---|
| {{d2}} | {{Front-Desk-SOP.docx}} | {{Current front-desk procedure}} |

### 21.3 Research
| ID | Source | What it supports | Accessed |
|---|---|---|---|
| RS-01 | {{title — URL}} | {{…}} | {{YYYY-MM-DD}} |

### 21.4 Clarifications from our team
Things ALICE did not understand and asked the user about. `sent to client` = it became a client question.

| ID | What was unclear | Answer from our team | Date | Status |
|---|---|---|---|---|
| U-01 | {{…}} | {{…}} | {{YYYY-MM-DD}} | {{answered / sent to client (Q-004) / pending}} |

## 22. Glossary

| Term | Meaning (in the client's usage) |
|---|---|

## 23. Changelog

| Version | Date | Change | Triggered by |
|---|---|---|---|
| v0.1 | {{YYYY-MM-DD}} | First draft | {{M01}} |
