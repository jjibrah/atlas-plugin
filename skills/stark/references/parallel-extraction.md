# Parallel extraction (large source sets)

Use only for large **extra design sources** (`design/_work/sources/INDEX.md` recommends it: more than ~30,000 words, or several documents totalling over ~12,000 words) and when your environment has subagents. The PRD itself is never split this way — you read it. You orchestrate; you never read the chunk files yourself, so your context stays free for design.

1. Group chunks into batches of roughly 6,000–10,000 words, keeping one document's adjacent chunks together.
2. Start one subagent per batch, all at once. If you can choose the model, a fast, inexpensive one is suitable. Give each this brief:

   > Read `<skill>/references/extraction-checklist.md`. Extract requirements from these chunk files: `<list of paths>`. Write your result to `<D>/_work/extract/<batch-name>.md`: first a table with the register columns and ID = `NEW` on every row, then any of these sections that apply, each under a `## ` heading with exactly this name — Actors & roles, Entities, States, Workflows, Dashboards & reports, Notifications, Integrations, Non-functional expectations, Constraints, Existing data & migration, Glossary, Contradictions, Open questions, Out of scope, Source ID map. Cite the chunk ID in every Source cell, plus the PRD `FR-###` it supports when the brief lists FRs. Invent nothing. List any chunk that has no requirements, with the reason. Read no other file. Reply with only: the number of requirements, the number of open questions, and any chunk you could not process.

3. When all have finished: `python3 <skill>/scripts/register.py merge <D>`. It appends every batch's rows to the register with final IDs and gathers the other sections into `_work/findings.md`.
4. **Consolidate** — this needs judgement, so you do it:
   - merge duplicate requirements (keep the lower ID; strike the other as `~~REQ-###~~ (duplicate of REQ-###)`);
   - normalise entity and role names across batches;
   - fold `_work/findings.md` into the register's sections, then delete it;
   - contradictions *between* batches surface here — log them.
5. For chunks reported as having no requirements, add them to `_work/ledger.md` with status `none` and the reason.
6. `python3 <skill>/scripts/verify.py <D> --stage extract`.
