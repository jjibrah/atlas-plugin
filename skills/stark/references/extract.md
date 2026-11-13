# Extract — sources, register, size

Read at the Extract step. Afterwards nobody reopens the sources: everything the build needs is a row in `<D>/_work/requirements.md` that says where it came from.

## 1. Sources

| Source | How |
|---|---|
| Alice's PRD, `<P>/discovery/PRD.md` (has `FR-###` rows) | Read it once, natively — never chunked. `register.py prd <D>` lists its FR / BR rows by status. |
| Extra technical documents in `<D>/sources/` (API spec, legacy schema, standard) | `python3 <lib>/convert_docs.py <D>/sources <D>/_work/sources` (`<lib>` = `<skill>/../../lib`; `--exclude <glob>` skips files). Then read `_work/sources/INDEX.md` and the chunks, never the originals. Cite chunks as `[d1-007]`. |

Converter flags: `visual` chunk → open its images and append `### Visual notes`; `NEEDS_DIRECT_READ` → read the original (≤ 20 pages per read) into the chunk file named; PDF read as `text-only` → the user runs `atlas setup` once, then re-run.

| PRD status | What Stark does |
|---|---|
| `confirmed`, `proposed` | In scope: one or more REQs citing the FR. |
| `to confirm` | In scope, unsettled: REQs with Status `to confirm (OQ-#)` plus the open question; design so the answer is cheap to absorb. |
| `deferred`, `rejected`, `out of scope` | No live REQ. List by FR ID under *Out of scope* in TECHNICAL.md. |

The PRD's other sections feed the design too (roles, current operations, data, integrations, non-functional requirements, regulations). Where there is no FR or BR ID, cite `PRD §<number>`. Cite Alice's `D-##` and `ASM-##`, never redefine them, and never copy her meeting or chunk references (`[M02@00:14:32]`) — the FR carries its evidence.

**Precedence.** The PRD defines the target system; a design source adds technical constraints only, never business behaviour. A conflict is logged under Contradictions and, if it changes what the client gets, becomes a client question.

## 2. Register rows

`register.py seed <D>` adds one numbered row per in-scope FR and BR. Refine: split compound rows into atomic REQs (new rows with ID `NEW`, same Source), set Cat, add what the other PRD sections and the design sources imply. Most FRs map one to one — do not split for its own sake. Then `register.py number <D>`.

```markdown
| ID | Cat | Type | Requirement | Source | Priority | Module | Status |
|---|---|---|---|---|---|---|---|
| NEW | RULE | stated | A member may hold at most 3 active bookings. | FR-014, BR-03 | Must | | |
```

| Column | Rules (lint enforces the starred ones) |
|---|---|
| ID | ★ Write `NEW`; only `register.py number` issues `REQ-###`. Never renumber or reuse. |
| Cat | `FUNC` · `RULE` (rule, validation, calculation) · `DATA` · `UI` · `NOTIF` · `INT` (external system) · `SEC` · `PERF` · `OPS` (operations, legal) · `UX` |
| Type | `stated` — a source says it. `practice` — only current operations say it, no FR covers it: also list it as an assumption (`ASM-T#`). `derived` — written nowhere, but a stated requirement cannot work without it. ★ Derived stays under ~20 % of stated; an idea or improvement is an open question, not a requirement. |
| Requirement | ★ One atomic, testable sentence. Copy numbers, limits, deadlines, formulas and legal wording exactly; keep the source's own identifiers (endpoint codes, table names). |
| Source | ★ Mandatory. `FUNC RULE DATA UI NOTIF INT` rows cite `FR-###` and/or `BR-##`. `SEC PERF OPS UX` rows cite an FR/BR, or `PRD §n`, or a chunk `[d1-007]`. A derived row writes `derived from REQ-### (FR-###)`. Several sources: separate with `;`. ★ Cited FRs and chunks must exist. |
| Priority | The FR's (Must / Should / Could); blank if unstated. |
| Module | Blank until the Model step. |
| Status | Blank · `to confirm (OQ-#)` · `claimed` (a source says it is built; only Jarvis's audit proves it). `out of scope`, `deferred`, `rejected`, `removed` take a row out of the live set. Never `built` or `done`. |

- ★ Every in-scope FR is cited by at least one REQ (the same check as gate G2); business rules should be.
- ★ Design sources go chunk by chunk. Every chunk yields rows or gets a reason: `register.py ledger <D>` writes `_work/ledger.md`; set a `TODO` chunk's Status to `none` and give the Reason.
- A pricing table, permission grid or status table usually yields one requirement per row or cell. Duplicates across documents: one row, several sources.

## 3. The other register sections

`register.py init` creates the headings; keep their names. Fill only those the sources give content for: document roles · actors and roles · entities (normalise synonyms into the glossary) · states (any word implying a lifecycle, with its trigger) · workflows and exceptions · dashboards and reports · notifications · integrations · non-functional expectations (verbatim, even when vague) · constraints · existing data and migration · contradictions (quote both sides with their IDs) · out of scope · source ID map.

## 4. Open questions

```markdown
| ID | Question | Affects | Blocking | Recommended default | Owner | Status |
|---|---|---|---|---|---|---|
| OQ-1 | What happens to a paid order when the payment is reversed? | Orders, Payments | yes | Cancel and restock | Client via Alice | open |
```

- **Blocking** `yes` only when a wrong guess forces rework of the data model, a state machine, an integration or the architecture. Gate G2 fails while one is open (Standard and Critical).
- **Status:** `open` · `asked (N-##)` once the note to Alice is left · `answered` / `resolved`.
- Every question has a recommended default. Ask only what changes what gets built.

## 5. Size

The brief gives the size Atlas holds. Check it against the register — score each factor 0–2:

| Factor | 0 | 1 | 2 |
|---|---|---|---|
| User roles | 1–3 | 4–6 | 7+, or tenants |
| Platforms built separately | 1 | 2–3 | 4+ |
| Core entities | ≤ 10 | 11–25 | 26+ |
| Stateful workflows | 0–2 | 3–5 | 6+, or multi-level approvals |
| External integrations | 0–1 | 2–3 | 4+, or real-time two-way sync |
| Money | none | records amounts | takes payments, pays out, ledgers |
| Sensitive data | contact details | personal records as a side effect | regulated data is the core |
| Scale | one organisation | tens of thousands of users | 50k+, or an availability target |
| Real-time / heavy processing | reminders | background jobs, imports | live tracking, chat, offline sync |

0–5 **Small** · 6–11 **Medium** · 12–18 **Large**; on a boundary choose the smaller. Record the scores under *Sizing breakdown*. If the result differs from the brief, tell the user and let them decide — over-sizing is the common failure.

What a size means: Small — 3–6 modules, 25–50 KB delivered · Medium — 6–10 modules, 60–130 KB · Large — 10–16 modules. Cut on sight: more than ~8 open questions on a small system; monitoring or audit trails nobody asked for; a multi-step design grown from one sentence (ask instead).

## 6. Adopted PRD — no FR rows

The project started from a client-supplied PRD (`atlas new --prd`): the file is in `<D>/sources/` and `discovery/PRD.md` is missing or has no `FR-###` rows. There is no FR chain, so **the chunk ID is each requirement's Source**.

1. Convert: `python3 <lib>/convert_docs.py <D>/sources <D>/_work/sources`. `register.py prd <D>` lists the chunks.
2. `register.py seed <D>` proposes candidate rows per chunk (list items, "must / can / should" sentences), ID `NEW`, Source `[d1-004]`. A first pass only: read every chunk, then correct, split and delete rows, add what it missed, set Cat and Priority. Invent nothing — an unclear passage becomes an open question.
3. **Confirm with the user in one batch before numbering:** the candidates grouped by area (one line each), what you left out and why, your questions. Apply the corrections.
4. `register.py number <D>`, then `register.py ledger <D>` — a chunk with no requirements needs Status `none` and a reason in `_work/ledger.md`.
5. Continue as usual: lint and verify accept chunk-cited rows, and gate G2 has no FR coverage to check.

## Appendix — parallel extraction

Only when INDEX.md recommends it (sources over ~30,000 words) and you have subagents. Alice's PRD is never split.

1. Batch the chunks (6,000–10,000 words, adjacent chunks together); one subagent per batch, all at once. Brief: *"Read `<skill>/references/extract.md` §2–§4. Extract requirements from these chunks: … Write `<D>/_work/extract/<batch>.md`: a table with the register columns, ID `NEW`, the chunk ID in every Source cell; then any register section that applies under a `## ` heading with its exact name. Invent nothing. List chunks with no requirements and why. Reply with counts only."*
2. `register.py merge <D>` appends the rows with final IDs and gathers the other sections in `_work/findings.md`.
3. Consolidate yourself: merge duplicates (strike the higher ID: `~~REQ-###~~ (duplicate of REQ-###)`), normalise names, fold findings.md into the register and delete it, give empty chunks a ledger reason.
