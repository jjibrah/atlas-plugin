# Brief: {{Phase / round name}} ({{work packages and their titles}})

Source: `docs/blueprint/plan/PLAN.md` {{§4, WP-04–WP-06}} (published by `atlas publish`). Base: {{branch `main` @ `abc1234`}}.

**Mode:** {{single agent / orchestrator + N lanes}}. {{Lanes touch disjoint files, so they run in parallel. The orchestrator owns sequencing, merging, the full test run and the hand-back.}}

## Read first (everyone)
1. `CLAUDE.md` / `AGENTS.md` — the project rules below come from here and are binding.
2. `docs/blueprint/design/TECHNICAL.md` §1, §3, §4, and `docs/blueprint/design/MODULES.md` for each module's rigour.
3. The spec sections and files listed in your lane.

## Standing rules
<!-- TEMPLATE NOTE — delete before finishing. Copy the project's real rules from CLAUDE.md / AGENTS.md; do not invent any. -->
- **Agents:** {{at most N at once}}; each lane on its own branch named after its work package — `WP-04-short-title` — with every commit message starting with the ID (`WP-04: …`).
- **Progress is inferred, never typed.** Atlas marks a work package *in progress* from the first branch, commit or pull request that names it, and *done* when its branch or pull request (title or branch `WP-04-…`) is merged into the default branch, or a commit there says "WP-04 done" / "closes WP-04". Use exactly these names; do not edit `PLAN.md`.
- **Tests:** {{lanes run targeted tests only; the orchestrator runs the full suite once after merging; commands: `…`}}
- **Shared resources:** {{database / lock / seeded accounts — how to use them safely}}
- **Never:** {{project-specific prohibitions — spend limits, formatters, real third-party calls in tests}}
- **Numbering / ownership:** {{migration numbers per lane}}
- **Commits:** {{convention}}
- **Flaky failures:** find the cause; do not re-run until green.

## Baseline (before any lane starts)
{{Result of the full test run on the base commit: N passed, N failed — list the failures so new ones are attributable.}}

---

## Lane A: {{WP-04 — title}} ({{REQ IDs}})

**Branch:** `WP-04-{{short-title}}` · **Rigour:** {{Light / Standard / Critical}}

**Read:** {{`docs/blueprint/design/technical/m04-orders.md` §2, §5}}

**Owns** (no other lane edits these):
- `{{path/to/file}}`
- new `{{path/to/new_file}}`

**Do:**
1. {{step — reference the spec section instead of restating it}}
2. {{…}}

**Acceptance:**
1. {{AC-0NN, AC-0NN}} (design spec) — each with a test
2. {{existing tests for … still pass}}
3. {{Critical: review checkpoint — what is reviewed and by whom}}

---

## Lane B: {{WP-05 — title}} ({{REQ IDs}})

**Branch:** `WP-05-{{short-title}}` · **Rigour:** {{…}}

**Read:** {{…}}

**Owns:**
- `{{…}}`

**Do:**
1. {{…}}

**Acceptance:**
1. {{…}}

---

## Orchestrator: integration and hand-back
1. Merge lanes in this order: {{A, then B}} — one merge commit per lane.
2. {{Apply migrations / run codegen / other integration steps.}}
3. Run the full test suite; compare with the baseline. Investigate every new failure.
4. Do **not** edit `docs/blueprint/` (it is regenerated). Merge each finished lane's branch or pull request (or commit "closes WP-04") so Atlas sees it as done; tell the user what is blocked, then they run `/atlas`.
5. **Hand back:**
   - what changed
   - test results compared with the baseline
   - decisions the owner needs to make
   - anything deferred, and why

**Out of scope:** {{what this round must not touch, with the work package that will}}
