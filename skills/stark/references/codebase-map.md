# Existing code — map it before designing (read-only)

Use this when the project has a code repository with application code beyond scaffolding (source folders, a package manifest with real dependencies, migrations, tests). Stark **reads** the code to fit the design to what exists and to fill `MODULES.md → Paths`. It never changes the code, and it does not judge what is *done* — that is Jarvis's audit, with `path:line` evidence.

## 1. Find the repository

- `<P>/atlas.json` → `repos[]` lists the linked repositories (`name`, `url`, and `path` when it was linked on this device). `atlasctl status --json` also works for the project's state.
- If only a URL is listed, or nothing is, ask the user for the local path (one question). If they have none yet, the system is greenfield for design purposes — Paths stay `?`.
- Read with your file tools and `git -C <repo> ls-files`, `git -C <repo> log --oneline -20`. Never write, commit, install or run migrations there.

## 2. Write `<D>/_work/codebase.md` (≤ ~200 lines; an index, not a description)

- **Stack in use** — languages, frameworks, database, hosting, auth, key services; versions that matter.
- **Layout** — top-level folders and what lives where: routes, models, migrations, jobs, screens, tests.
- **Module ↔ paths** — for each planned module, the folders/files that implement it today, as globs (these go straight into `MODULES.md → Paths`). Files that belong to no module: list them; they are a hint that a module is missing or that the code has extra scope.
- **Conventions in force** — naming, error format, API style, migration numbering, how permissions are checked.
- **What exists vs. the PRD** — a short list per module: *exists*, *partly exists*, *not found* — from a quick read, clearly labelled as a first impression for Jarvis to verify.
- **Binding project rules** found in `CLAUDE.md` / `AGENTS.md` / contributor guides (copy them; do not edit those files).

## 3. Consequences for the design

- The **stack and conventions are fixed** by the code. TECHNICAL.md §1 documents them; it does not choose new ones. Propose a change only when a requirement forces it, as a decision record (`AD-#`) with the reason.
- Use the code's real names (tables, routes, modules). A PRD name that differs from the code is noted in the glossary, not silently renamed.
- Tag spec elements **Exists / Partial / Planned** so an implementer knows whether they extend or create.
- Module boundaries should follow the code's real seams where they are sensible; when they are not, say so in the module's Reason and in a decision record.
