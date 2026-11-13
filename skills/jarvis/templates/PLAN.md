# {{Project name}} — Build Plan

> The order of work. The *what* is in [TECHNICAL.md](../design/TECHNICAL.md) and [MODULES.md](../design/MODULES.md); this file is the *when*. Real progress is recorded by Atlas from commits, pull requests and CI (`atlasctl status`, `views/STATUS.md`) — the Status column below is the **planned** state and is not edited as work happens.

**Plan version:** {{v1.0 — YYYY-MM-DD}} · **Work packages:** {{N}} in {{N}} phases · **Requirements covered:** {{N}} of {{N}}

## How to use this plan (agents and developers)

1. Take the first work package of the current phase whose **Depends on** are all done (ask, or check `atlasctl status`).
2. Read only what its **Read** line lists.
3. Work on a branch named after it — `WP-07-short-title` — and start every commit message with the ID (`WP-07: …`). That is how Atlas sees progress.
4. Make every acceptance criterion it names pass with a test. A package in a Critical module ends in its **review checkpoint** before it counts as done.
5. Never widen a package. If something is missing or wrong in the blueprint, raise it instead of guessing.

## 1. Phases

| Phase | Goal — what can be demonstrated at the end | Work packages | Gate to start | Target | Status |
|---|---|---|---|---|---|
| P0 Walking skeleton | {{sign in, one core action end to end, deploy pipeline}} | WP-01–WP-03 | G3 passed | {{YYYY-MM-DD or blank}} | todo |
| P1 {{name}} | {{…}} | {{WP-04–WP-09}} | {{P0 released}} | | todo |

Gated work (waiting on an open question): {{WP-12 — OQ-3 / none}}

## 2. Dependency graph

```mermaid
flowchart TD
    %% {{work packages (WP_01 --> WP_02) — underscores in node IDs; an arrow means "must be done before"}}
```

## 3. Risks & spikes

| Risk / complex area | Why it is hard | Mitigation | Spike | Needed before |
|---|---|---|---|---|
| {{payment provider integration}} | {{…}} | {{…}} | {{WP-06}} | {{P2}} |

## 4. Work packages

| WP | Title | Phase | Module | REQs | Depends on | Size | Status |
|---|---|---|---|---|---|---|---|
| WP-01 | {{Walking skeleton: sign in and one core action}} | P0 | {{X, M1}} | {{REQ-…}} | — | S | todo |
| WP-02 | {{Payment webhook handler + review}} | P0 | {{M3}} | {{REQ-…}} | WP-01 | M | todo |

Size: XS ≤ 2 hours · S under half a day · M about a day · L 2–3 days (split if you can). Status (planned): `todo` · `blocked` (gated on an open question — say which in the detail block) · `deferred`. Work packages in **Critical** modules are XS/S/M and their title ends in `+ review`.

### 4.1 Detail — {{current phase}}

#### WP-01 — {{title}}
- **Branch:** `WP-01-{{short-title}}`
- **Read:** {{../design/TECHNICAL.md §1, §3 · ../design/technical/m01-identity.md §2, §5}}
- **Do:**
  1. {{…}}
- **Touches:** {{folders or files — the module's Paths in MODULES.md}}
- **Acceptance:** {{AC-001–AC-003}}{{, plus any check specific to this package}}
- **Tests:** {{what to add; what must not be called for real}}
- **Review checkpoint:** {{Critical modules only — who reviews what before it counts as done (security, failure paths, rollback)}}
- **Out of scope:** {{…}}

### 4.2 Detail — {{next phase}}

### 4.3 Later phases
<!-- TEMPLATE NOTE — delete before finishing. Rolling wave: later phases keep only the table row plus one
acceptance line each. Detail them with `/jarvis plan next` when the phase before is nearly done. -->
- **WP-NN** — {{one-line acceptance}} ({{AC-…}})

## 5. Parallel rounds

Work packages that can run at the same time (no dependency between them, different files):

| Round | Lanes (work packages) | Shared resources to assign |
|---|---|---|
| {{P1-R1}} | {{A: WP-04 · B: WP-05, WP-06}} | {{migration numbers, test database}} |

## Changelog
| Date | Change |
|---|---|
| {{YYYY-MM-DD}} | Plan created from design {{TECHNICAL vX}} |
