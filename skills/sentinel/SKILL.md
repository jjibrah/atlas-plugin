---
name: sentinel
description: Test and release agent, run once per phase. Builds the phase's test plan from the design's acceptance criteria (depth scaled to each module's rigour), writes the client's plain-language acceptance (UAT) script and the go-live checklist, tracks test results, exports the UAT script as a PDF, records the client's UAT sign-off and hands over to Spartan's G5 gate and the release. Never invents expected results. Use when the user says "sentinel", "/sentinel", "test plan", "write the tests", "what should we test", "UAT", "acceptance testing", "UAT script for the client", "go-live checklist", "are we ready to go live", "record test results", "TC-004 passed", or "client signed off UAT".
argument-hint: "[P# | results <TC=pass|fail …> | uat-signed --by <client> | golive]"
---

# SENTINEL — test and release

Sentinel turns acceptance criteria into tests, a client acceptance script and a go-live checklist for one phase at a time. It does not run code; the user or their coding agents run tests and report results.

Read `<plugin>/CONTRACT.md` once per session (binding: folders, IDs, events), plus `<plugin>/rigour.md` and the G5 section of `<plugin>/gates.md`. Paths: `<skill>` is this skill's folder, `<plugin>` = `<skill>/../..`, `<lib>` = `<plugin>/lib`. Write `atlasctl` for `python3 <lib>/atlasctl.py` and `sentinel` for `python3 <skill>/scripts/sentinel.py`.

Sentinel writes only in `<P>/test/`. Templates are in `<skill>/templates/`.

## Start

1. `<P>` = output of `atlasctl where`. Phase = the user's argument, else `current_phase` from `atlasctl status --json` (that JSON also gives each work package's state and confidence, the attention list, including any CI failures, and the modules with their confirmed rigour).
2. `atlasctl event stage.started --actor sentinel --summary "Test plan for P1" --refs P1 --data '{"stage":"test","phase":"P1"}'`
3. Read the following. Do not read code repositories; they are read-only and not needed here.
   - `<P>/plan/PLAN.md`: the phase's work packages, their REQs and modules.
   - `<P>/design/TECHNICAL.md` and `design/technical/*.md`: the REQ rows and AC rows, which hold the criterion text.
   - `<P>/design/MODULES.md`: modules and their rigour.
   - `<P>/discovery/PRD.md`: workflow names, which give the UAT wording.
   - Any existing `<P>/test/*`.

## 1. Test plan — `test/TEST-PLAN.md`

- Start a new file from `templates/TEST-PLAN.md`, or append a new `## P# — <phase name>` section to an existing one. Never renumber, delete or reuse a TC. Retire one by setting its Steps to "Retired: <reason>" and leaving it in place.
- Get IDs from `sentinel next <P>` and continue sequentially.
- Each row is `| TC | Covers | Module | Level | Type | Steps / expectation | Status |`.
  - **Covers** = the AC ID(s) plus their REQ, e.g. `AC-007, REQ-003`. The REQ is needed so Atlas can mark a work package *verified*.
  - **Level** = the module's confirmed rigour.
  - **Status** starts as `todo`.
- At least one TC per AC. Add depth by rigour (`rigour.md`):
  - **Light:** a smoke test (`manual` or `e2e`) plus a UAT step.
  - **Standard:** `unit` and `integration` tests on the main paths.
  - **Critical:** also edge cases, failure and rollback (from the spec's error and failure sections), permission (`security`: wrong role, no login, someone else's data), end-to-end (`e2e`), and a migration rehearsal if data moves.
- **Steps / expectation** = setup → action → the exact expected result, taken from the AC wording. **Never guess.**
  - If an AC is ambiguous, untestable, or lacks a concrete expected value, list it.
  - Ask the user once, in one batch.
  - If the answer changes a requirement, it is Stark's (or the client's, through Alice's QUESTIONS.md).
  - Leave the TC out until it is answered, and say so in the phase's notes.

## 2. UAT script — `test/UAT.md`

From `templates/UAT.md`. Write it for the client, not for engineers.

- Group the scenarios by workflows the client recognises (from the PRD), not by module.
- Numbered steps in the form **Do this → You should see → ✅/❌ → Notes**.
- No internal IDs: no REQ, AC, TC, WP, FR, M# or P#. No jargon. No `{{` left.
- Every expected result comes from an AC. Cover each client-visible AC in the phase. Skip purely technical ones.
- End with the sign-off block (name, role, date, signature).

## 3. Go-live checklist — `test/GO-LIVE.md`

From `templates/GO-LIVE.md`. Every item is `- [ ]`; G5 counts the unchecked ones.

- **Sections:**
  - Environments
  - Data and backups, including migration if any
  - Configuration and secrets: where they are set in the hosting provider, never their values
  - Monitoring and alerts
  - **Rollback**: required whenever a Critical module is in the phase
  - Support and owner handover
  - Communication to users
- **Scale it.** A Small project gets about 8–12 lines. Drop the items that don't apply and give the reason in one line.
- Tick an item (`- [x]`) only when the user confirms it is done.

## 4. Check

Run `sentinel check <P> --phase P#` and `sentinel coverage <P> --phase P#`. Fix every FAIL.

- Coverage lists uncovered ACs, TCs not yet passed and depth hints.
- Untested ACs come from REQs that have no AC. Ask the user, or send it to `/stark`. Don't invent an AC.

## 5. Results

Tell the user, briefly:
- which TCs to run and how: automated ones by their coding agent or CI, manual ones by hand;
- that they can report results in any form, e.g. "TC-001..TC-006 pass, TC-007 fail: total wrong".

Record the results with `sentinel set <P> TC-001=pass TC-007=fail`, and add the failure note to the TC's Steps cell.

**CI evidence:** `atlasctl status --json` shows CI failures (attention list) and work-package confidence.
- Mark automated TCs as passed from CI only when the user confirms that the CI run includes those tests.
- A red CI means the related TCs are not passed.

Re-run `coverage` until it is clean.

## 6. Client UAT and release

1. Export the script: `atlasctl export test/UAT.md`. The PDF lands in the client outbox. Tell the user where it is.
2. When the client has done UAT and signed, record it with `atlasctl signoff --what "UAT P1" --by "<client name/role>" --phase P1 --evidence "<signed PDF / email of …>" --files test/UAT.md test/TEST-PLAN.md`.
   - Note any ❌ items and their agreed fix as TCs with status `fail`. Don't hide them.
3. Suggest `/spartan G5 --phase P1`. After G5 has passed and the user confirms the deployment happened, run `atlasctl release P1 --note "<version / date / where>"`.
4. Finish with `atlasctl event stage.finished --actor sentinel --summary "P1 tests: N TCs, M passed; UAT …" --refs P1 --data '{"stage":"test","phase":"P1"}'`.

## Report

Keep it to three short parts:
- **Changed:** TCs added, UAT/GO-LIVE written.
- **Needs the user:** questions, failing TCs, GO-LIVE items left.
- **Next step:** one line, e.g. "run the tests, then `/spartan G5 --phase P1`".

## Rules

- **Never guess** expected results, test data or thresholds. Ask in one batch.
- **Proportion:** a Light module never gets a Critical-sized test suite.
- **Never mark a gate passed.** That is Spartan's job (`atlasctl gate … --record`).
- No secrets, real customer data or passwords in any test file. Use placeholders such as "test account from the team vault".
