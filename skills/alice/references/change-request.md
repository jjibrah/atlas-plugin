# Change request

The brief lists an approved change request ("Change requests: CR-02 (approved): …"). Atlas opened it and the user approved it. Alice goes first; Stark, Jarvis and Sentinel follow.

1. `atlas show CR-02` gives its history; `atlas impact <FR-…>` lists what a requirement touches downstream. Unclear what the client wants → ask the user. Only the client knows → QUESTIONS.md.
2. **PRD, new version.** Change only the affected requirement and rule rows.
   - A dropped requirement keeps its row and ID, with status `rejected` or `out of scope` and the reason.
   - A new requirement gets a new ID (`alice.py next P FR`) citing the decision.
   - Add a decision `D-##` describing the change and citing `CR-02`, and a changelog row "Triggered by CR-02".
   - A change that came out of a meeting (opened with `atlas scope --cr`) already has its rows updated: add only the decision and the changelog row.
3. `atlas decision "D-09: <the change> (CR-02)" --by "<who asked>" --actor alice`
4. **Proposal.** `alice.py changed P` lists the changed rows and the proposal sections they touch. If the scope or the phases the client reads have changed, rewrite only those sections and raise the proposal's version. If not: `alice.py changed P --mark`.
5. `alice.py check P` and fix every FAIL. Then `atlas finish alice --stage none`.
6. Tell the user what changed, whether the proposal should be sent again (`atlas export discovery/PROPOSAL.md` when they ask), and that Stark is next (`/stark update`). Atlas closes the change request once every document has caught up.
