# Model — modules, rigour, completeness, architecture, review

Read at the Model step. Work from the register only: a model complete enough to write the spec module by module, and no bigger than the size calls for.

## 1. Build the model

1. **Platforms** — every separately built surface: who uses it, what it talks to.
2. **Roles** — each its own identity, or a capability on another account?
3. **Modules** — cohesive groups of behaviour, split by responsibility, not by screen; count per the size class.
   - Every requirement belongs to exactly one module: `M1`, `M2` … or `X` for cross-cutting non-functional, operational and legal rows.
   - Every entity is owned by one module; others reach it through that module.
   - Assign by script, not by hand: write `_work/modules.map`, one line per module (`M1: REQ-001-REQ-012, REQ-040` · `X: REQ-070-REQ-077`), then `register.py assign <D> _work/modules.map`.
4. **Data model**, **state machines** (one per entity with a real lifecycle), **use cases per role** (main path, important alternates), **integrations** (data each way, authentication, behaviour when the other side is down).
5. **Module dependencies** — A depends on B when A needs B's data or behaviour. They go in TECHNICAL.md's module table (`Depends on` column); the plan seed orders work from it.

## 2. MODULES.md and the rigour proposal

Write `<D>/MODULES.md` from `templates/MODULES.md` — one table, columns exactly `| Module | Name | Rigour | Paths | Signals | Reason |`:

- **Signals** — the ones in SKILL.md that apply, in plain words, or `none`.
- **Rigour** — `Light`, `Standard` or `Critical` by the rule in SKILL.md; a proposal until the user confirms it.
- **Reason** — one plain line the user can agree or disagree with ("handles card payments").
- **Paths** — code globs relative to the repository root (`src/billing/**, app/models/invoice.rb`), or `?` until known; Atlas maps commits to modules with them.
- No REQ / FR / AC / WP IDs anywhere in this file — `atlas impact` would treat the whole module as affected.

Then `register.py lint <D> --strict`: every REQ has a module, and every module value is in MODULES.md (or is `X`).

## 3. Completeness lenses

A finding becomes exactly one of: a **derived requirement** (only if a stated requirement cannot work without it), an **assumption** (a sensible, cheap-to-change default), or an **open question** (a business decision). On a Small system most are assumptions or nothing — a lens finds holes; it is no licence to add scope.

1. **Role life cycle** — getting an account, signing in, recovering access, the main job, fixing a mistake, history, notifications, losing access.
2. **State machines are closed** — every state reachable and every non-final state has a way out; failure, cancellation, timeout and reversal paths; each transition has a trigger, guard and side effects; dependent records follow the parent.
3. **CRUD by role** — per entity, who creates, reads, updates, archives, with what scope (own / team / all). Empty cells are decisions.
4. **Every screen has a source** — which module produces each number, how fresh, filters, exports, the empty state.
5. **Money and counts add up** — one record of truth, reversibility, reconciliation, rounding, double submit.
6. **Time** — schedules, deadlines, expiries, reminders, retention, time zones; each implies a job — list them.
7. **Abuse and privacy** — what each role could do that it should not; which data is sensitive, who sees it, whether access is logged.
8. **Arrival and departure of data** — first admin, seed data, imports, exports, account deletion, offboarding.
9. **When things break** — per integration and job: retry, duplicate delivery, partial failure, what the user sees.

## 4. Contradictions, assumptions, open questions

- **Contradictions:** always logged, quoting both sides. Settled by precedence (newer version, signed-off PRD over notes, target system over current practice) → a decision with its reason, mentioned at the checkpoint as "resolved by precedence — say if this is wrong". Otherwise → an open question.
- **Assumptions** are `ASM-T1`, `ASM-T2` … (`ASM-##` without the T is Alice's — cite hers, never define one). Every `practice` requirement is one.
- **Open questions** (`OQ-#`, format in extract.md §4): merge near-duplicates; drop any whose answer would not change what gets built.
- When the spec is written they move to their one home (DECISIONS.md, or TECHNICAL.md for a single file) and the register sections become a pointer.

## 5. Architecture and quality — depth by size

The simplest architecture the requirements allow (brownfield: document and extend what exists): a monolith and a relational database; a service, cache, queue or search engine only where a cited REQ needs it. Where the sources are silent on stack, recommend one as an assumption. Record each significant choice as `AD-#` with its reason (Medium/Large: with the alternatives rejected). Every item is a concrete decision ("passwords hashed with argon2id"), never a platitude.

| | Small — essentials | Medium adds | Large adds |
|---|---|---|---|
| Security | Auth method; hashed passwords; expiring sessions; HTTPS; secrets outside code; input validation; authorisation on every endpoint | Server-side role matrix; audit log for sensitive actions; rate limits; personal-data inventory and retention; safe uploads | Threat model; data classification; encryption at rest; 2FA for privileged roles; compliance mapping; signed webhooks; security review before launch |
| Performance | Indexes; pagination | Explicit targets (p95, page load); background jobs for slow work | Capacity estimate; caching strategy; stateless scaling; load-test plan |
| Reliability | Daily backups; clear errors | Tested restore; retry with backoff; idempotent webhook and payment handlers; transactions around multi-step changes | Failure-mode table; availability target, RPO/RTO; graceful degradation; disaster recovery |
| Operations | Error tracking; dev + production | Structured logs; uptime alerts; staging; CI/CD | Dashboards, tracing, runbooks; zero-downtime deploys |
| Usability | Responsive; empty / error / loading states; confirm destructive actions | Accessibility basics (WCAG 2.1 AA); role-tailored navigation; search and filters | Accessibility review; localisation; offline strategy for field users |

**Rigour overrides size per module:** a Critical module gets the Large column's items that touch it (threat notes, failure modes, rollback, idempotency, audit trail) even in a Small system. Remove from a Small or Medium design unless a REQ demands it: microservices, Kubernetes, event sourcing, CQRS, a database per module, message brokers where a job queue does, multi-region, custom auth.

## 6. Review (after the spec is written)

Four groups: **completeness** (lenses 1, 3, 4, 8 — every role and screen) · **behaviour** (lenses 2, 5, 6, 9 — states, money, time, failures) · **safety** (lens 7 plus the security row for the size) · **consistency and proportion** (names, IDs and facts agree across core, module files and MODULES.md; nothing over-built for the size).

Small: one pass with all four in mind, from what is already in context. Medium: the four groups as checklists (with subagents: two reviewers). Large: four parallel reviewers, each given only the register and the spec. Critical modules get a full pass of their own. Fix blockers and should-fixes, turn client decisions into open questions, cut what is over-built.

## Appendix — existing code (brownfield): map it first, read-only

When the brief lists `Code (read-only)` and the repository holds application code. Stark reads it to fit the design to it and to fill MODULES.md Paths; it never changes the code and never judges what is *done* (Jarvis's audit does). No local path → ask the user; no code yet → greenfield, Paths `?`.

Write `<D>/_work/codebase.md`, an index of at most ~200 lines: stack in use (versions that matter) · layout (routes, models, migrations, jobs, screens, tests) · module ↔ paths as globs, plus files that belong to no module · conventions in force (naming, error format, API style, permission checks) · a first impression per module (*exists / partly / not found*, unverified) · binding rules copied from `CLAUDE.md` / `AGENTS.md`.

Consequences: the code fixes the stack and conventions — TECHNICAL.md documents them and changes one only as an `AD-#` forced by a requirement. Use the code's real names. Tag spec elements **Exists / Partial / Planned**. Module boundaries follow the code's seams where sensible; where not, say so in the module's Reason.
