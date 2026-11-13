# Small track — design and plan in one run

The brief said `track: small`: one pass, one pause, two documents — `<D>/TECHNICAL.md` (`templates/TECHNICAL-small.md`) and `<P>/plan/PLAN.md`. Open the other references only where a step names a section.

1. **Extract.** `register.py init <D>` · read the PRD once · `register.py seed <D>` · split compound rows (ID `NEW`, same Source), set Cat · `register.py number <D>`. No FR rows → extract.md §6. If the PRD clearly outgrows Small (payments, regulated data, ~40+ FRs), stop and tell the user.
2. **Model.** 3–6 modules by responsibility; `register.py assign <D> _work/modules.map` (`M1: REQ-001-REQ-006`); MODULES.md with proposed rigour (default Light; signals raise it); `register.py lint <D> --strict`.
3. **Checkpoint — the only pause.** One message: *module — proposed level — reason*, what you assumed, at most four blocking questions with defaults. Then `atlas rigour --accept [M2=Critical …]`.
4. **Write TECHNICAL.md.** One `### 5.x M# Name` section per module at its rigour (Critical: errors and edge cases, failure and rollback, threat notes, audit trail), `Depends on` in the module table, and `| AC-NEW | REQ-### | Given / when / then |` for every live REQ → `register.py number-ac <D>`. Decisions and open questions stay in this file; no DECISIONS.md, OVERVIEW.md or module files. Diagram syntax: write.md §3.
5. **Plan.** `python3 <skill>/../jarvis/scripts/plan_seed.py <P> --out <P>/plan/_work/seed.md` proposes the work-package rows. Copy `<skill>/../jarvis/templates/PLAN.md` to `<P>/plan/PLAN.md` and fill it:
   - the header row `| Version | v1.0 — YYYY-MM-DD |`;
   - two or three phases, each ending in something a person can see working (`P0` = the thinnest end-to-end path):
     ```
     | Phase | Goal — what can be demonstrated at the end | Work packages | Gate to start | Target | Status |
     | P0 Walking skeleton | A patient signs in and books a slot | WP-01–WP-02 | G3 passed | | todo |
     ```
   - the seed's rows merged into vertical slices, ordered, with real titles and phases — every live REQ in one REQs cell:
     ```
     | WP | Title | Phase | Module | REQs | Depends on | Size | Status |
     | WP-02 | Booking rules + review | P0 | M2 | REQ-004–REQ-006 | WP-01 | S | todo |
     ```
     Size `XS` `S` `M` (`L` only if it cannot be split). Status `todo`, `blocked` or `deferred` — never progress. A package touching a **Critical** module is XS/S/M and its title ends `+ review`. Light modules get 1–2 packages.
   - a detail block per package (Branch `WP-02-booking-rules`, Read, Do, Acceptance by `AC-###`). Delete unused template sections and every `{{placeholder}}`.
6. **Finish.** `register.py trace <D>`, then `atlas finish stark` — it verifies design and plan, closes both stages and runs G2 and G3.

Later changes (`/stark update`): update the design per update.md and the affected PLAN.md rows in the same run (new work gets new `WP-##` IDs); finish again.
