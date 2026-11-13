# {{Project name}} — Build Plan

> The order of work. The *what* is in [TECHNICAL.md](../design/TECHNICAL.md) and [MODULES.md](../design/MODULES.md); this file is the *when*. Status columns hold the **planned** state: Atlas infers real progress from branches, pull requests and commits (`atlas status`).

| | |
|---|---|
| Version | {{v1.0 — YYYY-MM-DD}} |
| Built on | {{design TECHNICAL vX}} |
| Size | {{N}} work packages in {{N}} phases · {{N}} of {{N}} requirements covered{{, N already built}} |

## How to use this plan (agents and developers)

1. Take the first work package of the current phase whose **Depends on** are all done (`atlas status`).
2. Read only what its **Read** line lists.
3. Work on a branch named after it — `WP-07-short-title` — and start every commit message with the ID (`WP-07: …`). Atlas marks the package *in progress* from the first such branch, commit or pull request, and *done* when it is merged or a commit on the default branch says "WP-07 done" / "closes WP-07". Nobody edits this file to report progress.
4. Make every acceptance criterion it names pass with a test. A package in a Critical module ends in its **review checkpoint** before it counts as done.
5. Never widen a package. If something is missing or wrong in the blueprint, raise it instead of guessing.

## 1. Phases

| Phase | Goal — what can be demonstrated at the end | Work packages | Gate to start | Target | Status |
|---|---|---|---|---|---|
| P0 Walking skeleton | {{sign in, one core action end to end, deploy pipeline}} | {{WP-01–WP-03}} | G3 passed | {{YYYY-MM-DD or blank}} | todo |
| P1 {{name}} | {{…}} | {{WP-04–WP-09}} | {{P0 released}} | | todo |

Gated work (waiting on an open question): {{WP-12 — OQ-3 / none}}

## 2. Work packages

| WP | Title | Phase | Module | REQs | Depends on | Size | Status |
|---|---|---|---|---|---|---|---|
| WP-01 | {{Walking skeleton: sign in and one core action}} | P0 | {{X, M1}} | {{REQ-…}} | — | S | todo |
| WP-02 | {{Payment webhook handler}} + review | P0 | {{M3}} | {{REQ-…}} | WP-01 | S | todo |

Size: XS ≤ 2 hours · S under half a day · M about a day · L 2–3 days (split it if you can). Status (planned): `todo` · `blocked` (on an open question — named in the detail block) · `deferred`. Packages in **Critical** modules are XS/S/M and their title ends in `+ review`.

## 3. Already built

<!-- TEMPLATE NOTE — delete before finishing. Existing code only: requirements the audit proved `done` need no work
package (gate G3 counts them as covered). Evidence: `path:line`, or the audit file. Nothing built → delete this section. -->

| REQ | Evidence |
|---|---|
| {{REQ-001–REQ-004}} | {{audit/m01-identity.md}} |
| {{REQ-017}} | {{`src/orders/service.ts:88`}} |

## 4. Detail — {{current phase}}

#### WP-01 — {{title}}
- **Branch:** `WP-01-{{short-title}}`
- **Read:** {{../design/TECHNICAL.md §1, §3 · ../design/technical/m01-identity.md §2, §5}}
- **Do:**
  1. {{…}}
- **Touches:** {{folders or files — within the module's Paths in MODULES.md}}
- **Acceptance:** {{AC-001–AC-003}}{{, plus any check specific to this package}}
- **Tests:** {{what to add; what must not be called for real}}
- **Review checkpoint:** {{Critical only — who reviews what before it counts as done (security, failure paths, rollback)}}
- **Out of scope:** {{…}}

## 5. Later phases

<!-- TEMPLATE NOTE — delete before finishing. Detail blocks for the current and the next phase only; later phases keep
the table row plus one acceptance line here (`/jarvis plan next` details them later). -->
- **WP-NN** — {{one-line acceptance}} ({{AC-…}})

## 6. Dependencies, risks and parallel rounds

<!-- TEMPLATE NOTE — delete before finishing. Keep only what earns its place; a small plan may delete this whole section. -->

```mermaid
flowchart TD
    %% {{WP_01 --> WP_02 — underscores in node IDs; an arrow means "must be done before"}}
```

| Risk / complex area | Why it is hard | Mitigation | Spike | Needed before |
|---|---|---|---|---|
| {{payment provider integration}} | {{…}} | {{…}} | {{WP-06}} | {{P2}} |

| Round | Lanes (work packages that can run at the same time: no dependency, different files) | Shared resources to assign |
|---|---|---|
| {{P1-R1}} | {{A: WP-04 · B: WP-05, WP-06}} | {{migration numbers, test database}} |

## Changelog
| Version | Date | Change |
|---|---|---|
| v1.0 | {{YYYY-MM-DD}} | Plan created from design {{TECHNICAL vX}} |
