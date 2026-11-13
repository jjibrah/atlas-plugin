# Sizing rubric

Size decides how much gets written and how deep the design goes. Atlas already holds a size class from project creation (`atlasctl status --json` → project, or `<P>/atlas.json`); score it again here from the register, and if your result differs, tell the user and let them decide (`atlas.json` is changed only through Atlas). Size sets the project default; **rigour** (rigour.md) then raises or lowers individual modules. Getting it wrong in the *upward* direction is the common failure: a small system buried under a large system's documentation. Score each factor 0–2 from the register, add them up, and classify.

| Factor | 0 | 1 | 2 |
|---|---|---|---|
| **User roles** | 1–3 | 4–6 | 7+, or organisations as tenants |
| **Platforms / surfaces** | 1 (one web app, even if it has an admin area) | 2–3 separately built surfaces | 4+ (mobile apps, portals, public API, bots) |
| **Core entities** | up to 10 | 11–25 | 26+ |
| **Stateful workflows** (lifecycles with more than a simple status) | 0–2 | 3–5 | 6+, or multi-level approvals |
| **External integrations** | 0–1 | 2–3 | 4+, or any real-time two-way sync |
| **Money** | none | records amounts or invoices | takes payments, pays out, wallets, ledgers |
| **Sensitive data / compliance** | ordinary contact details | personal records kept as a side effect (notes, dates of birth, an allergy field) | regulated data is the product's core (medical records, bank accounts, government ID), or a named compliance regime applies |
| **Expected scale** | one organisation, up to a few thousand users | tens of thousands of users, or several organisations | 50k+ users, high concurrency, or a stated availability target |
| **Real-time / heavy processing** | none beyond scheduled reminders | background jobs, notifications at volume, imports | live tracking, chat, streaming, heavy analytics, offline sync |

## Classification

| Total | Size | Typical examples |
|---|---|---|
| 0–5 | **Small** | Clinic or salon booking, internal tool, simple CRUD admin, site with a CMS |
| 6–11 | **Medium** | SaaS with a few roles, online store, HR/leave system, school management |
| 12–18 | **Large** | Marketplace with payments, lending, logistics platform, hospital system, multi-tenant ERP |

**On a boundary, choose the smaller class.** A score of 6 or 12 that got there on factors sitting exactly on a threshold is the smaller class. It is far cheaper to add depth to one area later than to maintain documents nobody needed.

**Override (rare):** bump one class only when a single factor is the product's central risk at real scale — moving customers' money, or holding regulated records for many people. A booking system that stores an allergy note does not qualify. State the override and why.

Record it:

```markdown
## Sizing breakdown
| Factor | Score | Evidence |
|---|---|---|
| User roles | 1 | Patient, Receptionist, Dentist, Manager (REQ-002–REQ-005) |
| … | | |
| **Total** | **4** | **Small** |
Overrides: none
```

## What each size means

| | Small | Medium | Large |
|---|---|---|---|
| Architecture | One deployable app, one database | Modular monolith with clear module boundaries; background jobs where needed | Modular monolith, or services split *only* where scale, team or isolation demands it — justify every split |
| Modules | 3–6 | 6–10 | 10–16 |
| Files | `MODULES.md`, `OVERVIEW.md`, `TECHNICAL.md` — decisions inside it | + `DECISIONS.md` | + `technical/<module>.md`, `technical/x-cross-cutting.md` |
| Non-functional depth | Essentials checklist | Essentials + targets | Full treatment (threat model, capacity, failure modes) — and every Critical module gets threat notes and failure/rollback behaviour whatever the size |
| Decision records | A table of choices with reasons | Short records for the significant ones | Full records with alternatives |
| Diagrams | Context, data model, key state machines, build order | + components, key sequence diagrams | + deployment, sequence diagrams for every critical flow |
| Review | One self-review pass | One read, all four lens groups | Parallel reviewers |
| Overview length | 3–5 pages | 5–8 pages | 8–12 pages |

An existing codebase (brownfield) does not change the size class; the architecture row becomes "document and extend what exists".

## Choose the file layout before writing

Decide this once, at the start of the spec step, from counts you already have — not after the file has grown:

| Situation | Layout |
|---|---|
| Up to ~60 requirements **and** up to 6 modules | **Single file**: everything in `TECHNICAL.md` |
| More than that, or size class Large | **Core + module files**: `TECHNICAL.md` core, one `technical/<module>.md` per module, `technical/x-cross-cutting.md` |

Medium systems use whichever the counts say. A Critical module in a single-file layout may still get its own `technical/mNN-<name>.md` if its depth would crowd the core. Record the choice in STATE.md.

## Proportion

The blueprint should be proportionate to the substance of the sources. As a guide for everything delivered (not counting `_work/`):

| Size | Total | If you are far above it |
|---|---|---|
| Small | 25–50 KB | You are inventing detail the sources do not support. |
| Medium | 60–130 KB | Check for repeated content between core, modules, and plan. |
| Large | as needed | Keep each file within its budget. |

Signs of over-building to cut on sight: derived requirements above ~15% of stated ones; more than ~8 open questions on a small system; environments, monitoring, or audit trails nobody asked for on a system run by a handful of staff; a multi-step design grown from one sentence in the source (ask a question instead).

## File size budgets

Agents load these files into limited context, so size is a correctness issue. The verify script warns when a budget is exceeded.

| File | Budget | If it grows past the budget |
|---|---|---|
| `TECHNICAL.md`, single-file layout | ≤ 60 KB | Switch to core + module files. |
| `TECHNICAL.md`, core | ≤ 40 KB | Keep only what **every** implementer needs; move the rest to module files, `x-cross-cutting.md`, `DECISIONS.md`. |
| `technical/<module>.md` | ≤ 35 KB | Split the module, or move long reference tables to an appendix file linked from it. |
| `OVERVIEW.md` | ≤ 30 KB | Cut detail; it belongs in the technical docs. |
| Any table cell | ≤ ~600 characters | Put the explanation in a note below the table. |
