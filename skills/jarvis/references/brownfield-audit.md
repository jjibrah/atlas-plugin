# Existing codebases — mapping and auditing

Use this when the project already has code. Stark has already **mapped** it for the design (`<P>/design/_work/codebase.md`); Jarvis **audits** it so every requirement has a proven status and the plan covers only the real gaps.

Auditing is read-only. Do not change application code, and do not write anything into the code repository.

**Find the repository:** `<P>/atlas.json` → `repos[]` (a `path` if linked on this device); otherwise ask the user for the local path.

## 1–2. Start from Stark's map → `<P>/plan/_work/codebase.md`

Read `<P>/design/_work/codebase.md`. Add only what the audit and the plan need, in `<P>/plan/_work/codebase.md` (keep it under ~150 lines):

- **How to run and test**: commands, required services, known failing tests (the baseline).
- **Branch and commit conventions** already in use, and the base branch.
- **Paths that disagree with MODULES.md** — tell the user; Stark updates MODULES.md (`/stark update`).

## 3. Audit each requirement

Work module by module, Critical modules first and most carefully. For large systems use one subagent per module, each given: the module's requirement slice (`python3 <skill>/../stark/scripts/register.py slice <P>/design <M#> --out <P>/plan/_work/slices`), the two codebase maps, the module spec, and the rules below; each writes `<P>/plan/audit/mNN-<name>.md` and replies with counts only. Spot-check a sample of their `done` verdicts yourself.

| Status | Meaning |
|---|---|
| `done` | Implemented end to end — data, logic, interface, permission — including the limits and edge cases the requirement states. |
| `partial` | Some layers exist; say exactly what is missing (no UI, no validation, no permission check, not wired, no test). |
| `missing` | No implementation found. |
| `deviates` | Implemented, but differently from the requirement. State both sides. |
| `unclear` | Cannot be verified from code, or the requirement is ambiguous. Say why. |

**Evidence rules**

- Every status except `missing` cites evidence as `path/to/file.ext:line` — real paths, relative to the repository root. The verify script checks that each cited file and line exists.
- Do not trust names, comments, or the PRD's own "built" claims. Read the logic.
- Follow the whole path: screen → API → rule → data → permission check on the server.
- Check business rules against the exact values in the requirement (limits, rates, time-outs).
- Run the test suite if you can; note which requirements have passing tests. If it cannot run, say so.
- When unsure, choose `partial` or `unclear`, never `done`. Overstating progress is the costly error.

**Also record**

- **State machines**: states and transitions in the spec vs. in the code — missing and extra.
- **Extra scope**: behaviour in the code that no requirement asks for.
- **Risks noticed**: security holes, missing authorisation, secrets in code, absent validation, performance traps — with severity. Note them; do not fix them.

The register belongs to Stark: do **not** write statuses back into it. The audit files are the record of what is built; `register.py trace` reads them. Deviations that need the requirement changed go to Stark (or to Alice when the client must decide).

## 4. Output — keep it loadable

A single audit file for a large system grows to hundreds of kilobytes and no agent can use it. Split it:

```
<P>/plan/
├── AUDIT.md              ← summary for people: ≤ ~30 KB (templates/AUDIT.md)
└── audit/
    ├── m01-<module>.md   ← per-module evidence table (templates/audit-module.md)
    └── …
```

- `AUDIT.md`: summary, scorecard, what works, what is missing (grouped, in plain words), deviations, risks, open questions. Sections 1–5 must be readable by a non-technical person.
- `audit/<module>.md`: one row per requirement — status, evidence, gap. Keep cells short; long explanations go in a note below the table.
- The **completion plan is not in the audit** — it goes in `PLAN.md` as work packages covering every `partial`, `missing`, and (after a decision) `deviates` requirement; `done` requirements go in the `WP-00` baseline row (`planning.md`). Deviations are settled first: for each, either the code changes or the requirement does — ask the user; the requirement side is Stark's (or Alice's) to change.

## 5. Verify

```bash
python3 <skill>/scripts/verify.py <P>/plan --stage audit --repo <repository root>
```

It checks that every requirement has an audit row, that statuses are valid, and that every evidence path and line number exists in the repository.

## 6. Re-auditing after work

When work packages finish, update only the affected rows in `audit/<module>.md` from the merged code and refresh the scorecard in AUDIT.md. A full re-audit is only needed after large unplanned changes (Atlas reports those as unmatched commits or drift).
