# Client progress update (`/alice report`)

Written from evidence only. Anything the evidence does not settle is a question for the user, never a guess.

1. `atlas status` refreshes the evidence from the code. Then `atlas pack alice --report` prints about 40 lines: each phase with how many pieces of work are done, the current phase's items, what was recorded since the last update was sent, the open client questions and our next step.
2. Read `P/discovery/PROPOSAL.md` (its words are the dictionary) and the open rows of `P/discovery/QUESTIONS.md`.
3. Write `P/reports/client-update-YYYY-MM-DD.md` from `templates/CLIENT-UPDATE.md`. One or two pages; the reader is the owner or manager.
4. `alice.py check-client <that file>` and fix every FAIL. Read it once as the client would. Then `atlas finish alice --stage none` saves it.
5. Show it to the user. When they approve: `atlas export reports/client-update-YYYY-MM-DD.md`.
6. **Only when the user confirms it was sent:** `atlas event report.sent --actor alice --summary "Client update YYYY-MM-DD sent to <role>"`. The next update starts from this point.

## What may be called done

The pack has already applied the rule: an item it shows as `done` has evidence behind it, and everything in a phase marked `RELEASED` is done. `in progress`, `todo` and `blocked` are never "done", whatever anyone says. Never upgrade a status.

## In the client's words

- No internal IDs of any kind (the pack shows phases as `P1`; write "Phase 1 — <what they get>"). Name each item by what it gives the client, in the proposal's wording.
- Several pieces of work that make one visible feature are one line. Internal work (set-up, tooling) is left out unless it changes something for them.
- A change request becomes "You asked us to … — agreed / we are looking at it / not going ahead", with what it means for the phases. No prices unless the user says to include them.
- "What we need from you": the open questions ("needed before we start" first), sign-offs or tests we are waiting for, and accounts or data the proposal said they would provide.
- "Since the last update" is what the pack lists under that heading; the first update covers everything since sign-off.
