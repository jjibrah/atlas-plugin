# Writing style

The two documents have different readers. Write each for its reader.

---

## OVERVIEW.md — for people

**Reader:** a project manager, designer, or new developer on day one (the client gets Alice's proposal, not this). Smart, busy, not necessarily technical.

**Test:** could the client read this and say "yes, that's what we want" — or spot what's wrong?

### Rules

1. **Plain words.** Say what the system does for people.
   - ✅ "When a customer pays, the order moves to *Preparing* and the kitchen is notified."
   - ❌ "On `payment.succeeded` webhook the Order aggregate transitions to PREPARING and emits an event."
2. **No technical leakage.** No endpoints, field names, table names, code, framework names in body text, HTTP verbs, JSON, SQL. (The tech stack may appear once, in one plain sentence, e.g. "It will be a web app and an Android/iOS app sharing one backend.")
3. **Lead with the summary.** Each section starts with 1–3 sentences that stand alone. Detail follows.
4. **Short sentences, short paragraphs.** Bullets and small tables over walls of text.
5. **Use the business's own vocabulary** (from the glossary), consistently.
6. **Name things the same as TECHNICAL.md.** Module and role names must match exactly, so people and agents talk about the same things.
7. **Show uncertainty honestly.** Open questions go in their own section, phrased as questions the client can answer.
8. **Length target:** Small 3–5 pages, Medium 5–8, Large 8–12. If you're over, cut detail — it belongs in TECHNICAL.md.

---

## TECHNICAL.md — for coding agents and developers

**Reader:** an AI coding agent (or developer) about to implement one module, who has *only* this document.

**Test:** could an agent implement the module and its tests without asking a question or opening the PRD? (TECHNICAL.md is published to the code repository as `docs/blueprint/design/TECHNICAL.md`; the PRD is not.)

### Rules

1. **Structured over prose.** Tables, numbered lists, schemas, checklists. Prose only for rationale.
2. **Explicit and exact.** Types, constraints, defaults, limits, error cases, who-can-do-what. Copy numbers from the sources exactly.
3. **One fact, one place.** Define each entity, rule, and state machine once; reference it elsewhere by ID or link.
4. **Trace everything.** Every business rule, state transition, permission, and acceptance criterion cites its `REQ-###` (and a rule cites Alice's `BR-##` when it has one). Assumptions cite `ASM-T#`; unresolved items cite `OQ-#`.
5. **Imperative, testable acceptance criteria.** "Given a pending order older than 30 min, when the expiry job runs, then the order becomes `expired` and stock is released (REQ-045)."
6. **Stable identifiers.** Use `snake_case` / `kebab-case` names consistently for entities, fields, states, events, endpoints; never rename without updating every reference.
7. **Decisions with reasons.** Each architecture choice: *decision — reason* (and *trade-off* for Large).
8. **Depth follows size and rigour.** Don't pad Small systems or Light modules with sections that say nothing; don't skimp on Large systems or Critical modules — those carry every error and edge case, failure and rollback behaviour, threat notes and an audit trail (rigour.md).
9. **Mark what's not decided.** Never present an assumption as a requirement. Use `> ⚠️ ASM-T3: …` or `> ❓ OQ-7: …` inline where it affects the design.
10. **Write for partial loading.** An agent implementing one module reads the core file's "always read" sections plus that module's file — nothing else. So: each module file must be complete for its own work, the core must not repeat module detail, and cross-references name the file and section (`technical/m04-billing.md §2`).
11. **Respect the size budgets** in `sizing-rubric.md`. Keep table cells short; a cell that needs three sentences becomes a note under the table.
12. **Existing systems:** tag each entity, endpoint, screen, and transition **Exists**, **Partial**, or **Planned** from what you read in the code, and use the code's real names. An agent must know whether it is extending or creating. (Proof of what is *done* against each requirement is Jarvis's audit, with `path:line` evidence.)
13. **Questions and assumptions have one home.** Their full text lives in DECISIONS.md (in TECHNICAL.md for a single-file blueprint). Everywhere else cite the ID with at most one line on the local impact. Once that home is written, replace the register's Open questions and Assumptions sections with a pointer to it — do not maintain two copies.
14. **Acceptance criteria have one home**: the module's spec, as rows of a table `| AC | REQ | Given / when / then |` with global sequential IDs `AC-001`, `AC-002` … (`register.py next-ac <D>` prints the next). Every live REQ has at least one. Jarvis's work packages and Sentinel's tests cite them by ID — never renumber.
15. **Keep the source's identifiers** (decision numbers, roadmap items, feature codes) alongside the REQ IDs wherever the team already uses them.
16. **Headings carry module IDs only for the module itself** (`### 6.1 M1 Identity`, or the file `technical/m01-identity.md`). Gate G2 finds a module's spec by the first heading naming it.

---

## DECISIONS.md and MODULES.md

- **DECISIONS.md** holds what was decided and what is still open. Decisions use a short record: *context → decision → reason → alternatives rejected → consequences*. Open questions carry a recommended default, `Blocking` yes/no and a `Status`, so nothing waits on them. Phrase questions so they can be answered in one line.
- **MODULES.md** is one table and a two-line note — nothing else. Reasons are one plain line each.
