# Client updates and the handover pack

Both are written from evidence only: `atlasctl handover-data` (JSON), the PRD, the proposal, and for the handover the design summary. Nothing is inferred; anything the evidence does not settle is an unclear point for the user.

## Reading handover-data

| Field | Use |
|---|---|
| `project` | name, client, author for the header |
| `phases`, `released` | which phases exist and which were released (with dates) |
| `work_packages[]` | `state` (todo / in-progress / done / deferred / blocked) and `confidence` |
| `change_requests` | scope changes: opened, approved, rejected, done |
| `questions_open` | how many client questions are still open (details in QUESTIONS.md) |
| `milestones[]` | sign-offs, releases, decisions, previous `report.sent` events (the last one dates "since the last update") |

**Confidence decides what you may call done:**

| Confidence | Say |
|---|---|
| `verified` (tests / CI pass) | done |
| `likely` (code exists and matches) | done |
| `claimed` (only recorded, no code evidence) | in progress — never "done" |

If a phase was released (`released`), everything in it is done for the client, whatever its confidence.

## Translating into the client's words

- Never show WP, REQ, AC, FR, M#, P#, CR, G# or any other ID. Map each work package to what it gives the client, using the proposal's wording (its *Scope of work* and *How we will deliver it* sections are the dictionary).
- Phases are "Phase 1 — <what they get>".
- Several work packages that make one visible feature become one line.
- Internal-only work (set-up, refactoring, test tooling) is not mentioned unless it changes something for them.
- A change request becomes "You asked us to … — agreed / we are looking at it / not going ahead", with what it means for the phases. No prices unless the user tells you to include them.
- "What we need from you" comes from open questions in QUESTIONS.md ("Needed before we start" first), sign-offs or tests we are waiting for, and accounts or data the proposal said they would provide.

## Client update — rules

1. One or two pages. The reader is the owner or manager.
2. Sections from `templates/CLIENT-UPDATE.md`: in short · done since the last update · next · what we need from you · changes to scope · phases.
3. "Since the last update" = since the last `report.sent` milestone; the first update covers everything since sign-off.
4. Run `alice.py check-client <file>` and fix every FAIL. Read it once as the client would.

## Handover — rules

1. Write two files: `reports/HANDOVER.md` (internal, with IDs and evidence) and `reports/HANDOVER-CLIENT.md` (for the client, plain words). The client file is derived from the internal one and adds nothing.
2. Delivered = released phases. Not delivered = deferred, rejected or open items, each with its reason (decision or CR).
3. Operation comes from `design/OVERVIEW.md` (or a short summary of `design/TECHNICAL.md`): where it runs, backups, routine tasks. Summarise; link the design documents in the internal file.
4. Accounts and integrations: list every outside service in PRD §13 and the design, who owns the account, and who holds the credentials. **Never write a password, key or token** — only who holds it.
5. Support contacts, hours and support period: ask the user. Never invent them.
6. Known limitations: from PRD rows that are `deferred`, `rejected` or `out of scope`, open client questions, and open risks.
