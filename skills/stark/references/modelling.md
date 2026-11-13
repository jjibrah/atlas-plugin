# Modelling the system — and the completeness lenses

Work from the register only (not the PRD or the source chunks). The aim is a model complete enough that the spec can be written module by module without new discoveries — and no bigger than the size class calls for.

## 1. Build the model in this order

1. **Platforms** — every separately built surface: apps, portals, dashboards, public API, bots, background workers. For each: who uses it and what it talks to. Record them in the register's Platforms section.
2. **Roles** — one row per role. Decide whether each is a separate identity or a capability layered on another account; the difference shapes authentication.
3. **Modules** — cohesive groups of behaviour (Identity, Orders, Billing, Reporting…).
   - Use the module count for the size class (`sizing-rubric.md`). More modules than that usually means the split is by screen, not by responsibility.
   - Every requirement belongs to exactly **one** module: `M1`, `M2`, … and `X` for cross-cutting non-functional, operational and legal requirements.
   - Each entity is **owned** by one module. Other modules read or change it through that module, never directly.
   - Fill the Module column with one command instead of editing rows by hand. Write a map file (`_work/modules.map`), one line per module:
     ```
     M1: REQ-001-REQ-012, REQ-040
     M2: REQ-013-REQ-031
     X:  REQ-070-REQ-077
     ```
     and run `python3 <skill>/scripts/register.py assign <D> <map file>`, then `register.py lint <D> --strict`.
   - Write `<D>/MODULES.md` from `templates/MODULES.md` (§5 below) — `lint --strict` checks the register's modules against it.
4. **Data model** — entities, key fields, relationships, owning module.
5. **State machines** — one per entity with a real lifecycle (see lens 2).
6. **Use cases per role** — main path and the important alternates.
7. **Integrations** — per third party: data each way, authentication, and what happens when it is down or slow.
8. **Module dependencies** — A depends on B when A needs B's data or behaviour to work. This graph drives the build order.

## 2. Completeness lenses

Run each lens over the model. What a lens finds becomes one of three things — choose deliberately:

- a **`derived` requirement**, only if a stated requirement cannot work without it;
- an **assumption**, if a sensible, cheap-to-change default exists;
- an **open question**, if it is a business decision.

On a Small system most findings are assumptions or nothing at all. A lens is a check for holes, not a licence to add scope.

**Lens 1 — Walk each role through a full cycle.** From first contact to leaving: how do they get an account, sign in, recover access, do their main job, fix a mistake, see history, get notified, and how is their access removed?

**Lens 2 — State machines are closed.** For every stateful entity:
- every state is reachable and every non-final state has a way out;
- failure, cancellation, timeout/expiry, and reversal paths exist (payment fails, approver never responds, user abandons halfway);
- each transition names who or what triggers it, its condition, and its side effects (notifications, money, stock, audit);
- what happens to *dependent* records when the parent changes state.

**Lens 3 — CRUD by role.** For each entity: which role can create, read, update, delete/archive, and with what scope (own / team / branch / all). Empty cells are decisions, not accidents. Most missing admin screens are found here.

**Lens 4 — Every screen has a source.** Each dashboard, report and list: which module produces each number, how fresh it must be, what filters and exports exist, and what the empty state is.

**Lens 5 — Money and counts add up.** Wherever money, credits, stock, seats or quotas move: where is the single record of truth, is it reversible, who reconciles it, how is rounding handled, what happens on a double submit?

**Lens 6 — Time.** Schedules, deadlines, expiries, reminders, retention periods, time zones, billing cycles. Each implies a background job — list them.

**Lens 7 — Abuse and privacy.** For each role: what could they do that they should not? Which data is personal or sensitive, who can see it, and is that access logged?

**Lens 8 — Arrival and departure of data.** Initial data (who creates the first admin, seed catalogues), imports from spreadsheets or legacy systems, exports, account deletion, and offboarding of a whole customer.

**Lens 9 — When things break.** Each integration and job: retry, duplicate delivery, partial failure, and what the user sees meanwhile.

## 3. Contradictions, assumptions, open questions

**Contradictions** — one rule everywhere:

1. Always log it in the register's Contradictions table, quoting both sides.
2. If the precedence rules settle it (newer version, signed-off PRD over notes, target-system document over current practice): record the resolution as a **decision** with its reason. It is *not* an open question. Mention it in the checkpoint summary as "resolved by precedence — say if this is wrong".
3. If precedence does not settle it: it is an **open question**, blocking if a wrong guess would force rework.

**Assumptions** (`ASM-#`) are defaults you chose because the sources are silent and the choice is low-risk. This includes every `practice` requirement taken from a current-practice document. Record them in the register's Assumptions table during modelling.

**Assumption IDs** are `ASM-T1`, `ASM-T2` … (`ASM-##` without the T belongs to Alice).

**Open questions** (`OQ-#`) are decisions that belong to the client or product owner. Each has a recommended default so work continues, and a `Blocking` yes/no. Keep the list short and honest: merge near-duplicates, and drop any question whose answer would not change what gets built. A question only the client can answer is routed through Alice (the skill's *Never guess* rule); the OQ row then names her `Q-###` and has Status `asked (Q-###)`.

When the spec is written, the full text of questions and assumptions moves to its single home (DECISIONS.md, or TECHNICAL.md §11 for a single-file blueprint) and the register sections are replaced by a pointer.

## 5. Modules file and rigour proposal

`MODULES.md` (`templates/MODULES.md`, columns exactly `| Module | Name | Rigour | Paths | Signals | Reason |`) is what Atlas, Jarvis, Sentinel and Spartan read. For each module:

1. **Signals** — check the module against `<plugin>/rigour.md`: money or payments · personal or health data · login, roles or permissions · an outside integration that moves data or money · a state machine with more than ~5 states · a regulation applies (PRD §15) · data migration from an old system · many other modules depend on it. List the ones that apply in plain words, or `none`.
2. **Rigour** — one strong signal (money, health data, auth) → `Critical`. Two or more moderate signals → at least `Standard`. None → the project default (Small → `Light`, Medium/Large → `Standard`). Critical is never a default; it is earned by a signal.
3. **Reason** — one short line the user can agree or disagree with ("handles card payments", "only reads the catalogue").
4. **Paths** — code globs relative to the repository root when the code exists or its layout is decided (`src/billing/**, app/models/invoice.rb`); `?` otherwise. Brownfield: take them from `_work/codebase.md`.
5. No REQ / FR / WP IDs in this table — `atlasctl impact` would treat the whole module as affected.

The level is a **proposal** until the user confirms it (`atlasctl rigour M# <Level> --reason "…"`). Write the spec at the proposed depth; if the user lowers or raises a level, adjust that module's depth before finishing.

## 4. Review (after the spec is written)

Fresh eyes find what the author cannot. Four lens groups:

| Group | Checks |
|---|---|
| Completeness | Lenses 1, 3, 4, 8 — every role and every screen |
| Behaviour | Lenses 2, 5, 6, 9 — state machines, money, time, failures |
| Safety | Lens 7 plus the size-appropriate security list in `quality-attributes.md` |
| Consistency & proportion | Names, IDs and facts agree across core, module files, MODULES.md and overview; nothing is over-built for the size class (`sizing-rubric.md` → Proportion) |

How much review, by size:

- **Small:** one pass over the spec with all four groups in mind. Do not re-read from disk what is already in your context.
- **Medium:** read the spec once; work through the four groups as checklists against it. With subagents: two reviewers (Completeness + Consistency, Behaviour + Safety).
- **Large:** four parallel reviewers, each given **only** the register and the written spec (not your working notes).

Reviewers return a list: *location → problem → suggested fix → severity (blocker / should fix / minor)*. Fix blockers and should-fixes. Anything that needs a client decision becomes an open question. Cutting something that is over-built counts as a fix.
