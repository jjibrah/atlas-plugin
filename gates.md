# Gates

Spartan runs these with `atlasctl gate <G#> [--phase P1]`. Each check is scripted where possible; otherwise it becomes a yes/no question for the user. Results: **pass**, **fail** (with reasons) or **waived** (`atlasctl gate <G#> --waive "<reason>"`, logged). A check marked (S) applies to Standard and Critical; (C) only where a Critical module is involved.

## G1 — define → design
- Client sign-off recorded (`signoff` event for the PRD or proposal)
- No open questions in QUESTIONS.md → "Needed before we start"
- Every functional requirement has a status; no `Must` requirement is `to confirm`
- (S) Regulations section (PRD §15) is filled in or says "None identified"
- (C) Every legal flag in PRD §15 acknowledged by the user

## G2 — design → plan
- Every in-scope FR is cited by at least one REQ
- Every REQ has at least one acceptance criterion
- MODULES.md exists; every module's rigour is confirmed
- (S) No blocking open questions (OQ) left in TECHNICAL.md
- (C) Critical modules have threat notes and failure/rollback behaviour

## G3 — plan → build
- Every REQ is covered by a work package
- No dependency cycles between work packages
- Every phase has a goal (exit criterion)
- (C) Work packages in Critical modules are small (S/M) and end in a review checkpoint

## G4 — build → test (per phase)
- Every work package in the phase is done (evidence from reconcile) or explicitly deferred
- CI is green on the default branch (when CI exists)
- (S) No unresolved drift from the last reconcile
- (C) Security review recorded for changes touching Critical modules
- No secrets found in the code repositories' tracked files

## G5 — test → release (per phase)
- TEST-PLAN.md covers every acceptance criterion in the phase
- UAT passed and signed off by the client
- (S) GO-LIVE.md checklist complete
- (C) Rollback plan written and rehearsed; data migration rehearsed if any
