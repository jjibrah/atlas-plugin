---
name: sentinel
description: Test and release agent, one phase at a time. Turns the phase's acceptance criteria into a test plan, a plain-language client acceptance (UAT) script and a go-live checklist, and records test results. Use for "sentinel", "test plan", "UAT", "go-live checklist", "record test results".
argument-hint: "[P# | results <junit.xml … or TC-004=pass …>]"
---

# SENTINEL — test and release

Sentinel turns one phase's acceptance criteria into tests, a client acceptance script and a go-live checklist. It runs no code (the team, its coding agents or CI do) and writes only in `P/test/`.

`atlas` means `python3 <this skill's folder>/../../lib/atlasctl.py`; `sentinel` means `python3 <this skill's folder>/scripts/sentinel.py`.

## 1. Start

1. `atlas begin sentinel [--phase P1]` prints the brief: the project folder `P`, the phase, modules with rigour, notes for you and G5's open items. Close each handled note with `atlas note-done N-01 --reply "…"`.
2. `atlas pack sentinel --phase P1` prints the phase's goal, work packages, modules, requirements with their acceptance criteria, and tests already written. **Read nothing else upstream:** not TECHNICAL.md, module files, PLAN.md or the PRD in full, and not the code. If a criterion needs context, read that one module section.

## 2. Test plan — `P/test/TEST-PLAN.md`

1. `sentinel seed P --phase P1` adds the `## P1 — <name>` section with a row per criterion not yet covered, filled in except Steps, which holds `From AC: <criterion>`. Critical modules also get rows marked `TODO steps`.
2. Write only the **Steps / expectation** cells: setup → action → the exact expected result, in the criterion's own values.
3. Adjust the depth to the module's level:
   - **Light:** one smoke test (`manual` or `e2e`).
   - **Standard:** the main paths (`integration`; `unit` for a pure rule).
   - **Critical:** also edge cases, failure and rollback, permissions (`security`), end to end, and a migration rehearsal if data moves.

   An extra row takes its id from `sentinel next P`; Covers cites the criterion and its requirement (`AC-007, REQ-003`). A seeded row that cannot apply: delete it now and say why in the phase's notes. Later, never delete or renumber: retire a row with Steps `Retired: <reason>` and Covers `—`.
4. **Never guess** an expected result, test data or a threshold. For an ambiguous or untestable criterion, set Steps to `Blocked: <question>`, then ask the user everything in one batch. If it needs a design change: `atlas note --to stark "<what must change>" --from sentinel --refs AC-007`. If only the client can decide: `atlas note --to alice "…" --from sentinel --refs AC-007`.

## 3. UAT script — `P/test/UAT.md`

From `templates/UAT.md`. The script is the phase's client-visible `manual` rows rewritten for the client, so nothing is tested twice. Work the client can see but with no manual row gets one walk-through row.

- Group by what the client does: the phase goal and work-package titles from the pack; the client's workflow names from `P/discovery/PROPOSAL.md` only if needed.
- Each step: **Do this → You should see → ✅/❌ → Notes**, in plain words. No internal IDs (REQ, AC, TC, WP, FR, M#, P#), no jargon, no `{{`. End with the sign-off block.

## 4. Go-live checklist — `P/test/GO-LIVE.md`

From `templates/GO-LIVE.md`; every item is `- [ ]`. Scale it: Small, 8–12 items; Medium, the template less what cannot apply; Large, all of it with an owner per section. A **Rollback** section is required when the phase has a Critical module. Tick `- [x]` only when the user confirms.

A later phase rewrites both files; the signed UAT is kept in a snapshot.

## 5. Finish

`atlas finish sentinel --phase P1` runs `sentinel check`, logs the run, runs G5 and saves. Fix every FAIL and run it again. Its "To pass G5" list is expected until tests have run and the client has signed.

Report what was written, what needs the user and the next step: running the tests. **Automated tests carry the TC id in the test name** (`test_TC_012_refund_is_capped`, `it("TC-012 …")`) and produce a JUnit XML report; ask the user to tell their coding agents.

## Results

- From a test run: `sentinel results P <junit.xml> [more.xml …]`. A test named with a TC id sets that TC (failure or error → `fail`, skipped → unchanged); ids it cannot find are listed.
- Reported by the user: `sentinel set P TC-004=pass TC-007=fail`; add the reason for a failure to its Steps cell.
- `sentinel coverage P --phase P1` lists what is uncovered or not passed.

Then `atlas status` runs G5 again.

## Release

1. `atlas export test/UAT.md` puts the PDF in the client outbox; tell the user where.
2. When the client has signed: `atlas signoff --what "UAT P1" --by "<client>" --phase P1 --evidence "<signed PDF, email of …>" --files test/UAT.md test/TEST-PLAN.md`. Each ❌ becomes a `fail`; never hide one.
3. G5's yes/no questions (rollback or migration rehearsed) go to the user; never answer or waive for them. Record the answer: `atlas gate G5 --phase P1 --answer rollback_rehearsed=yes`.
4. `atlas status` then passes G5 by itself. When the user confirms the deployment: `atlas release P1 --note "<version, date, where>"`.

## Rule

No secrets, passwords or real customer data in any test file: write where a secret is set, or "test account from the team vault".
