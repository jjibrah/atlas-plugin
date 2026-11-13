# Handover pack (`/alice handover`)

After the last phase is released. `atlas begin alice --stage handover` has run. Everything comes from evidence; anything it does not settle is a question for the user.

1. `atlas handover-data` prints compact JSON: `phases` and `released` (a phase not released → say what is left and stop, unless the user insists), `work_packages[]` (`state`, `confidence`), `change_requests`, `questions_open`, `milestones[]` (sign-offs, releases, decisions, updates sent).
2. Read only what the pack needs. From the PRD: integrations; rows that are `deferred`, `rejected` or `out of scope`; decisions; open risks. For how it runs: `P/design/OVERVIEW.md` if it exists, otherwise the deployment and operations part of `P/design/TECHNICAL.md`.
3. Ask the user in one batch: support contact, hours and channel, support period, and who owns each account where the evidence does not show it. Never invent these.
4. Write `P/reports/HANDOVER.md` from `templates/HANDOVER.md`: the internal record, with IDs and evidence.
   - Delivered = released phases. Not delivered = deferred, rejected or open items, each with its reason (decision or change request).
   - Operation: where it runs, backups, routine tasks. Summarise and link the design documents.
   - Accounts and integrations: every outside service, who owns the account and who holds the credentials. **Never write a password, key or token.**
   - Known limitations: from the deferred and rejected rows, open client questions and open risks.
5. Write `P/reports/HANDOVER-CLIENT.md` from `templates/HANDOVER-CLIENT.md`. It is derived from the internal file and adds nothing: plain words, the proposal's vocabulary, no IDs, phases as "Phase 1 — <what they got>".
6. `alice.py check-client P/reports/HANDOVER-CLIENT.md` and fix every FAIL. Show both files to the user.
7. When they approve: `atlas finish alice --stage handover` (it repeats the check, closes the stage and saves), then `atlas export reports/HANDOVER-CLIENT.md`. Never export the internal file.
8. Only when the user confirms it was sent: `atlas event report.sent --actor alice --summary "Handover pack sent to <role>"`.
