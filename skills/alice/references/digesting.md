# Digesting meetings and documents

Capture everything the client told us, once, with a pointer back to the moment they said it, so the PRD can be written and updated without rereading transcripts. Only `NEW` and `CHANGED` files are read.

## 1. List and classify each source

Add every new file to STATE.md → Sources with its kind and Processed `no`:

| Kind | How to recognise it | What to do |
|---|---|---|
| meeting transcript | speaker turns, timestamps | Meeting ID (`alice.py next P M`) and a digest |
| meeting notes | summary bullets written after a meeting | Meeting ID and digest; no timestamps, cite `[M03]` |
| SOP / procedure | numbered steps, roles, forms | No digest; mined when writing the PRD (workflows, rules), citing chunks `[d2-003]` |
| client document | price lists, forms, spreadsheets, org charts, screenshots | Mined for facts, fields, volumes, rules; cite chunks |
| answers | the client's replies to QUESTIONS.md | Applied when writing (`writing.md` → *Applying client answers*) |
| other | unrelated or empty | Processed `n/a — <reason>` |

Meeting IDs are issued in the order meetings are processed and never renumbered, even when an earlier meeting arrives later.

**Changed and awkward files** (the converter says which):
- `CHANGED`: set Processed back to `no` and read the diff it offers, not the whole file.
- `visual` chunks: open the page image and describe it under `### Visual notes` in the chunk. `needs-read`: read the original and write it into the chunk. Then run the reindex command the converter printed.
- "PDF quality is reduced": tell the user to run `atlas setup`, then convert again.

## 2. Reading a transcript

Transcripts are messy: crosstalk, filler, speech-recognition errors, the same point made three times. Read for substance.

- **Who is speaking matters.** Note each person's role the first time they appear. When the owner and a staff member disagree, record both: it is a question, not a fact.
- **Workflows.** "First we… then she… and if that happens we…": capture steps, people, tools, time taken, frequency and the exceptions.
- **Pain.** Complaints, workarounds ("we keep a separate book for that"), errors, delays, lost money or customers. Capture the impact in their terms and one short quote.
- **Numbers.** Staff, branches, customers, transactions per day, prices, how long things take. Copy them exactly.
- **Requests versus ideas.** "We need X" is a request. "Maybe it could…" is an idea to confirm. "Our competitor has X" is a hint, not a requirement.
- **What is not said:** who approves refunds, what happens at month end, who covers for a sick receptionist. These become questions.
- **Anything you are unsure you heard or understood:** do not infer. Write it as heard, mark it `(unclear)` and add it to STATE.md → *Unclear points for the user* with the timestamp. Never invent a name, number, product or meaning.
- **Commitments we made** ("we'll send a proposal by Friday", "yes, we can do WhatsApp") go under Action items and must be honoured or flagged.

## 3. Writing the digest

Use `templates/meeting-digest.md`; save as `_work/meetings/M01-<yyyy-mm-dd>-<topic>.md`.

- Every fact carries its tag: `[M01@00:14:32]` (transcript timestamp) or `[M01]` (notes without times).
- Keep the client's vocabulary. Their word for a thing becomes the PRD's word.
- Capture every fact once, without filler.

## 4. Contradictions across meetings and documents

- **The same decision-maker clearly changes their mind later** ("actually, only Peter can change orders") → the later statement wins. Record a decision (`D-##`) citing both moments.
- **Anything less clear-cut** (different people disagree, a document says one thing and a meeting another, or you cannot tell whether a later remark changes an earlier one) → an unclear point for the user. Until it is settled the PRD shows both versions, marked `to confirm` citing the U- or Q-.
- **A document marks something superseded, removed or old** → out of scope, never a requirement.

## 5. Large volumes

When `INDEX.md` recommends parallel work and you have subagents: one subagent per meeting or long document. Give each the chunk file paths, its meeting ID, this file and `templates/meeting-digest.md`. It writes the digest file and replies with only the number of pain points, requests and unclear points. You then work from the digests.
