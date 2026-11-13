# Gate open items — plain meaning, fix, owner

For each `[FAIL]` / `[ASK ]` line of `atlas gate G#`: tell the user the meaning with the IDs from the line, then the fix. **Note to** names the agent that gets `atlas note --to <agent> "<fix>" --from spartan --refs <IDs>`; `user` means tell the user, no note. (S) Standard and Critical only · (C) Critical only.

## G1 — before design
| Open item, in plain words | Fix | Note to |
|---|---|---|
| The client has not approved the PRD or proposal | `atlas signoff --what "PRD v1.0" --by "<client role>" --evidence "…"` once they have | user |
| Answers needed from the client before we start are missing | Send QUESTIONS.md, record the answers | alice |
| A requirement has no valid status | confirmed / proposed / to confirm / deferred / rejected / out of scope | alice |
| A Must requirement is still "to confirm" | Confirm it with the client or lower its priority | alice |
| (S) PRD §15 (regulations) is empty | Fill it in, or write "None identified" | alice |
| ASK `legal_ack` | "Has the team taken advice on, or accepted, the legal flags in PRD §15?" | user |

## G2 — before planning
| Open item, in plain words | Fix | Note to |
|---|---|---|
| A client requirement (FR) has no technical requirement | Add or extend a REQ that cites it | stark |
| A REQ has no acceptance criterion | Add AC rows citing it | stark |
| No module list | Write design/MODULES.md | stark |
| Rigour levels are still proposals | `atlas rigour --accept [M2=Critical …]` | user |
| (S) Design questions block planning | Resolve the OQ rows (client-only ones go on to Alice) | stark |
| (C) A Critical module's spec lacks threat notes or failure/rollback | Add them; questions: `spartan.py threats <the module's signals>` | stark |

## G3 — before build
| Open item, in plain words | Fix | Note to |
|---|---|---|
| No work-package table | Write plan/PLAN.md | jarvis |
| A REQ is in no work package | Add it to one, or list it as already built | jarvis |
| "Depends on" loops, or names a missing work package | Fix the column | jarvis |
| A phase has no goal, or a work package names an unknown phase | Fix the phase table | jarvis |
| (C) A Critical work package is too big or has no review checkpoint | Split to S/M; end the title with "+ review" | jarvis |

## G4 — before testing (per phase)
| Open item, in plain words | Fix | Note to |
|---|---|---|
| Work in the phase is unfinished | Finish it, or `atlas wp WP-07 deferred --reason "…"` | user |
| Marked done, but no commit was matched | `atlas unmatched`, then `atlas learn '<glob>' WP-07` | user |
| The default branch fails CI | Fix the build or tests | user |
| (S) Records and code disagree (drift) | Settle each item `atlas status` lists | user |
| (C) A Critical module has no security review for this phase | Do the review now (review mode) | — |
| Secret-looking values are committed | Remove, **rotate the credential**, set it in the hosting provider | user |

## G5 — before release (per phase)
| Open item, in plain words | Fix | Note to |
|---|---|---|
| A criterion has no test, or TEST-PLAN.md / GO-LIVE.md is missing | `/sentinel P#` | sentinel |
| Tests fail or have not run | Run them, fix the code; `sentinel.py results` or `set` records them | user |
| The client has not accepted the phase | Client runs the UAT script; `atlas signoff --what "UAT P1" --by "<client>" --phase P1` | user |
| (S) Go-live items are unticked | Do them; tick them in GO-LIVE.md | user |
| (C) GO-LIVE.md has no Rollback section | Write it | sentinel |
| ASK `rollback_rehearsed` | "Was the rollback in GO-LIVE.md rehearsed — when, and did it work?" | user |
| ASK `migration_rehearsed` | "Was the migration rehearsed on a copy of real data, with counts checked?" | user |
