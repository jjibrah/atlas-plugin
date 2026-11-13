# Writing the three documents

Three readers, three documents. All three must agree.

| | PRD.md | PROPOSAL.md | QUESTIONS.md |
|---|---|---|---|
| Reader | Our team: PM, engineers, coding agents | The client: owner, managers | The client |
| Purpose | Complete source of truth for building | Show we understood; agree the scope of work | Get decisions and missing facts |
| Tone | Precise, detailed, technical where useful | Warm, plain, confident | Polite, short, easy to answer |
| Tags and IDs | Everywhere | None | Q-IDs only |
| Regulations, risks, internal views | Yes | No | No |
| Timeline, price | No | No — phases only | No |

## PRD.md — detailed and traceable

1. **Detail is the point.** This is the knowledge base. Capture workflows step by step, numbers, exceptions, the client's exact terms. When in doubt, include it — with its tag.
2. **Every factual statement has a provenance tag.** A reader must always be able to tell *client said* from *we propose* from *we assumed*:
   - `[M02@00:14:32]` / `[M02]` — said in a meeting
   - `[d3-002]` — from a client document (chunk ID)
   - `[U-03]` — clarified by our team (the user)
   - `[D-05]` — agreed decision (including answered questions)
   - `[P-04]` — our proposal · `[RS-03]` — research · `[ASM-02]` — assumption the user approved · `[Q-007]` — waiting on the client
3. **Requirement statuses are honest.**
   - `confirmed` only with evidence: a meeting, a client document, a decision, or an answered clarification from our team.
   - Our ideas are `proposed` until the client accepts them (then cite the decision). Things the recommended solution needs but nobody said (sign-in, a product list) cite the **core** proposal and are `proposed` until the client accepts the proposal.
   - Anything pending a question or clarification is `to confirm`. Nothing is inferred: if you are not sure, ask (SKILL.md *Asking the user*).
   The check script enforces this.
4. **One requirement, one testable statement.** "The system sends an SMS reminder 24 hours before each appointment" — not "reminders should be good".
5. **IDs are permanent.** Get the next free ID from `alice.py next`. Never renumber, never reuse. A dropped requirement stays with status `rejected` or `out of scope` and the reason.
6. **Write sections that do not apply as "None identified yet."** so readers know they were considered.
7. **Technical notes (§16) are a view, not a design.** Likely architecture, the hard parts, integration risk. The detailed design comes later (Stark, in `design/`).
8. **Mermaid diagrams** for the current workflows that matter and the solution overview. Node IDs without spaces or hyphens; quote labels with punctuation.
9. **Keep the machine-read structure** (atlasctl and gate G1 read it): FR tables keep the columns `ID | Requirement | Role | Priority | Source | Status`; the regulations section stays `## 15. Regulations and compliance`; the header keeps `| Version | v0.3 — YYYY-MM-DD |`. Every new version gets a changelog row naming its trigger (a meeting, client answers, `CR-04`).

## PROPOSAL.md — the scope of work, in plain language

1. **Write for a busy business owner.** Short paragraphs, their words, no jargon: "the system texts the patient a day before", not "an SMS notification is triggered via the gateway API".
2. **Start with them, not us.** Their business, their day, their problems, then our solution. They should feel understood before they are sold to.
3. **Scope is explicit.** What is included, what is not, what we suggest (clearly labelled as a suggestion for their decision), and what we need from them.
4. **Phases only** — what they get in each phase and what they can do at the end. No durations, no prices.
5. **Distil, never add.** Every claim in the proposal must be in the PRD. Our **core** proposals are the recommended solution and belong in the main sections, presented as our recommended approach. **Optional** proposals appear only under *Our suggestions* until the client accepts them.
6. **No internal material:** no source tags, no requirement IDs, no regulations section, no risks about the client, no opinions about people.
7. **Length:** usually 4–10 pages. If it is longer, it is too detailed — the detail lives in the PRD.
8. Show the author (atlas.json `author`; STATE.md if atlas.json has none) in the header.

## QUESTIONS.md — easy to answer

1. **Ask only what changes what we build** or what we need to proceed. Not curiosity, not things the documents already answer.
2. **One question per row**, answerable in a line. Offer *our suggestion* so the client can just reply "agree".
3. **Say why we ask** in one plain sentence — what it changes.
4. **Group by topic**; "Needed before we start" first.
5. **Where people disagreed**, say so neutrally: "In our meetings we heard both A and B — which should the system follow?" Never name who said what if that could cause friction.
6. Plain words, no internal IDs or tags in the text. Q-IDs are permanent.
7. **Keep the structure atlasctl reads:** the three sections `## Needed before we start`, `## Can be answered later`, `## Already answered`; every question row starts `| Q-…` and its **last** cell is the status (`open`, `answered`, `withdrawn`); open-question tables keep the empty **Your answer** column so the exported PDF can be filled in.
8. Typical size: 5–20 questions. More than ~25 means you are asking things you should decide or research.
