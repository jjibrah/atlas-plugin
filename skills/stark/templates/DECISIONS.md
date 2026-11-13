# {{Project name}} — Technical Decisions & Open Questions

> What has been decided, what was assumed, and what still needs an answer — for the design. Referenced from the spec as `AD-#`, `ASM-T#`, `OQ-#`. Client-facing questions are not asked here: they go through Alice into `../discovery/QUESTIONS.md` (`Q-###`), and the OQ row names that Q.

**Updated:** {{YYYY-MM-DD}} · Open questions: {{N}} ({{N}} blocking) · Assumptions awaiting confirmation: {{N}}

## 1. Open questions

Blocking = a wrong guess would force rework of the data model, a state machine, an integration or the architecture. Gate G2 does not pass while a blocking question is open. Status: `open` · `asked (Q-###)` · `answered` · `resolved`. Answered questions stay in this table (IDs are permanent): set the Status, add the answer and the date to the Question cell, and update every place that relied on the default.

| ID | Question | Affects | Blocking | Recommended default | Owner | Status |
|---|---|---|---|---|---|---|
| OQ-1 | {{…}} | {{modules / REQs}} | {{yes}} | {{…}} | {{Client via Alice Q-0NN / Team}} | {{open}} |

## 2. Assumptions

Defaults chosen where the PRD was silent and the choice is cheap to change now. Please confirm.

| ID | Assumption | Affects | Confirm with | Status |
|---|---|---|---|---|
| ASM-T1 | {{…}} | {{…}} | {{…}} | {{unconfirmed / confirmed YYYY-MM-DD}} |

## 3. Contradictions in the sources

| # | One place says | Another says | Resolution |
|---|---|---|---|
| C-1 | {{quote, FR-… / [d1-004]}} | {{quote, source}} | {{settled by precedence → AD-# / open → OQ-#}} |

## 4. Decision records

### AD-1 — {{title}}
- **Context:** {{what forced a choice; requirements involved}}
- **Decision:** {{what we will do}}
- **Reason:** {{why this fits the size class, rigour and requirements}}
- **Alternatives rejected:** {{option — why not}}
- **Consequences:** {{what this makes easier, harder, or must be revisited}}

## Changelog
| Date | Change |
|---|---|
| {{YYYY-MM-DD}} | Created |
