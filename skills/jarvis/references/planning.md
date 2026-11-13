# Planning — phases and work packages

The plan turns the design into an ordered list of jobs that an agent or developer can pick up one at a time.

Output: `<P>/plan/PLAN.md` from `templates/PLAN.md`, for every size of system — `atlasctl` reads its two tables (CONTRACT §3), so their columns are fixed. (Parallel lanes and agent briefs: `briefs.md`, read only when asked for a brief.)

Inputs, all read-only: `<P>/design/TECHNICAL.md` (+ `technical/`), `<P>/design/MODULES.md` (modules, rigour, paths), the register `<P>/design/_work/requirements.md`, `<P>/design/DECISIONS.md`, and — when it exists — the audit in `<P>/plan/`. Rigour per module: the confirmed level wins over the proposed one (`atlasctl status --json` → `modules[].rigour`, `confirmed`).

## 1. Phases

- **Each phase ends in something a person can see working** — a demo sentence, not a layer ("a customer can place and pay for an order", not "backend models done").
- **Phase 0 is the walking skeleton**: the thinnest end-to-end path through every platform — sign in, one core action, deployment, one test of each kind. It proves the architecture before volume is built on it.
- **Build in vertical slices**: a slice carries one capability through data, logic, API and screen. Avoid "all the tables, then all the APIs, then all the screens".
- **Order by dependency, then by risk**: what others depend on goes first; among equals, the riskiest goes first. A risky integration gets a short **spike** work package in the phase *before* the one that needs it.
- **Respect the client's roadmap.** PRD §18 *Delivery phases* (Alice) and the proposal name stages the client already agreed to: map your phases onto them and keep their names. Phase IDs are `P0`, `P1`, … (never reuse one).
- **Target dates** (optional `Target` column, `YYYY-MM-DD`): only dates the user or the PRD gives, or that the user approves when you propose them. Atlas flags a phase that passes its target with work open. Never invent a deadline.
- **Gates**: state what must be true to start the phase (`G3 passed` for P0; `P0 released` or a client decision for later ones). Work waiting on an open question gets Status `blocked` and its detail block names the OQ.
- Small systems usually need 2–3 phases; do not manufacture more.

## 2. Work packages

A work package (`WP-01`, `WP-02`, …) is one unit of work for one agent session.

| Rule | Why |
|---|---|
| Finishable in roughly a day or less | Fits one session with room for tests |
| Sized by the module's **rigour** (below) | Risky work is reviewed in small pieces |
| One module, or one thin slice across a few | Limits the context the agent must load |
| At most ~15 requirements | Reviewable; acceptance stays checkable |
| Has acceptance criteria that can be tested on their own | "Done" is a fact, not an opinion |
| Lists what it depends on | The verify script checks the order and finds cycles |
| Names the area of the codebase it touches | Parallel work can be planned without overlap |

The work-package table — these columns, in this order (extra columns may follow):

```markdown
| WP | Title | Phase | Module | REQs | Depends on | Size | Status |
|---|---|---|---|---|---|---|---|
| WP-07 | Order checkout and payment intent | P2 | M4 | REQ-061–REQ-068, REQ-112 | WP-03, WP-05 | M | todo |
| WP-08 | Card payment webhook + review | P2 | M5 | REQ-070–REQ-073 | WP-07 | S | todo |
```

- **WP** — the ID alone (`WP-07`, two digits at least). Permanent: never renumber or reuse; a dropped package becomes `deferred`.
- **Module** — `M#` IDs from MODULES.md; more than one (`X, M5`) for a slice such as the walking skeleton.
- **REQs** — every REQ the package delivers, in this column (ranges allowed). Gate G3 reads only this column, not the detail blocks.
- **Size**: XS (≤ 2 hours), S (under half a day), M (about a day), L (2–3 days — split it if you can).
- **Status** is the **planned** state only: `todo` · `blocked` (gated on an OQ) · `deferred`. Jarvis never changes it to reflect progress; Atlas records progress as events from branches, commits, pull requests and CI (`atlasctl wp …` for corrections).
- **Every live requirement appears in a work package's REQs column.** Brownfield: requirements the audit proved `done` go in one baseline row `| WP-00 | Baseline — built before this plan (audit review in AUDIT.md) | P0 | … | <REQs> | — | XS | done |` so the coverage check and gate G3 see them; the gaps get normal packages.

### Granularity follows rigour

| Module rigour | Work packages |
|---|---|
| Light | 1–2 for the module |
| Standard | Normal packages, S/M |
| Critical | Small packages (XS/S/M), each ending in a **review checkpoint** — put `+ review` at the end of the title and say in the detail block what is reviewed (security, failure and rollback paths, audit trail) and by whom. Gate G3 checks both the size and the word "review". |

### Detail level: rolling wave

Write the detail block only for the **current and next phase**. Later phases keep the table row plus one line. Detail them with `/jarvis plan next` when the phase before is nearly done — by then decisions have been made and the detail will be right.

```markdown
#### WP-07 — Order checkout and payment intent
- **Branch:** `WP-07-order-checkout`
- **Read:** ../design/TECHNICAL.md §1, §3 · ../design/technical/m04-orders.md §2, §5
- **Do:** 1. … 2. … 3. …
- **Touches:** `backend/orders/`, `frontend/src/checkout/`, new migration
- **Acceptance:** AC-031–AC-034 (technical/m04-orders.md §12), plus: duplicate submit with the same idempotency key creates one order (REQ-112).
- **Tests:** unit for totals and state transitions; integration for the checkout endpoint; no live payment calls.
- **Out of scope:** refunds (WP-11)
```

**Acceptance criteria live in the design, not the plan.** Stark's spec holds them as `AC-###` rows citing their REQ. A work package names the criteria it must satisfy and adds only checks specific to that package. A requirement with no criterion is a design gap — send it back to Stark (`/stark update`), do not write one here.

**Branch names.** Every detail block and brief gives the branch `WP-07-short-title` (lowercase words after the ID). Atlas matches commits and pull requests to work packages by the `WP-##` in branch names and commit messages.

## 3. Keeping the plan alive (re-plan)

- Progress comes from Atlas: `atlasctl status --json` → `wps[]` (`state`: todo / in-progress / done / deferred / blocked, `confidence`), `phases[]`, `current_phase`. Never re-plan a package Atlas shows as done; never edit Status to mirror progress.
- When an open question is answered (Stark updates DECISIONS.md), change the gated packages from `blocked` to `todo` and adjust their detail.
- When the design changes (Stark update or a change request), only the affected packages change — `atlasctl impact <FR-…|REQ-…>` lists them. New requirements get new packages. Never silently widen a finished one.
- Add a changelog row and bump the plan version on every re-plan.
