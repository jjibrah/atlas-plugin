# Research

Research fills what the client could not tell us: how comparable businesses solve this, what the outside services they mentioned can really do, and which rules apply. It informs proposals, integrations and regulations. It never decides what the client wants.

## Confidentiality — not negotiable

Search queries leave the machine. **Never put the client's name, people's names, phone numbers, figures or anything confidential from the meetings into a search query or a fetched URL.** Search generically: industry + country + topic.

- ✅ `dental clinic appointment reminder SMS no-show reduction`
- ✅ `Kenya Data Protection Act health data requirements`
- ❌ `Bright Smile Dental Nairobi booking system`

## What to research

Do the areas that apply and skip the rest. Spend effort where the money or the risk is: a small internal tool needs a few sources; a regulated system that handles payments needs many more.

| Area | Goes into the PRD's | Questions to answer |
|---|---|---|
| The requirements in context | solution, functional requirements | What do systems for this kind of business normally include? What did the client not mention but will need? What is unusual about how they work? |
| Proposals | proposals table | Which proven practices fix their pain points better than copying today's process (automatic reminders, deposits at booking)? |
| Integrations | integrations table | For each service mentioned or needed: what it supports, its limits, how pricing works, what account or approval the client needs, local availability. |
| Regulations | regulations section (**internal only**) | Data protection, tax and e-invoicing, sector rules for this business in this country, and what each means for the system. Flag anything that needs a lawyer. |

Named competitor products are researched only if the user asks. When the client asks *us* something ("should we buy a till?", "will it work with our accounting software?"), research the product category generically; answer in the PRD and, in plain words, as a suggestion in the proposal.

## Recording it

- Each source used gets an `RS-##` row in the PRD's research table: title, URL, what it supports, date accessed. Draft notes can go in `_work/research.md`.
- Cite it as `[RS-04]`. A requirement that exists only because of research is `proposed` or `to confirm`, never `confirmed`.
- Prefer primary sources: the vendor's own documentation, the regulator's site, the text of the law. Blogs only for industry practice.
- State uncertainty. If sources disagree or are old, say so. Research is not legal advice.
- Where research changes the client's options or obligations it becomes a proposal or a question. It reaches the client in plain words through *Our suggestions* or *What we need from you*, never as a regulations section.
- No web search available: say so in the PRD and the run summary, and list the research still to do as internal action items.
