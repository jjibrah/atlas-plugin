# Update and change requests

For a design that already exists: the PRD changed, questions were answered, or a change request reached design. IDs are permanent — REQ, AC, OQ, AD, ASM-T and module IDs are never renumbered or reused.

## Update (`/stark update`, or the brief says `CHANGED UPSTREAM`)

1. **Read only what changed:** `atlas pack stark --changed` — the FR / BR rows that are new, changed or removed since the last design run, and the REQs that cite them. Do not re-read the PRD tables. (No earlier run recorded → `register.py prd <D>` lists the FRs no REQ cites yet.) Design sources: re-run the converter; it marks each document UNCHANGED / CHANGED / NEW / REMOVED, and `convert_docs.py diff <D>/_work/sources dN.prev dN` shows the difference.
2. **Register:**
   - new FR → new rows (`register.py seed <D>` adds and numbers them; split as usual);
   - changed FR → edit the citing REQs in place; add the new source next to the old one;
   - removed or descoped FR → strike the row's ID `~~REQ-012~~ (removed v1.1: reason)` **and** set its Status to `out of scope (removed v1.1)` — gates count a row as live unless its Status says out of scope, deferred, rejected or removed.
3. **Answered questions** (a note from Alice, or the PRD now says): set the OQ's Status to `answered`, add the answer and date, and update every place that relied on the default. Close the note: `atlas note-done N-## --reply "…" --from stark`.
4. **Rigour:** re-check the signals of each affected module. A new risk signal raises the level — tell the user and confirm with `atlas rigour M# <Level> --reason "…"`, then adjust that module's depth.
5. **Spec:** change only the affected sections (and the overview, if one exists); new criteria as `AC-NEW` → `register.py number-ac <D>`; remove citations of struck REQs; add a changelog row and bump the `| Version |` row.
6. `register.py trace <D>`, then `atlas finish stark`. If the plan exists, status will report it is behind the design — the next step is `/jarvis plan` (small track: update PLAN.md yourself, see small-track.md).

## Change request (`/stark cr CR-##`)

The brief lists the change request. `atlas impact <FR-… or REQ-…> --cr CR-##` prints every REQ, criterion, work package and test downstream. Do the Update steps restricted to those items; raise a module's rigour if the change adds a risk signal. Finish the same way.
