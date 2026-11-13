# Parallel rounds and agent briefs

Read this only for `/jarvis brief …` or when proposing parallel rounds in `/jarvis plan next`. Briefs are written to `<P>/plan/briefs/` and published to the code repository with the rest of the plan by `atlasctl publish`.

## 1. Lanes and rounds

Two work packages can run at the same time when neither depends on the other **and** they touch different files. A group of such packages is a **round**; each agent's share is a **lane**.

- Lanes in one round own **disjoint files**. If two lanes need the same file, either order them or give the file to one lane and have the other hand over its change.
- Shared resources are assigned up front: migration numbers, shared config, lock files, a shared test database.
- Cap the number of parallel lanes at what the project can absorb (default 2–3; ask the user if the project rules do not say). More lanes mean more merge work, not more speed.
- One orchestrator owns sequencing, merging, the full test run, and the hand-back.

## 2. Writing a brief

A brief is the complete instruction for one round of work. It **points** to the blueprint rather than repeating it. Use `templates/brief.md`. Before writing:

1. Read the code repository's `CLAUDE.md` / `AGENTS.md` (read-only) and copy its binding rules into *Standing rules* (test commands, formatting, spend or safety limits, shared-environment rules, commit conventions). Invent none. Never write those files — `atlasctl publish` maintains the blueprint pointer in them.
2. Confirm with `atlasctl status --json` that every work package in the round has its dependencies done.
3. For an existing codebase, open the files each lane will touch and list them under *Owns* — real paths, checked to exist, inside the module's MODULES.md Paths. State the base branch or commit, and each lane's branch `WP-##-short-title`.
4. Record the test baseline (which tests fail before the work starts) so new failures are attributable.
5. Check lanes for file overlap. Fix the split before writing, not after.
6. If the work packages in the round have no detail block yet, write those first (`/jarvis plan next`).

Every brief ends with a hand-back: what changed, test results against the baseline, decisions needed, anything deferred. Agents do **not** edit PLAN.md or `docs/blueprint/`; Atlas picks progress up from the branches and commits, and the user runs `/atlas`.

Critical-module lanes include their review checkpoint in the acceptance list.

Save it as `<P>/plan/briefs/<phase>-<round>.md`.
