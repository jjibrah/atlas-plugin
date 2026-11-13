# Extraction — building the requirements register

Goal: after this step nobody opens the PRD or the design sources again. Everything the build needs is in `<D>/_work/requirements.md`, each technical requirement (`REQ-###`) traceable to the PRD row (`FR-###`, `BR-##`) or design-source chunk it came from.

**Start from the PRD.** `python3 <skill>/scripts/register.py seed <D>` adds one numbered row per in-scope FR and BR that no REQ cites yet (to-confirm rows get Status `to confirm`). Then work through the seeded rows: split compound ones into atomic REQs (new rows with ID `NEW`, citing the same FR), set the category, and add what the PRD's other sections (§3–§4, §11–§16) and any design sources imply. Alice's FRs are already testable statements, so most map one-to-one; do not split for the sake of it.

## What counts as a requirement

An **atomic** statement of something the system must do, hold, enforce, or be. Split compound sentences:

> "Admins can approve or reject vendor applications and the vendor is emailed the result."

- Admin can approve a vendor application.
- Admin can reject a vendor application.
- Vendor receives an email with the approval or rejection outcome.

Copy numbers, limits, deadlines, formulas, and legal wording **exactly**. Never round or paraphrase them.

## Register columns

```markdown
| ID | Cat | Type | Requirement | Source | Priority | Module | Status |
|---|---|---|---|---|---|---|---|
| NEW | RULE | stated | A member may hold at most 3 active bookings. | FR-014, BR-03 | Must | | |
```

| Column | Rules |
|---|---|
| **ID** | Write `NEW`. The script assigns `REQ-###` (`register.py number`). Never number by hand, never renumber, never reuse an ID. |
| **Cat** | One of the categories below. |
| **Type** | `stated` — the PRD (or a design source) says it. · `practice` — only PRD §4 *current operations* or a current-practice design source says it and no FR covers it; recorded, and listed for confirmation as an assumption (`ASM-T#`) — and if it changes what the client gets, a question for Alice. · `derived` — written nowhere, but a stated requirement cannot work without it ("password reset" when login is required). Keep `derived` rare: an idea, an improvement, or a design grown from one sentence is an open question, not a requirement. **Never invent a requirement.** |
| **Requirement** | One atomic, testable sentence. Include the source's own identifier when it has one (see *Source identifiers*). |
| **Source** | **The upstream ID — mandatory.** Functional rows (FUNC, RULE, DATA, UI, NOTIF, INT) cite their `FR-###` and/or `BR-##`. Non-functional rows (SEC, PERF, OPS, UX) cite an FR, or `PRD §14` / `PRD §15`, or a design-source chunk `[d1-007]`. A `derived` row writes `derived from REQ-### (FR-###)`. Several sources: separate with `;`. Never copy Alice's meeting or chunk references. |
| **Priority** | The FR's priority (Must/Should/Could). Blank if unstated. |
| **Module** | Leave blank during extraction; filled in the modelling step. |
| **Status** | Blank normally. `to confirm (OQ-#)` when the FR is `to confirm` or the REQ rests on an open question. `claimed` if a source *says* it is already built — only Jarvis's audit can prove it. Never `built`/`done`: Stark does not audit. |

## Categories

| Code | Category | Examples |
|---|---|---|
| `FUNC` | Functional behaviour | create order, approve leave, export report |
| `RULE` | Business rule, validation, calculation | max 3 active loans, VAT 16%, cut-off 5pm |
| `DATA` | Data stored, retained, migrated | keep invoices 7 years, import the customer spreadsheet |
| `UI` | Screen, dashboard, report | admin dashboard shows daily revenue |
| `NOTIF` | Notification or message | SMS when order ships |
| `INT` | Integration with an external system | mobile-money payments, SSO, SMS gateway |
| `SEC` | Security, privacy, access control | only finance sees salaries, 2FA for admins |
| `PERF` | Performance, scale, availability | 10k concurrent users, page under 2s |
| `OPS` | Operations, deployment, support, legal | daily backups, audit log, hosting region |
| `UX` | Usability, accessibility, localisation | two languages, works offline |

## Source identifiers — keep them

The PRD's IDs (`FR-###`, `BR-##`, Alice's decisions `D-##` and assumptions `ASM-##`, pain points `PP-##`) are how the client and the team already speak. Cite them; never renumber or redefine them. A design source's own identifiers (an API's endpoint codes, a legacy table name) go in the requirement text and the **Source ID map** section. PRD §18 phase names are reused by Jarvis — note them.

## Also capture (the other register sections)

`register.py init` creates the register with every section heading already in place and in order — keep those heading names; the scripts read them. Document roles and the sizing breakdown sit above the requirements table; the rest below. The Platforms, Modules and Assumptions sections are filled in the modelling step.

1. **Document roles & precedence** — PRD version and sign-off; what each design source is; which wins on conflict (`intake.md` §3).
2. **Actors & roles** — every human role and external system, with responsibilities.
3. **Entities** — business objects, the attributes mentioned, relationships. Normalise synonyms: if the sources say *client*, *customer* and *account holder* for one thing, pick one name and record the others in the Glossary.
4. **States & transitions** — any word implying a lifecycle (*pending, approved, draft, submitted, expired, cancelled, escalated, overdue, suspended*). Record what triggers each transition and any condition.
5. **Workflows (from SOPs)** — real step-by-step processes, approval chains, hand-offs, and exceptions ("if the manager is absent…").
6. **Dashboards & reports** — what each shows, for whom, filters, exports, freshness.
7. **Notifications** — trigger, channel, recipient.
8. **Integrations** — system, direction, data, frequency, stated failure behaviour.
9. **Non-functional expectations** — even vague ones ("fast", "secure"), verbatim. They are quantified later.
10. **Constraints** — mandated technology, budget, deadlines, hosting, regulation.
11. **Existing data & migration** — spreadsheets, legacy systems, or manual records that must be imported or run in parallel.
12. **Glossary** — business terms, acronyms, and the synonyms you normalised.
13. **Contradictions** — two places that disagree. Always log them here, quoting both with their IDs (FR, BR, chunk). Whether one becomes a decision or an open question is settled in the modelling step (`modelling.md` §3).
14. **Open questions** — what a developer must know that the PRD does not say. Use the triage format below. A question only the client can answer is also handed to Alice (see the skill's *Never guess* rule).
15. **Out of scope** — anything explicitly excluded or deferred.
16. **Source ID map** — the source's own identifiers → REQ IDs.

### Open question format

```markdown
| ID | Question | Affects | Blocking | Recommended default | Owner | Status |
|---|---|---|---|---|---|---|
| OQ-1 | What happens to a paid order when the payment is later reversed? | Orders, Payments | yes | Cancel the order and restock | Client via Alice | open |
```

- **Blocking** (`yes` / `no`): `yes` when a wrong guess would force rework of the data model, a state machine, an integration, or the architecture — name what it affects. Otherwise `no`: configuration and data the client supplies later, and behaviour details where the default is safe and cheap to change. Gate G2 fails while a blocking question is open (Standard/Critical projects).
- **Status**: `open` · `asked (Q-###)` once Alice has put it to the client · `answered` / `resolved`.
- **Recommended default**: what you will assume if nobody answers. Every question needs one, so work is never stuck.
- Ask only what changes the design. "What colour should the button be" is not an open question.

## Working method

- **Every in-scope FR must be cited by at least one REQ** (lint fails otherwise — the same check as gate G2). Business rules should be cited too.
- **Design sources go chunk by chunk** in the order INDEX.md lists them; append rows (ID = `NEW`) after each chunk. Every chunk is accounted for: one with no requirements is recorded in `_work/ledger.md` with the reason (`register.py ledger <D>`).
- **Tables are dense.** A pricing table, permission grid, or status table usually yields one requirement per row or cell. Do not summarise a table into a single requirement.
- **Respect the PRD's statuses.** `out of scope`, `rejected` and `deferred` FRs produce no live REQ; list them under Out of scope. In a design source, *superseded*, *deprecated* or struck-through text is not a current requirement.
- Duplicates across documents: one row, several sources.
- When done: `python3 <skill>/scripts/register.py number <D>`, then `python3 <skill>/scripts/verify.py <D> --stage extract`, and fix what it reports.

For large source sets, see `parallel-extraction.md`.
