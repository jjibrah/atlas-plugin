# Writing the three documents

Three readers, three documents. All three must agree.

| | PRD.md | PROPOSAL.md | QUESTIONS.md |
|---|---|---|---|
| Reader | Our team: PM, engineers, coding agents | The client: owner, managers | The client |
| Purpose | Complete source of truth for building | Show we understood; agree the scope | Get decisions and missing facts |
| Tone | Precise, detailed, technical where useful | Warm, plain, confident | Polite, short, easy to answer |
| Tags, IDs, regulations, risks | Yes | None | Q-numbers only |

`alice.py check P` (run by `atlas finish alice`) enforces the structure: tags, statuses, table columns, header counts, the version row, no internal material in client documents.

## PRD.md — detailed and traceable

Use the template `alice.py init` named: `PRD-small.md` for a Small project, `PRD.md` otherwise. Order of work: how they work today and the pain points first; then goals, scope, the solution with our proposals, and the functional requirements by area.

1. **Detail is the point.** Workflows step by step, numbers, exceptions, the client's exact terms. When in doubt include it, with its tag. Scale to the client: a three-shop business gets short sections and few diagrams.
2. **A reader can always tell *client said* from *we propose* from *we assumed*.** Statuses are honest:
   - `confirmed` only with evidence: a meeting, a client document, a decision, or a clarification our team answered.
   - Our ideas are `proposed` until the client accepts them (then cite the decision). What the recommended solution needs but nobody said (sign-in, a product list) cites the **core** proposal and stays `proposed` until the proposal is accepted.
   - Anything waiting on a question or clarification is `to confirm`. A Q-number exists only for points the user sent to the client.
3. **One requirement, one testable statement.** "The system sends an SMS reminder 24 hours before each appointment", not "reminders should be good".
4. **A dropped requirement keeps its row**, with status `rejected` or `out of scope` and the reason. Rows are never deleted or renumbered.
5. **A part that does not apply says "None identified."** so readers know it was considered. Regulations are always considered.
6. **Technical notes are a view, not a design.** Likely architecture, the hard parts, integration risk. Stark writes the design.
7. **Mermaid diagrams** only for the workflows that matter and the solution overview. Node IDs without spaces or hyphens; quote labels that contain punctuation.
8. **Every new version** gets a changelog row naming its trigger (a meeting, client answers, `CR-04`), and the header counts are brought up to date.

## Clarifications

Every unclear point you asked the user is a `U-##` row in *Clarifications from our team*:

- **answered** → answer and date; cite `[U-##]` where used (it counts as client evidence);
- **ask the client** → status `sent to client (Q-###)` and a row in QUESTIONS.md; what depends on it stays `to confirm`, citing the Q;
- **suggestion accepted** → answered, plus an assumption `ASM-##` citing the U;
- **could not ask** → `pending`; what depends on it stays `to confirm`, citing `[U-##]`.

## Applying client answers

For each answered question (step 4 found them):

1. QUESTIONS.md: move the row to *Already answered* with the date and status `answered`.
2. PRD: add a decision `D-##` citing the question. Update everything that waited on it: `to confirm` → `confirmed` or `rejected`; assumptions likewise; proposals `accepted`, `partly accepted` (say which part) or `rejected`.
3. Record it: `atlas decision "D-07: <decision> (answer to Q-003)" --by "<client role>" --actor alice`.
4. If the question came from another agent's note, tell that agent: `atlas note --to stark "Q-003 answered: <answer> (D-07)" --from alice`.

## QUESTIONS.md — easy to answer

1. **Ask only what changes what we build** or what we need in order to proceed. Not curiosity, not what the documents already answer.
2. **One question per row**, answerable in a line. Offer *our suggestion* so the client can reply "agree". Say **why we ask** in one plain sentence.
3. **Group by topic**, "Needed before we start" first: only what truly blocks the design.
4. **Where people disagreed**, say so neutrally: "In our meetings we heard both A and B. Which should the system follow?" Never name who said what if it could cause friction.
5. Keep the three sections, the empty **Your answer** column, and **Status as the last column** (`open`, `answered`, `withdrawn`): Atlas counts open questions from it. Q-numbers never change.
6. Typical size: 5–20 questions. More than about 25 means you are asking things you should decide or research.

## PROPOSAL.md — the scope of work, in plain language

1. **Write for a busy business owner.** Short paragraphs, their words: "the system texts the patient a day before", not "an SMS notification is triggered via the gateway".
2. **Start with them, not us.** Their business, their day, their problems, then our solution.
3. **Scope is explicit:** what is included, what is not, what we suggest (labelled as a suggestion for their decision) and what we need from them.
4. **Phases only:** what they get in each phase and what they can do at the end. No durations, no prices.
5. **Distil, never add.** Every claim must be in the PRD. Our **core** proposals are the recommended solution and belong in the main sections. **Optional** proposals appear only under *Our suggestions* until the client accepts them.
6. **No internal material:** no tags, no requirement IDs, no regulations section, no risks about the client, no opinions about people.
7. **Length:** usually 4–10 pages; a small client gets less. Show the author in the header.

**Updating an existing proposal.** Never rewrite it whole. `alice.py changed P` lists the requirements, rules, pain points and proposals that are new, changed or removed since this proposal version was written, each with the section it belongs in. Rewrite only those sections (and the phases table if a phase changed), then raise the version. If nothing the client reads has changed: `alice.py changed P --mark`.
