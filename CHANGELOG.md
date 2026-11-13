# Changelog

## 1.2.0

On record and in sync: what the client asked for is written down from the first conversation, and the project is told whenever it drifts from what was agreed. Existing projects keep working; no migration is needed.

**A front door**
- `atlas start "<client or project>" [--files <folder>]` goes from nothing to a project in one command. On a new device it sets up a projects folder at `~/AtlasProjects` by itself; the size starts as Small.
- `atlas set size|client|author|name <value>` corrects a detail later.
- Alice starts by herself: with no project she asks one question, the client's name, and carries on.

**Leads and the pipeline**
- `atlas lead new "<client>"`, `lead note`, `lead sent "Proposal v1.0" --followup +5d`, `lead followup`, `lead won`, `lead lost --reason`.
- `atlas pipeline` lists every client and project: where it is, days waiting, what needs you. A proposal with no reply by its follow-up date is on the attention list.

**Scope watch**
- `atlas signoff` and `atlas lead sent` freeze the PRD's requirement and rule rows as the baseline: what was agreed.
- `atlas status` reports when the PRD no longer matches it. `atlas scope` shows what was added, changed or removed, with the wording before and after, the meeting moment it came from and what it touches downstream.
- Someone decides: `atlas scope --cr` opens a change request; `atlas cr approved CR-##` moves the baseline; `atlas cr rejected CR-## --note …` leaves Alice a note to put the PRD back; `atlas scope --baseline "<why>"` accepts the PRD as it is.
- After a new meeting Alice still updates the PRD, then says in plain words what differs from what was agreed, quotes the moment the client said it and asks you to decide. Agreed scope never changes silently.

**Diagram pack**
- `/stark diagrams` writes `design/DIAGRAMS.md`: who uses the system and for what, the main workflows, who talks to whom, the information it keeps, the life of the main record and the parts of the system. Plain labels, one sentence above each picture saying what it shows, three or four pictures for a small project.
- `verify.py <design> --diagrams` checks it; `atlas export design/DIAGRAMS.md` makes the PDF with the diagrams drawn.
- Alice offers it once the client approves. The full design builds on the pack and keeps the two consistent.

**Alice speaks plain words**
- In chat she says "the requirements document", "the questions for the client", "the check before design"; no IDs or command names. The documents keep their IDs.
- Fewer questions, only those that change the outcome, each with a suggested answer.
- She proposes the project size in plain words, with the reason, and sets it.

**Guide**
- The guide gained photographs.

## 1.1.0

Easier to run and cheaper in tokens. Existing projects keep working; no migration is needed.

**Running a project**
- `/atlas go` does the next step, whichever agent it belongs to.
- Checks G1–G5 run by themselves when an agent finishes and on every status. Status lists only what is still open.
- Progress is inferred: a work package starts on its first matching commit, branch or pull request, and is done when the branch or pull request is merged, or a commit says so ("WP-07 done", "closes WP-07"). Rebased commits are counted once.
- Small projects use a shorter track: Stark writes the design and the plan in one run.
- Adopt existing work: `atlas new … --prd file.md` or `--start design|plan|build`.
- `atlas intake <files or folder>` adds client files from anywhere.
- `atlas rigour --accept` confirms every module's level at once.
- An `atlas` terminal command: `atlas status` outside a chat uses no tokens.
- Status no longer writes to the log or commits when nothing changed, and skips the network if the last scan was under ten minutes ago (`--fresh` forces one).

**Agents working together**
- `atlas begin <agent>` prints a short brief; `atlas finish <agent>` checks, logs, runs the check for the stage and saves, in one call.
- `atlas pack <agent>` prints only the rows an agent needs from earlier documents.
- Notes between agents (`atlas note --to alice …`), shown in the recipient's next brief.
- Status reports when the design has fallen behind the PRD, the plan behind the design, or the tests behind either.

**Per agent**
- Alice: short PRD template for small clients; `alice.py changed` so only affected proposal sections are rewritten; report, handover, sign-off and change requests load only when used.
- Stark: nine reference files merged into three; accepts a PRD it did not come from Alice; the overview is written on request.
- Jarvis: `plan_seed.py` proposes work-package rows; requirements already built are listed with evidence in place of a placeholder work package.
- Sentinel: `sentinel.py seed` creates one test row per acceptance criterion; `sentinel.py results` reads JUnit XML.
- Spartan: on demand, for explaining a failing check, waivers and security reviews.

**Sizes**
- Skill instructions: 71 KB → 35 KB in total. Skill descriptions (loaded in every session): about 700 words → about 260.

**Fixes**
- `publish` no longer copies source documents (for example an adopted client PRD) into the code repository.
- A work package with no CI was reported as "verified"; it is now "likely".
- Meeting IDs (`M01`) are no longer confused with module IDs (`M1`).

**Guide**
- The GitHub Pages guide is redesigned.

## 1.0.0

First release.
