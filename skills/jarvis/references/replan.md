# Re-plan

For `/jarvis plan` when PLAN.md exists (the design changed, a change request, a question was answered, or the brief says `CHANGED UPSTREAM`), and `/jarvis plan next` (detail the next phase).

1. **What is true now:** `atlas pack jarvis` — every live REQ with `UNPLANNED` where no work package covers it, and the *Real progress* line (`WP-03=done · WP-04=in-progress …`). Progress is Atlas's, inferred from branches, pull requests and commits; never copy it into PLAN.md's Status column.
2. **What changed:** the brief's `CHANGED UPSTREAM` line names the REQs and criteria added, changed or removed since the plan was built. For a change request, `atlas impact <FR-… or REQ-…>` lists the affected work packages.
3. **Change only what is affected:**
   - new REQs → `python3 <skill>/scripts/plan_seed.py <P>` proposes rows for the unplanned ones, numbered after the last work package; merge, name and phase them (new IDs — never reuse one);
   - a changed REQ in a package Atlas shows as done → a new package for the difference; never re-scope finished work;
   - a removed REQ → take it out of the REQs cell; a package left empty becomes `deferred`;
   - an answered open question → its `blocked` packages become `todo`, with their detail adjusted.
4. **`plan next`:** write full detail blocks for the next phase (`references/planning.md` §3; `atlas pack jarvis --module M#` for the criteria) and propose parallel rounds (`references/briefs.md`).
5. Bump the `| Version |` row, add a changelog row, then `atlas finish jarvis`.
