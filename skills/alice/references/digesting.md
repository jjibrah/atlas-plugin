# Digesting meetings and documents

The goal: capture everything the client told us, once, with a pointer back to the moment they said it — so the PRD can be written and updated without rereading transcripts.

## 1. Classify each source

Record every document in STATE.md → Sources with its kind:

| Kind | How to recognise it | What to do |
|---|---|---|
| meeting transcript | speaker turns, timestamps, conversational | Give it a meeting ID (`alice.py next` → M); write a digest |
| meeting notes | summary bullets written by someone after a meeting | Meeting ID and digest, as above (no timestamps — cite `[M03]`) |
| SOP / procedure | numbered steps, roles, forms | No digest; mine it straight into §4 workflows and §10 rules, citing chunks `[d2-003]` |
| client document | price lists, forms, spreadsheets, org charts, existing system screenshots | Mine for facts, data fields, volumes, rules; cite chunks |
| answers | the client's replies to QUESTIONS.md (a returned file, an email, notes) | Apply them — SKILL.md step 4 |
| other | unrelated or empty | Mark Processed `n/a — <reason>` |

Meeting IDs follow the meeting dates (M01 = earliest). A meeting added later that happened earlier still gets the next free ID — never renumber.

## 2. Reading a transcript

Transcripts are messy: crosstalk, filler, speech-recognition errors, the same point made three times. Read for substance:

- **Who is speaking matters.** Note each person's role the first time they appear. When the owner and a staff member disagree, record both — it is a question, not a fact.
- **Listen for workflows.** "First we… then she… and if that happens we…" is a workflow. Capture steps, people, tools, time taken, frequency, and the exceptions.
- **Listen for pain.** Complaints, workarounds ("we keep a separate book for that"), errors, delays, lost money or customers. Capture the impact in their terms and one short quote.
- **Listen for numbers.** Staff counts, branches, customers, transactions per day, prices, how long things take. Copy them exactly.
- **Separate requests from ideas.** "We need X" is a request. "Maybe it could…" is an idea to confirm. "Our competitor has X" is a hint, not a requirement.
- **Notice what is *not* said** — no mention of who approves refunds, what happens at month end, how they handle a sick receptionist. These become questions.
- **Speech-recognition errors and anything you are unsure you understood:** do not infer. Write it as heard, mark it `(unclear)`, and add it to STATE.md → *Unclear points for the user* with the timestamp. Never invent a name, number, product or meaning.
- **Commitments we made** in the meeting ("we'll send a proposal by Friday", "yes we can do WhatsApp") go under Action items and must be honoured or flagged.

## 3. Writing the digest

Use `templates/meeting-digest.md`, save as `_work/meetings/M01-<yyyy-mm-dd>-<topic>.md`.

- Every fact carries its tag: `[M01@00:14:32]` (transcript timestamp) or `[M01]` (notes without times).
- Keep the client's vocabulary. Their word for a thing becomes the PRD's word, recorded in the glossary.
- Capture every fact once, without filler. For a long meeting the digest is a fraction of the transcript; for a short call it can be longer than the transcript because of its headings — that is fine.

## 4. Contradictions across meetings and documents

- **The same decision-maker clearly changes their mind in a later meeting** ("actually, only Peter can change orders") → the later statement wins. Record it as a decision (D-) citing both moments.
- **Anything less clear-cut** — different people disagree, a document says one thing and a meeting another, or you cannot tell whether a later remark changes an earlier one → an unclear point for the user. The user answers it or sends it to the client. Until then the PRD shows both versions, marked `to confirm` citing the U- or Q-.
- **A document marks something superseded / removed / old version** → out of scope, never a requirement.

## 5. Large volumes

When `INDEX.md` recommends parallel work and you have subagents: one subagent per meeting or long document. Give each: the chunk file paths, its meeting ID, this file, and `templates/meeting-digest.md`. It writes the digest file and replies with only: number of pain points, requests, and unclear points. You then synthesise from the digests — never from the transcripts.
