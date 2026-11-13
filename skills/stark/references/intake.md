# Intake — the PRD and any extra design sources

Goal: every input Stark designs from is addressable, so every requirement can point at exactly where it came from, and nobody reopens a heavy document later.

## 1. The PRD (primary source) — read it natively

`<P>/discovery/PRD.md` is Alice's internal PRD and the team's source of truth. It is already markdown with stable IDs, so it is **not** converted or chunked. Read it once, start to finish, and note in the register's *Document roles & precedence* section: its version (header or changelog), its date, and whether the client signed it off (`atlasctl log --type signoff.recorded`).

Then get the mechanical summary:

```bash
python3 <skill>/scripts/register.py prd <D>
```

It lists the FR / BR rows by status:

| PRD status | What Stark does |
|---|---|
| `confirmed`, `proposed` | In scope. Becomes one or more REQs, each citing the FR in its Source cell. |
| `to confirm` | In scope but unsettled. Becomes REQs with Status `to confirm` and an open question (`OQ-#`) naming Alice's `Q-###` if she already asked it. Design so the answer is cheap to absorb. |
| `deferred`, `rejected`, `out of scope` | Skipped. Listed in TECHNICAL.md §2.5 *Out of scope* by FR ID so nobody builds them. |

What else in the PRD feeds the design (cite these in Source cells as `PRD §n` when there is no FR or BR ID): §3 People (roles), §4 current operations (workflows, practice), §10 business rules (`BR-##`), §11 data, reports and dashboards, §12 notifications, §13 integrations, §14 non-functional requirements, §15 regulations, §16 technical notes, §17 risks, §18 delivery phases (Jarvis reuses their names), §19–20 assumptions and decisions (cite Alice's `ASM-##` / `D-##`; never redefine them).

Never copy Alice's own source references (`[M02@00:14:32]`, `[d3-002]`) into the register — cite the FR or BR instead. The FR already carries its evidence.

## 2. Extra technical documents (optional)

The user may drop documents that are for the design only — an API spec of a system to integrate, a legacy database schema, an architecture standard, a hosting constraint — into `<P>/design/sources/`. If that folder has files, convert and chunk them with the shared converter (never write your own):

```bash
python3 <lib>/convert_docs.py <P>/design/sources <P>/design/_work/sources
```

If the inventory says a PDF was read as `text-only` or `NEEDS_DIRECT_READ`, the PDF engine is missing from the shared environment: tell the user to run `atlasctl setup` (or `atlasctl doctor`) once, then re-run. Use `--exclude <glob>` to skip files the user says are irrelevant.

What you get in `_work/sources/`: `INDEX.md` (read this, not the documents), `manifest.json`, and one folder per document with chunks `d1-001.md`, `d1-002.md`, … Chunk IDs in the register (`[d1-007]`) always refer to these design sources.

| Flag / status | What to do |
|---|---|
| `visual` chunk | Open each image the chunk lists (`media/…png`) and append a `### Visual notes` section describing it: screens, fields, states, arrows and labels, numbers. |
| `NEEDS_DIRECT_READ` | Read the original by page range (≤ 20 pages per read) and write the transcription into the chunk file the inventory names. |
| Broken table | Compare with the original page and fix the chunk file. |

After intake, the chunk files are the source — nothing later goes back to the originals.

## 3. Precedence

- The PRD defines the target system. A design source can add **technical** constraints (the payment provider's API, the legacy schema, a mandated stack) but never adds or changes business behaviour on its own.
- A design source that contradicts the PRD → log it under Contradictions; if it changes what the client gets, it is a question for the client (through Alice), not a decision for Stark.
- A newer PRD version beats an older one.

## 4. When the PRD or sources change (update mode)

- PRD: compare its changelog and FR table with the register (`register.py prd <D>` shows new uncited FRs; FRs whose status became out of scope show up as lint warnings).
- Design sources: re-run the converter. It marks each document `UNCHANGED`, `CHANGED`, `NEW` or `REMOVED`, keeps the previous chunks of a changed document in `dN.prev/`, and shows what changed with
  `python3 <lib>/convert_docs.py diff <P>/design/_work/sources dN.prev dN`.
- Old requirements keep their source pointers; add the new FR or chunk next to them when a requirement is confirmed or changed.
