# Leads, the pipeline and the scope watch

Talk to the user in plain words: "what was agreed", "a change to what was agreed", never IDs or command names.

## Leads and the pipeline

A lead is a client you are still talking to. It is an ordinary project, so Alice can already write up its meetings.

| When | Command |
|---|---|
| A possible client appears | `atlas lead new "<client>" [--contact "…"] [--source "referral"] [--files <folder>]` |
| A call or an email worth keeping (no requirement in it) | `atlas lead note "<what happened>"` |
| The proposal went out | `atlas lead sent "Proposal v1.0" [--followup +5d]` — also freezes the requirements as what was agreed |
| No reply, you chased them | `atlas lead followup +5d` (or a date, `2026-11-20`) |
| They said yes | `atlas lead won`; the written approval is a sign-off (the alice skill, "the client approved") |
| They said no | `atlas lead lost --reason "<why>"` |
| "Where are all our clients?" | `atlas pipeline`: every client and project, where it is, days waiting, how many things need the user, the next step. Rows that need a follow-up come first. Relay it as a short list, most urgent first |

Status and the pipeline say "FOLLOW UP" when the follow-up date has passed with no reply recorded: remind the user, then record what happened with one of the commands above.

## The scope watch

`atlas lead sent` and `atlas signoff` freeze the PRD's requirement and rule rows as the baseline: what was agreed. From then on `atlas status` reports any difference, until someone decides.

| Status says | Do |
|---|---|
| "The PRD no longer matches what the client signed (or: the proposal you sent)" | Steps 1–3 below |
| "Scope change waiting for a decision (CR-##)" | Ask the user whether both co-founders, and the client where it changes what they get or pay for, have agreed. Then step 3 |
| "CR-## was rejected but the PRD still contains its change" | Load the alice skill: she puts the PRD back (her `references/scope.md` §3) |

1. `atlas scope` lists every difference: `ADDED`, `CHANGED` (`was:` agreed, `now:` current) or `REMOVED`, with `from:` the meeting moment or document it came from and `touches:` what is already designed, planned or tested on top of it. "(changed 3 times)" marks a requirement that keeps moving: say so.
2. Tell the user in plain words, one line per difference: what was agreed, what it says now, where the change came from, what it affects. Ask them to decide; never decide for them.
3. Record the decision:

| Decision | Command |
|---|---|
| Accept the change | `atlas scope --cr "<short title>"` opens `CR-##`; once everyone agrees `atlas cr approved CR-##` moves the baseline for those rows. Then `references/change-requests.md` from step 4: Stark, Jarvis and Sentinel catch up |
| Keep what was agreed | `atlas scope --cr "<short title>"`, then `atlas cr rejected CR-## --note "<why, who decided>"`. Atlas leaves Alice a note to put the PRD back; status keeps reporting until it matches |
| Still discussing | `atlas scope --cr "<short title>"` and leave it open: it stays on the attention list and in the pipeline |
| It is not a change of scope (a question was answered, wording was tidied) | `atlas scope --baseline "<why>"` accepts the PRD as it is now. Only with the user's say-so |

`atlas scope` with nothing to report says "In sync"; "No baseline yet" means no proposal was recorded as sent and nothing was signed.
