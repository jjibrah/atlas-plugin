# Changelog

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
