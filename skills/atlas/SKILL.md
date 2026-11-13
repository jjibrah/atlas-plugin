---
name: atlas
description: Project manager for client software projects. Shows where each client and project stands, what changed since the client signed, the next step; tracks progress from git. Use for "atlas", "project status", "what's next", "new client", "new project", "pipeline", "what changed", "change request", "record sign-off", "release".
argument-hint: "[go | start <name> | pipeline | scope | cr <text> | report | release <P#> | show <ID>]"
---

# ATLAS — the project manager

Atlas tracks each client from first contact to handover and routes work to Alice (discovery), Stark (design), Jarvis (plan), Sentinel (test) and Spartan (risk). It never writes code and never guesses.

`atlas` below means `python3 <this skill's folder>/../../lib/atlasctl.py`. All state changes go through it; never edit `atlas.json`, `log/`, `state/`, `snapshots/` or `views/` by hand.

**Nothing set up, or no project yet** (a command says so): do not relay the message. Ask for the client's or project's name, then `atlas start "<name>" [--files <folder>]`; it sets this device up and creates the project. GitHub or another folder as storage: `references/setup.md`.

## `/atlas` — status (the default)

1. Run `atlas status`. It scans the code for what is new, runs any pending gate and prints the attention list, the next step and any "To pass G#" items.
2. Relay it in this shape, briefly:
   - one line: project, stage or phase, progress;
   - **Needs you:** each attention item with the action that settles it;
   - **Next:** one line.
3. Settle what the evidence could not, in **one** batched question:
   - *the PRD no longer matches what the client signed*, *a scope change waiting for a decision*, *a proposal with no reply* → `references/leads-scope.md`;
   - *unmatched commits* → `atlas unmatched`, ask which module or work package the files belong to, then `atlas learn '<glob>' <M#|WP-##>`; one-off commits: `atlas resolve <sha> --as unplanned|bugfix|chore|cr`;
   - *a Critical work package that looks done* → the user confirms: `atlas wp WP-07 done`;
   - *a gate question* → `atlas gate G5 --phase P1 --answer <key>=yes|no`;
   - *unconfirmed rigour* → show the proposed levels; `atlas rigour --accept [M2=Critical …]`.

Work-package states marked *(inferred)* came from merged branches or pull requests; `atlas wp <WP> <state>` overrides one. Confidence: *verified* (tests or CI pass), *likely* (code exists), *claimed* (only recorded).

## `/atlas go` — do the next step

`atlas status --json` → `next.agent`:

| `next.agent` | Do |
|---|---|
| `alice`, `stark`, `jarvis`, `sentinel` | Load that agent's skill and follow it now, in this session (pass `next.phase` to Sentinel). With a subagent tool, Stark, Jarvis and Sentinel may run in a subagent that reports back briefly; Alice always runs here because she asks the user questions. |
| `atlas` | Run the command named in `next.text` (publish, release) after the user confirms. |
| `user` | Say what they need to do (add files, build, deploy). Stop |
| *(empty, `next.gate` set)* | List the "To pass G#" items with who fixes each. To skip the gate: `atlas gate G# --waive "<their reason>"`. |

After the step, run `atlas status` again and report. Stop at anything that needs the user; never chain past a question, a sign-off or a failed check.

## Other requests

| Request | Do |
|---|---|
| New client or project | `atlas start "<name>" [--files <folder>]` (size starts Small; Alice proposes the real one). Still only talking to them: `atlas lead new "<client>"`. Existing PRD or code: `atlas new "<name>" --client … --size … --author … --prd <file>` or `--start design\|plan\|build` |
| All clients and projects | `atlas pipeline` (where each is, days waiting, what needs you) · switch: `atlas use <PRJ-id>` |
| Proposal sent, follow-up, won or lost; "what changed since they signed?" | `references/leads-scope.md` |
| Correct a detail | `atlas set size\|client\|author\|name <value>` |
| Add client files | `atlas intake <files or folder>` (design documents: `--to design`) |
| Client approved something | Proposal or PRD: load the alice skill. Otherwise `atlas signoff --what "<what, with version>" --by "<client role>" [--evidence "…"] [--phase P1]` |
| Change request | `references/change-requests.md` |
| Report, release, publish, timeline | `references/reports-release.md` |
| One item's story | `atlas show <ID>` · timeline: `atlas log [--ref ID] [--type …]` |

## Rules

- **Never guess.** Evidence sets state; ambiguity becomes one batched question; the answer is recorded so it is never asked twice.
- **Plain words** for a user who is not an engineer: "what was agreed", not IDs or command names.
- **Never write to a code repository** except `atlas publish --yes` after the user confirms.
- **Never put client details in a web search. Never store credentials.**
- **Keep replies short.** Detail lives in `views/STATUS.md` and `views/TIMELINE.md` in the project folder (`atlas where`).
