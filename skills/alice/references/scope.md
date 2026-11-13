# The proposal, the agreed scope and changes to it

`atlas begin alice --stage none` has run (or you are at step 7 of the main run). Talk to the user in plain words throughout: "what was agreed", "a change to what was agreed", never IDs or command names.

## 1. The proposal went out

The user says the proposal was sent:

```
atlas lead sent "Proposal v0.1" --followup +5d
```

Use the proposal's real version, and the user's own date if they give one (`--followup 2026-11-20`). This records it, sets the reminder and **freezes the requirements as "what was agreed"**. Tell the user the reminder date and that from now on you will point out anything in a later meeting that differs from this proposal.

| The user says | Do |
|---|---|
| "I called them", "they emailed back" (no requirement in it) | `atlas lead note "<what happened>"` |
| "No answer yet, I chased them" | `atlas lead followup +5d` |
| "They said yes" (nothing in writing yet) | `atlas lead won`; the approval itself is `references/signoff.md` |
| "They are not going ahead" | Ask why, once. `atlas lead lost --reason "<why>"` |
| "Where are all our clients?" | `atlas pipeline`; relay it as a short list, what needs them first |

## 2. A new meeting after the scope was agreed

1. Run the main run as usual up to step 7. The PRD **is** updated from the meeting: each new or changed row carries the tag of the moment it was said, the version goes up, the changelog row names the meeting. Leave the proposal alone for now.
2. `atlas scope`. "In sync" → nothing agreed has changed; carry on with the main run. Otherwise it lists each difference: `ADDED`, `CHANGED` (`was:` the agreed wording, `now:` the new one) or `REMOVED`, with `from:` the source tag and `touches:` what is already designed or planned on top of it.
3. **Tell the user, in plain words, for each difference:** what was agreed, what the client says now, the moment they said it (date, who, their words, from the digest), and what it affects.

   > Compared with what Sunrise Bakery signed on 3 Nov, the 12 Nov meeting changes two things:
   > 1. **New:** home delivery. Mary, 12 Nov: "people keep asking if we can deliver". It is not in what was agreed.
   > 2. **Changed:** orders would close at 2pm; we agreed 4pm. Mary, 12 Nov: "the bakers need more time". The order form is already designed around 4pm.
   >
   > Shall we accept these as changes to what was agreed, or keep the agreed scope?

4. The user decides. Never decide for them, and never leave a difference unreported.

| Decision | Do |
|---|---|
| **Accept** | `atlas scope --cr "<short title>"` opens the change (`CR-##`). When both co-founders, and the client where it changes what they get or pay for, agree: `atlas cr approved CR-##`. Not agreed yet → leave it open; Atlas keeps showing it. Once approved, finish with `references/change-request.md` (the PRD rows are already updated: add the decision and the changelog row, then its steps 3–6) |
| **Keep what was agreed** | `atlas scope --cr "<short title>"`, then `atlas cr rejected CR-## --note "<why, who decided>"`, then §3 |
| **Some of each** | Put back the rows that are not accepted first (§3, steps 1–3) and record `atlas decision "Not accepted: <what> — <why>" --by "<who>" --actor alice`. Then `atlas scope` shows only the accepted ones: handle them as *Accept* |
| **Not a change of scope** (an open question got its answer, a wording fix) | Say so in one line; when the user agrees: `atlas scope --baseline "<why>"` |
| **Not signed yet** and the user agrees to the changes | Update the proposal (main run, step 10). When the new version is sent: `atlas lead sent "Proposal v0.2"` makes it the agreed scope |

Then `atlas finish alice` (or `--stage none` if you began that way).

## 3. Putting the PRD back

A change was not accepted: you just recorded it, or the brief shows a note from atlas ("CR-## was rejected … Put these requirements back").

1. `atlas scope` shows every row to restore:
   - `CHANGED` → set Requirement, Priority and Status back to exactly what the `was:` line shows, and take the declined meeting's tag out of its Source;
   - `REMOVED` → put the row back as the `was:` line shows;
   - `ADDED` → take the row out (it was never agreed). Write "FR-0## withdrawn, CR-## not accepted" in STATE.md's run log so the ID is never used again.
2. Keep the record: under *Out of scope* (or *Later*), one line saying what was asked and that it was not accepted, with its source tag.
3. Raise the PRD version; changelog row "Scope kept as agreed: change of <date> not accepted (CR-##)". Bring the header counts up to date.
4. `atlas scope` must say "In sync". Then `atlas note-done N-## --reply "PRD restored" --from alice` and `atlas finish alice --stage none`. If its check reports "Rows deleted from the PRD" for the row you withdrew: `alice.py changed P --mark`, and finish again.
5. Offer the user one sentence for the client: "We noted your request for home delivery. It is outside what we agreed, so we have left it out for now; we can look at it as a separate piece of work."
