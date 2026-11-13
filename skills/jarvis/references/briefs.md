# Briefs and parallel rounds

For `/jarvis brief <phase, round or WPs>`, and when proposing parallel rounds in `/jarvis plan next`. A brief is the complete instruction for one round of work; it points to the blueprint rather than repeating it. Written to `<P>/plan/briefs/<phase>-<round>.md` from `templates/brief.md`, and published to the code repository with the rest of the plan.

## Lanes and rounds

Two work packages can run at the same time when neither depends on the other **and** they touch different files. Such a group is a **round**; each agent's share is a **lane**.

- Lanes own disjoint files. If two need the same file, order them, or give the file to one lane.
- Assign shared resources up front: migration numbers, shared config, lock files, the test database.
- Cap the lanes at what the project can absorb (2–3 unless the user or the project rules say otherwise).
- One orchestrator owns sequencing, merging, the full test run and the hand-back.

## Before writing

1. Read the code repository's `CLAUDE.md` / `AGENTS.md` (read-only) and copy their binding rules into *Standing rules*. Invent none; never write those files.
2. `atlas pack jarvis` → the *Real progress* line: every dependency of the round must be done. If the packages have no detail block yet, write those first (`references/replan.md`).
3. Open the files each lane will touch and list them under *Owns* — real paths, inside the module's Paths. State the base branch or commit and each lane's branch `WP-##-short-title`.
4. Record the test baseline (what fails before the work starts) so new failures are attributable.
5. Check the lanes for file overlap before writing, not after.

## In every brief

- **Progress conventions** (keep the template's paragraph): branches and pull requests named `WP-##-short-title`, commits starting `WP-##:`; a package is done when its branch or pull request is merged, or a commit on the default branch says "WP-07 done" / "closes WP-07". Agents never edit PLAN.md or `docs/blueprint/`.
- Critical-module lanes list their review checkpoint among the acceptance items.
- A hand-back: what changed, test results against the baseline, decisions needed, anything deferred.

Then `python3 <skill>/scripts/verify.py <P>/plan`.
