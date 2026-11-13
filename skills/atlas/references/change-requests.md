# Change requests

The client changes scope after sign-off. A change that is already in the PRD (status says the PRD no longer matches what was signed) starts in `references/leads-scope.md`: `atlas scope --cr` opens the change request with its rows attached; continue here at step 4.

1. `atlas cr open "<what changes, citing FR/REQ IDs if known>" --by "<who asked>"` → `CR-##`.
2. Find what it touches (ask the user if unclear), then `atlas impact <FR-…> [REQ-…] --cr CR-##`. It lists every REQ, acceptance criterion, work package and test downstream.
3. Tell the user the impact in plain words. They decide: `atlas cr approved CR-##` or `atlas cr rejected CR-## --note "…"`.
4. When approved, the agents pick it up in order. Each one sees the change request in its `atlas begin` brief, and Atlas's status reports which documents are now behind:
   1. **Alice** updates the PRD and records the decision; the proposal changes only if scope or phases do.
   2. **Stark** updates only the affected REQs and modules (`/stark update`); a new risk signal raises the module's rigour.
   3. **Jarvis** re-plans only the affected work packages (`/jarvis plan`).
   4. **Sentinel** updates only the affected tests.
5. When status no longer reports anything behind: `atlas cr done CR-##`.
