# Audit — what the existing code really implements

For `/jarvis audit`, and before planning whenever a linked repository (the brief's `Code (read-only)` line) holds application code and there is no current audit. The plan then covers only the real gaps. Read-only: never change the code or write anything into the repository. No local path → ask the user for it.

## 1. Prepare

Read Stark's map, `<P>/design/_work/codebase.md`. Add only what the audit and the plan need to `<P>/plan/_work/codebase.md` (≤ ~150 lines): how to run and test (commands, services, the tests that already fail — the baseline) · branch and commit conventions and the base branch · paths that disagree with MODULES.md (tell the user; `atlas note --to stark "…" --from jarvis`).

## 2. Audit each requirement

Module by module, Critical modules first and most carefully: `atlas pack jarvis --module M#` gives the module's REQs with their acceptance criteria. Large systems: one subagent per module, each given that pack, both codebase maps, the module spec and the rules below; it writes `<P>/plan/audit/mNN-<name>.md` (`templates/audit-module.md`) and replies with counts only. Spot-check a sample of their `done` verdicts.

| Status | Meaning |
|---|---|
| `done` | Implemented end to end — data, logic, interface, permission — including the limits and edge cases the requirement states |
| `partial` | Some layers exist; say exactly what is missing (no UI, no validation, no permission check, not wired, no test) |
| `missing` | No implementation found |
| `deviates` | Implemented differently from the requirement; state both sides |
| `unclear` | Cannot be verified from code, or the requirement is ambiguous; say why |

- Every status except `missing` cites evidence as `path/to/file.ext:line`, relative to the repository root. verify checks that each file and line exists.
- Do not trust names, comments or a PRD's "built" claims. Follow the whole path: screen → API → rule → data → permission check on the server. Check rules against the requirement's exact values.
- Run the test suite if you can and note which requirements have passing tests.
- Unsure → `partial` or `unclear`, never `done`. Overstating progress is the costly error.
- Also record: state machines specified vs built, behaviour no requirement asks for, and risks noticed (missing authorisation, secrets in code, absent validation) with severity. Note them; do not fix them.

The register is Stark's — write no status into it. A deviation is settled before planning: either the code changes (a work package) or the requirement does (ask the user; then a note to Stark, or to Alice when the client must decide).

## 3. Output

- `<P>/plan/audit/mNN-<name>.md` — one row per requirement: status, evidence, gap. Short cells; long explanations in a note below.
- `<P>/plan/AUDIT.md` (`templates/AUDIT.md`, ≤ ~30 KB) — summary, scorecard, what works, what is missing, deviations, risks. Sections 1–5 readable by a non-technical person.
- **PLAN.md** carries the consequences: every `done` requirement goes in its *Already built* table `| REQ | Evidence |` (a range per module pointing at the audit file is enough: `| REQ-001–REQ-012 | audit/m01-identity.md |`); everything else gets a work package. verify fails if a REQ listed there is not `done` in the audit.

```bash
python3 <skill>/scripts/verify.py <P>/plan --stage audit --repo <repository root>
```

## 4. Re-audit

When work packages finish, update only the affected rows from the merged code and refresh the scorecard. REQs delivered by a work package stay in that package — *Already built* is only for what existed before the plan. A full re-audit is needed only after large unplanned changes (Atlas reports those as unmatched commits).
