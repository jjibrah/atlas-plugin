# Planning — phases and work packages

Read at the Plan step. Start from the seed (`plan_seed.py`): it has grouped the REQs by module, split them to the size each module's rigour allows and chained them by module dependency. What it cannot do — and you must — is merge, order, name and phase.

## 1. Phases

- **Each phase ends in something a person can see working** — a demo sentence, not a layer ("a customer can place and pay for an order", not "backend models done").
- **P0 is the walking skeleton:** the thinnest end-to-end path through every platform — sign in, one core action, deployment, one test of each kind.
- **Vertical slices:** one capability through data, logic, API and screen. Merge the seed's per-module rows where a capability crosses modules; never "all the tables, then all the APIs".
- **Order by dependency, then by risk.** What others depend on goes first; among equals the riskiest goes first. A risky integration gets a short **spike** package in the phase before the one that needs it.
- **Keep the client's phase names** where delivery phases were already agreed (ask the user if the design does not carry them). Phase IDs are `P0`, `P1` … — never reused.
- **Target dates** (`YYYY-MM-DD`) only when the user or the PRD gives them or the user approves your proposal. Atlas flags a phase past its target. Never invent a deadline.
- **Gate to start:** `G3 passed` for P0; `P0 released` or a client decision for later phases.
- Small systems need two or three phases; do not manufacture more.

```markdown
| Phase | Goal — what can be demonstrated at the end | Work packages | Gate to start | Target | Status |
|---|---|---|---|---|---|
| P0 Walking skeleton | A patient signs in and books one slot on the deployed app | WP-01–WP-03 | G3 passed | | todo |
```

## 2. Work packages

One unit of work for one agent session: about a day at most, one module or one thin slice across a few, at most ~15 requirements, acceptance testable on its own.

```markdown
| WP | Title | Phase | Module | REQs | Depends on | Size | Status |
|---|---|---|---|---|---|---|---|
| WP-07 | Order checkout and payment intent | P2 | M4 | REQ-061–REQ-068, REQ-112 | WP-03, WP-05 | M | todo |
| WP-08 | Card payment webhook + review | P2 | M5 | REQ-070–REQ-073 | WP-07 | S | todo |
```

These columns, in this order (verify and Atlas read them; extra columns may follow):

- **WP** — the ID alone, two digits at least. Permanent: never renumber or reuse; a dropped package becomes `deferred`.
- **Module** — `M#` IDs from MODULES.md; several (`X, M1`) for a slice such as the walking skeleton.
- **REQs** — every REQ the package delivers (ranges allowed). Gate G3 reads only this column, never the detail blocks. Every live REQ is in exactly the packages that deliver it — or in the *Already built* table.
- **Depends on** — real `WP-##` IDs, no cycles, nothing in a later phase.
- **Size** — `XS` ≤ 2 hours · `S` under half a day · `M` about a day · `L` 2–3 days (split it if you can).
- **Status** — the planned state only: `todo` · `blocked` (gated on an open question; the detail block names the `OQ-#`) · `deferred`. Never `in-progress` or `done`.

| Module rigour | Granularity (verify and gate G3 check the Critical row) |
|---|---|
| Light | 1–2 packages for the module |
| Standard | normal packages, S/M — about six REQs each |
| Critical | small packages, **XS/S/M**, about three REQs each, title ends **`+ review`**; the detail block says what is reviewed (security, failure and rollback paths, audit trail) and by whom |

**Already built** (existing code, after the audit): requirements the audit proved `done` get no work package. List them in PLAN.md in a table `| REQ | Evidence |` — a REQ or range per row, evidence as `path:line` or the audit file. Gate G3 counts them as covered; `partial`, `missing` and settled `deviates` requirements get normal packages.

## 3. Detail blocks — rolling wave

Detail blocks only for the **current and the next phase**; later phases keep the table row plus one acceptance line. PLAN.md stays under 40 KB.

```markdown
#### WP-07 — Order checkout and payment intent
- **Branch:** `WP-07-order-checkout`
- **Read:** ../design/TECHNICAL.md §1, §3 · ../design/technical/m04-orders.md §2, §5
- **Do:** 1. … 2. … 3. …
- **Touches:** `backend/orders/`, `frontend/src/checkout/`, new migration
- **Acceptance:** AC-031–AC-034, plus: a duplicate submit with the same idempotency key creates one order (REQ-112).
- **Tests:** unit for totals and transitions; integration for the checkout endpoint; no live payment calls.
- **Out of scope:** refunds (WP-11)
```

- **Acceptance criteria live in the design.** A package names the `AC-###` it must satisfy (`atlas pack jarvis --module M#` lists them per REQ) and adds only checks specific to itself. A REQ with no criterion is a design gap: `atlas note --to stark "REQ-045 has no acceptance criterion" --from jarvis` — do not write one here.
- **Branch names:** `WP-07-short-title`, lowercase. Atlas matches branches, pull requests and commits to work packages by the `WP-##` in their names — that is how progress is known.
- A Critical package adds **Review checkpoint:** who reviews what before it counts as done.
