# Write — layout, style, diagrams

Read at the Write step, with the templates you will use.

## 1. Layout and budgets — choose before writing

| Situation | Layout |
|---|---|
| ≤ ~60 requirements and ≤ 6 modules | **Single file:** everything in TECHNICAL.md; each module is a `### 6.x M# Name` section. Small systems keep decisions and questions in it; Medium moves them to DECISIONS.md. |
| More, or size Large | **Core + module files:** TECHNICAL.md keeps what every implementer needs; `technical/mNN-<name>.md` per module (`templates/technical-module.md`); `technical/x-cross-cutting.md`. A Critical module may get its own file in any layout. |

Budgets (verify warns; agents load these files into limited context): TECHNICAL.md 60 KB single file, 40 KB as a core · each `technical/<module>.md` 35 KB · DECISIONS.md 40 · OVERVIEW.md 30 · MODULES.md 15 · any table cell ~600 characters (put the explanation in a note under the table). Over budget → move detail down a level or split the module.

## 2. TECHNICAL.md — for a coding agent that has only this document

Test: could an agent implement one module and its tests without asking a question? (The design is published to the code repository as `docs/blueprint/`; the PRD is not.)

1. **Structured over prose; one fact, one place** — tables, schemas, numbered flows; each entity, rule and state machine defined once and referenced by ID or `file §section`.
2. **Exact** — types, constraints, defaults, limits, error cases, who can do what; numbers copied from the register.
3. **Trace everything** — every rule, transition, permission, endpoint and criterion cites its `REQ-###` (a rule also cites `BR-##`). verify fails if a live REQ is cited nowhere in the spec.
4. **Depth follows rigour** (SKILL.md). A Critical module's spec must contain *Errors & edge cases*, *Failure & rollback*, *Threat notes* and *Audit trail* — gate G2 looks for the threat and failure/rollback notes. Do not pad Light modules with sections that say nothing: drop them with "None — <reason>."
5. **Headings name a module ID only for the module itself** (`### 6.1 M1 Identity`, or the file `technical/m01-identity.md`). Gate G2 finds a module's spec by the first heading that names it, so entity, state-machine and flow headings carry no module ID — write "Owner: M1" in the text. Never put REQ IDs in a table row whose first cell is a module ID.
6. **Mark what is not decided** — never present an assumption as a requirement: `> ⚠️ ASM-T3: …`, `> ❓ OQ-7: …` where it bites. Every `OQ-`, `AD-` and `ASM-T` cited must be defined as a table row or heading in its one home (DECISIONS.md, or TECHNICAL.md for a single file); elsewhere cite the ID with at most one line on the local impact.
7. **Write for partial loading** — an implementer reads the core's "always read" sections plus one module file: each module file is complete for its own work, and the core links every one.
8. **Brownfield** — tag each entity, endpoint, screen and transition Exists / Partial / Planned and use the code's names.
9. **No plan in the design** — no work-package table; TECHNICAL.md holds only the module build order and the `Depends on` column. (Small track: the plan still goes in `plan/PLAN.md`.)
10. **Header and housekeeping** — the header table keeps its `| Version | v1.0 — YYYY-MM-DD |` row (`atlas finish` reads it); every change adds a changelog row and bumps the version. No `{{placeholders}}` or template notes left; every relative link resolves.

**Acceptance criteria** have one home, the module's spec (cross-cutting ones in the non-functional section), as rows of

```markdown
| AC | REQ | Given / when / then |
|---|---|---|
| AC-NEW | REQ-045 | Given a pending order older than 30 min, when the expiry job runs, then it becomes `expired` and stock is released. |
```

Write `AC-NEW`, then `register.py number-ac <D>` (IDs are global, sequential, permanent). At least one per live REQ, each testable on its own. Work packages and tests cite them by ID.

**Open questions** use the table in extract.md §4 — gate G2 reads its `Blocking` and `Status` columns. Answered questions stay in the table with their answer and date.

## 3. Diagrams (Mermaid)

| Diagram | Type | Needed from |
|---|---|---|
| System context: people, platforms, external systems | `flowchart LR` | Small |
| Data model | `erDiagram` | Small |
| State machine per stateful entity, each paired with a transition table (from, event, actor, guard, to, side effects, REQ) | `stateDiagram-v2` | Small |
| Build order: module dependency graph, labels starting with the module ID (`auth["M1 Identity"] --> orders["M4 Orders"]`) | `flowchart TD` | Small |
| Components; sequence diagrams for critical flows (payments, auth, integrations) | `flowchart`, `sequenceDiagram` | Medium |
| Deployment | `flowchart` | Large |

Syntax that breaks rendering: read `references/diagrams.md` §2 once (verify warns on hyphenated or `end` node IDs and fails an empty diagram).

**A diagram pack exists (`<D>/DIAGRAMS.md`, the pictures the client saw):** build on it instead of redrawing. Keep its names for roles, records, states and parts; the design's diagrams add the technical detail (IDs, fields, modules). Link it from TECHNICAL.md's introduction (`[DIAGRAMS.md](DIAGRAMS.md)`). Where the design has to differ from a picture (a state added, a part split), change the pack in the same run: new version, a changelog row, `atlas export design/DIAGRAMS.md`, and tell the user the client's pictures changed.

## 4. DECISIONS.md (Medium / Large)

`templates/DECISIONS.md`: open questions (the G2 table), assumptions, contradictions, decision records (*context → decision → reason → alternatives rejected → consequences*). Small systems keep these inside TECHNICAL.md.

## 5. Module specs in parallel (core + module files, with subagents)

Write the core first. Then per module: `register.py slice <D> <M#>`, and give its subagent the core TECHNICAL.md, the slice, `templates/technical-module.md`, this file, the module's rigour with its depth rule, and (brownfield) `_work/codebase.md`. It writes `technical/mNN-<name>.md` with criteria as `AC-NEW` and replies only with the open questions, assumptions and cross-module needs it found. Then `register.py number-ac <D>` and fold the replies into DECISIONS.md.

## 6. OVERVIEW.md — only for `/stark overview` or a Large project

For a project manager or newcomer, distilled from the finished spec with `templates/OVERVIEW.md`: no fact that is not in TECHNICAL.md, the same module and role names. Plain words — no endpoints, field names, code, SQL or HTTP verbs (verify fails on them); the stack gets one sentence. Each section opens with a 1–3 sentence summary; diagrams use plain labels and at most 12 nodes; only blocking questions are listed. Length: 3–5 pages Small, 5–8 Medium, 8–12 Large.
