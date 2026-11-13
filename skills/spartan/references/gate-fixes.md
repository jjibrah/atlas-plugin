# Gate checks — what a FAIL means and who fixes it

Keys are the ones `atlasctl gate` prints for ASK checks and stores in recorded results. Explain each FAIL to the user in one plain sentence, then give the fix and the agent.

## G1 — define → design
| Key | Plain meaning | Fix | Who |
|---|---|---|---|
| signoff | The client has not approved the PRD/proposal yet | Get approval, then `atlasctl signoff --what "PRD v1.0" --by "<client>" --evidence "…"` | user → atlas |
| questions | Questions we need answered before starting are still open | Send QUESTIONS.md, record answers | `/alice` |
| frs | Some requirements have no (valid) status | Give every FR a status: confirmed / proposed / to confirm / deferred / rejected / out of scope | `/alice` |
| must | A "Must" requirement is still "to confirm" | Confirm it with the client or lower its priority | `/alice` + client |
| regulations | (S) PRD §15 regulations is empty | Fill it in, or write "None identified" | `/alice` |
| legal_ack (ASK) | PRD §15 flags something needing legal advice | Ask: "Has the team acknowledged the legal flags in PRD §15 (e.g. taken advice or accepted the risk)?" | user |

## G2 — design → plan
| Key | Plain meaning | Fix | Who |
|---|---|---|---|
| fr_req | A client requirement (FR-…) has no technical requirement | Add/extend a REQ that cites it | `/stark` |
| acs | A REQ has no acceptance criterion | Add AC-… rows citing the REQ | `/stark` |
| modules | No module list | Write design/MODULES.md | `/stark` |
| rigour | Rigour levels are only proposals | User confirms each: `atlasctl rigour M1 Critical --reason "…"` | user |
| oq | (S) Blocking open design questions remain | Resolve the OQ rows (ask user/client) | `/stark` (+ `/alice` for client questions) |
| crit_M# | (C) A Critical module spec lacks threat notes or failure/rollback behaviour | Add them (see `references/threat-notes.md`) | `/stark` |

## G3 — plan → build
| Key | Plain meaning | Fix | Who |
|---|---|---|---|
| plan | No work-package table | Write plan/PLAN.md | `/jarvis` |
| coverage | A REQ is in no work package | Add it to a WP | `/jarvis` |
| cycles / deps | Work packages depend on each other in a loop / on a WP that does not exist | Fix "Depends on" | `/jarvis` |
| goals / phases | A phase has no exit criterion / a WP names an unknown phase | Fix the phase table | `/jarvis` |
| crit_wps | (C) Critical-module WPs are too big or have no review checkpoint | Split to S/M; end each with "… + review" | `/jarvis` |

## G4 — build → test (per phase)
| Key | Plain meaning | Fix | Who |
|---|---|---|---|
| wps / done | Work in the phase is unfinished | Finish it, or `atlasctl wp WP-07 deferred --reason "…"` (user decides) | user / coding agents |
| evidence | A WP is marked done but no code was seen | `/atlas status`, then `atlasctl learn '<glob>' WP-07` or confirm | `/atlas` |
| ci | CI is not green on the default branch | Fix the build/tests | user / coding agents |
| drift | (S) Records and code disagree | Resolve the drift items | `/atlas` |
| security_review | (C) A Critical module has no security review for this phase | `/spartan review --phase P# --module M#` | `/spartan` |
| secrets | Secret-looking values are committed | Remove them, **rotate the credential**, move it to the hosting provider's settings | user |

## G5 — test → release (per phase)
| Key | Plain meaning | Fix | Who |
|---|---|---|---|
| tests | An acceptance criterion has no test | Add a TC | `/sentinel` |
| results | Tests failing or not run | Run them, fix failures, record results | user / coding agents → `/sentinel` |
| uat | The client has not signed off acceptance testing | Client does UAT; `atlasctl signoff --what "UAT P1" --by … --phase P1` | client → `/sentinel` |
| golive | (S) Go-live checklist has unticked items | Do them; tick in GO-LIVE.md | user → `/sentinel` |
| rollback_rehearsed (ASK) | (C) | Ask: "Has the rollback in GO-LIVE.md been rehearsed (when, and did it work)?" — FAIL if no Rollback section | user; `/sentinel` writes the section |
| migration_rehearsed (ASK) | (C) | Ask: "Was the data migration rehearsed on a copy of real data, with counts checked?" | user |
