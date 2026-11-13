# ATLAS shared contract

The interface every agent in this plugin follows: where things live, which IDs exist and who issues them, and how a run starts and ends. When a skill and this contract disagree, the contract wins.

**Agents do not read this file during a run.** `atlas begin <agent>` prints the parts that matter for that run. This file is for people changing the plugin.

## 0. A run, start to finish

`atlas` means `python3 <plugin>/lib/atlasctl.py` (after `atlas setup` there is also an `atlas` terminal command).

| Step | Command | What it does |
|---|---|---|
| Start | `atlas begin <agent> [--phase P1] [--stage none\|handover]` | Pulls, logs `stage.started`, prints a brief: project, path, stages, modules and rigour, what changed upstream since this agent last ran, notes left for it, open items of its gate |
| Read | `atlas pack <agent> [--phase P1] [--module M3] [--changed] [--report]` | Prints only the rows that agent needs from upstream documents. Agents read packs, not whole upstream documents |
| Talk | `atlas note --to <agent> "<text>" --from <agent>` · `atlas note-done N-01 --reply "…"` | Notes between agents; they appear in the recipient's next brief |
| End | `atlas finish <agent> [--phase P1] [--stage none\|handover]` | Runs the agent's check script, logs document versions and `stage.finished`, records what the run was built on, runs the gate, rebuilds the views, saves once |

- **Gates run by themselves**, in `finish` and in `atlas status`. A gate that passes is recorded; one with open items is listed under "To pass G#". Spartan is only needed for waivers, security reviews, or when a failure needs explaining.
- **Staleness.** `finish` records a fingerprint of the upstream rows a run used (PRD requirements for Stark; REQs and criteria for Jarvis; both for Sentinel). Status reports when those rows change afterwards.
- **Tracks.** A `Small` project is on the `small` track: Stark writes the design and the plan in one run (`finish stark` closes both stages). Everything else is `standard`.
- **The front door.** `atlas start "<client or project>" [--files <folder>…]` needs nothing set up: on a new device it creates a folder-mode setup at `~/AtlasProjects`, then the project (size `Small` until `atlas set size …`), and takes in the files. `atlas lead new "<client>"` is the same with a `lead.created` event. A lead is an ordinary project; `atlas pipeline` lists them all.
- **Scope watch.** `atlas lead sent` and `atlas signoff` (not a phase or UAT sign-off) freeze the PRD's FR / BR rows in `state/baseline.json`. Status reports any later difference until it is settled: `atlas scope` shows it; `atlas scope --cr` opens a change request carrying the differing IDs; `atlas cr approved` moves the baseline for those IDs; `atlas cr rejected` leaves a note for Alice, who puts the PRD back; `atlas scope --baseline "<why>"` accepts the PRD as it is. Agents never edit the baseline.
- **Diagram pack.** `/stark diagrams` runs as `begin stark --stage none` … `finish stark --stage none`; while `design/TECHNICAL.md` does not exist, that `finish` runs no check (Stark runs `verify.py <P>/design --diagrams` itself).
- **Progress is inferred.** A work package moves to *in-progress* on its first matching commit, branch or pull request, and to *done* when its branch or pull request is merged, or a commit on the default branch says so ("WP-07 done", "closes WP-07"). What the user records with `atlas wp` always wins.

## 1. Paths

- `<plugin>` is the plugin root (the folder containing `CONTRACT.md`). From any skill: `<skill dir>/../..`.
- `<lib>` = `<plugin>/lib`. Run scripts as `python3 <lib>/<script>.py …` (Python 3.9+, standard library; PDF reading and export use the venv that `atlasctl setup` creates and the scripts re-exec into it automatically).
- `<P>` is the **project storage folder** of the current project: `atlasctl where` prints it. Agents never guess it.

```
<P>/                         one project (a private git repo in GitHub mode)
├── atlas.json               identity: id, name, client, size, author, repos[]   (written by atlasctl only)
├── project.md               generated summary
├── log/events.jsonl         append-only, hash-chained event log                  (atlasctl only)
├── snapshots/               documents frozen at milestones                        (atlasctl only)
├── state/                   mapping.json · reconcile.json · stamps.json · baseline.json · lock   (atlasctl only)
├── discovery/               ALICE
│   ├── sources/             client files dropped here by the user (never modified)
│   ├── PRD.md  PROPOSAL.md  QUESTIONS.md
│   └── _work/               STATE.md · sources/ (chunks) · meetings/ · research.md · proposal-basis.json
├── design/                  STARK
│   ├── TECHNICAL.md (+ technical/*.md, DECISIONS.md, OVERVIEW.md)
│   ├── DIAGRAMS.md          the diagram pack: plain-language pictures for the client (optional)
│   ├── MODULES.md           module · rigour · code paths  (read by atlasctl)
│   ├── sources/             extra technical documents (optional)
│   └── _work/               STATE.md · requirements.md · ledger.md · traceability.md · sources/
├── plan/                    JARVIS
│   ├── PLAN.md              phases + work packages        (read by atlasctl)
│   ├── briefs/  AUDIT.md  audit/
│   └── _work/               STATE.md · codebase.md
├── test/                    SENTINEL: TEST-PLAN.md · UAT.md · GO-LIVE.md
├── reports/                 ALICE (report/handover) and ATLAS: status-YYYY-MM-DD.md · client-update-YYYY-MM-DD.md · HANDOVER.md
└── views/                   generated by atlasctl: STATUS.md · TIMELINE.md (never edit)
```

- **Code repositories are read-only** for every agent, with one exception: `atlasctl publish` copies the technical blueprint (design/ + plan/, never discovery/ or reports/) into a code repo's `docs/blueprint/` after the user confirms. Coding agents read it there.
- **Client outbox:** `~/Desktop/<PRJ-id>-<slug>-for-client/` — PDFs only, produced by `atlasctl export`. The internal PRD, design and plan are never exported, with one exception: the diagram pack `design/DIAGRAMS.md`, which is written for the client.
- Agents write only inside their own folder (above). Everything else goes through `atlasctl`.

## 2. IDs

Each ID kind has one owner. IDs are permanent: never renumber, never reuse.

| Kind | Format | Owner | Issued by |
|---|---|---|---|
| Project | `PRJ-0001` | Atlas | registry |
| Meeting, pain point, workflow, proposal, decision, research, assumption, clarification, client question | `M01` `PP-01` `WF-01` `P-01` `D-01` `RS-01` `ASM-01` `U-01` `Q-001` | Alice | `alice.py next` |
| Functional requirement, business rule | `FR-001` `BR-01` | Alice | `alice.py next` |
| Technical requirement | `REQ-001` (Source column cites its `FR-…`, or a source chunk such as `[d1-004]` when the PRD was adopted) | Stark | `register.py number` |
| Acceptance criterion | `AC-001` (inside REQ rows / module specs, cites REQ) | Stark | Stark, sequential |
| Architecture decision, open question, assumption (technical) | `AD-1` `OQ-1` `ASM-T1` | Stark | Stark |
| Module | `M1`, `M2` … (in MODULES.md) | Stark | Stark |
| Work package | `WP-01` | Jarvis | Jarvis |
| Phase | `P0`, `P1` … | Jarvis | Jarvis |
| Test case | `TC-001` (cites AC) | Sentinel | Sentinel |
| Change request | `CR-01` | Atlas | `atlasctl cr open` |
| Gate | `G1`–`G5` | Spartan | fixed |

**Chain:** source (`[M02@00:14:32]`, `[d3-002]`) → `FR` → `REQ`/`AC` → `WP` → commits/PRs → `TC` → release. Every downstream row cites its upstream ID in the same table row. `atlasctl impact` and Spartan's gates walk this chain by reading table rows: the ID in a row's first cell is the row's own ID; every other ID in the row is a link.

## 3. Files atlasctl reads

**design/MODULES.md** — one table, these columns in this order:

```
| Module | Name | Rigour | Paths | Signals | Reason |
|---|---|---|---|---|---|
| M1 | Identity & roles | Critical | src/auth/**, src/users/** | auth, personal data | logins and permissions |
```
- Rigour: `Light`, `Standard` or `Critical` — Stark's proposal. The user confirms all at once with `atlas rigour --accept [M2=Critical …]`, or one with `atlas rigour M1 Critical --reason "…"`; the confirmed value wins.
- Paths: comma-separated globs relative to the code repo root (`**` allowed). Write `?` if not known yet.

**plan/PLAN.md** — the phase table (`| Phase | Goal … |`, first cell `P0 …`) and the work-package table with at least these columns: `| WP | Title | Phase | Module | REQs | Depends on | Size | Status |`. Status in PLAN.md is the *planned* state; Atlas records real progress as events and never edits PLAN.md.

A second optional table in PLAN.md, `| REQ | Evidence |`, lists requirements the audit found already built; gate G3 counts them as covered.

**design/DIAGRAMS.md** — optional, written by `/stark diagrams`. Atlas only exports it (`atlas export design/DIAGRAMS.md`); `verify.py <P>/design --diagrams` checks it: a header table with a `| Version | v1.0 — YYYY-MM-DD |` row, no template leftovers, balanced code fences, at least three Mermaid diagrams, each starting with its diagram type, and no internal IDs inside a diagram. Each diagram has a "What this picture shows" sentence above it.

**state/baseline.json** — the agreed scope, written by `atlasctl` only (`lead sent`, `signoff`, `cr approved`, `scope --baseline`):

```
{"kind": "sent" | "signoff", "date": "YYYY-MM-DD", "version": "<PRD version>",
 "rows": {"FR-001": {"h": "<hash of requirement, priority, status>", "text": "…", "priority": "Must", "status": "confirmed", "source": "[M01@00:08:15]"}, "BR-01": {…}}}
```
The rows are read from the PRD's requirement and rule tables (`| ID | Requirement or Rule | … | Priority | Source | Status |`). A difference is a row added, a row whose requirement, priority or status changed, or a row removed (a row whose status became `out of scope`, `rejected` or `removed` counts as removed). `cr approved` replaces only the rows that change request carries; the other writers replace them all.

**test/TEST-PLAN.md** — one `## P# — <phase name>` section per phase (Atlas looks for that heading), each with a table with `| TC | Covers | Module | Level | Type | Steps / expectation | Status |`, Covers listing AC/REQ IDs.

## 4. Events

`atlas begin` and `atlas finish` log the routine events. An agent calls `atlas event` itself only for the rows marked *agent* below. `atlasctl` is the only writer of the log.

```
python3 <lib>/atlasctl.py event <type> --actor <agent> --summary "<one line>" [--refs ID,ID] [--data '<json>']
```

| When | Type |
|---|---|
| Starting / finishing a run | `stage.started` / `stage.finished` — logged by `begin` / `finish` |
| A document's version changes | `doc.version` — logged by `finish` from the `| Version | v0.3 … |` row in the document's header table |
| Evidence moves a work package | `wp.inferred` — logged by reconcile |
| A gate passes | `gate.passed` — logged automatically |
| A note is left or handled | `note.added` / `note.closed` |
| Client approved something | `atlasctl signoff` (records the event and takes a snapshot) |
| A decision was agreed | `atlas decision "…"` (*agent*) |
| A report was sent to the client | `report.sent` (*agent*, only when the user confirms it was sent) |
| A security review was done | `review.security` (*agent*: Spartan) |
| A possible client is recorded; something worth keeping happened | `lead.created` · `lead.note` — logged by `atlas lead new` / `lead note` |
| The proposal went out; the follow-up date moved | `proposal.sent` (data: `what`, `followup`; also sets the baseline) · `lead.followup` (data: `on`) |
| The client said yes or no | `lead.won` · `lead.lost` (data: `reason`) |
| The PRD differs from the baseline | `scope.changed` (data: `added`, `changed`, `removed`, `key`) — logged by status, once per distinct set of differences |
| The PRD was accepted as the new baseline | `scope.baseline` (data: `reason`) — logged by `atlas scope --baseline` |
| A project detail was corrected | `project.updated` (data: `key`, `old`, `new`) — logged by `atlas set` |
| Client or design files were taken in | `sources.added` (data: `count`, `to`) — logged by `atlas intake` and `atlas start --files` |

Stage names: `define`, `design`, `plan`, `build`, `test`, `release`, `handover` (see `pipeline.md`).

## 5. Rules for every agent

1. **Never guess.** Unclear → ask the user (batched). What only the client can answer → a note to Alice (`atlas note --to alice …`), who puts it in QUESTIONS.md.
2. **Proportion.** Scale depth to the module's rigour level (`rigour.md`) and the project size class.
3. **Privacy.** Never put client names, people, figures or anything confidential into web searches or URLs.
4. **No secrets** in any file. Credentials stay in the user's environment.
5. **Finish with `atlas finish <agent>`.** It runs your check script and refuses to close the run while it fails.
6. **Report briefly**: what changed, what needs the user, the suggested next step.
7. **Every document has a header table with a `| Version | v1.0 — YYYY-MM-DD |` row.** `finish` reads it.
