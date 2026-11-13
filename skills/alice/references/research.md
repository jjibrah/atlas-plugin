# Research

Research fills what the client could not tell us: how comparable businesses solve this, what the third-party services they mentioned can actually do, and which rules apply. It turns a list of complaints into a credible proposal.

## Confidentiality — non-negotiable

Search queries leave the machine. **Never put the client's name, people's names, phone numbers, figures, or anything confidential from the meetings into a search query or a fetched URL.** Search generically: industry + country + topic.

- ✅ `dental clinic appointment reminder SMS no-show reduction`
- ✅ `Kenya Data Protection Act health data requirements`
- ✅ `Africa's Talking SMS API delivery reports pricing`
- ❌ `Bright Smile Dental Nairobi booking system`

## What to research

Do the areas that apply; skip the rest. Spend effort where the money or the risk is.

| Area | Goes into | Questions to answer |
|---|---|---|
| **The client's requirements, in context** | PRD §8–§9, proposals | What do systems for this kind of business normally include? Which of those did the client not mention but will need? What is unusual about their way of working? |
| **Proposals** | PRD §8.4, PROPOSAL §6.2 | What proven practices would fix their pain points better than copying their current process? (e.g. automatic reminders cut no-shows; deposits at booking.) |
| **Integrations** | PRD §13 | For each service mentioned or needed: what it supports, its limits, how pricing works (not exact prices unless public and current), what account or approval the client needs, local availability. |
| **Regulations** | PRD §15 — **internal only** | Data protection, tax / e-invoicing, sector rules for this business in this country. What each means for the system. Flag anything that needs a lawyer. |

Named competitor products are not researched unless the user asks. But when the client asks *us* something ("should we buy a till?", "can it work with our accounting software?"), research the product category generically and answer it in the PRD and, in plain words, as a suggestion in the proposal.

## Recording it

- Each source used gets an `RS-##` row in PRD §21.3: title, URL, what it supports, date accessed. Draft notes can go in `_work/research.md`.
- In the PRD, cite it: `[RS-04]`. A requirement that exists only because of research is `proposed` or `to confirm` — never `confirmed`.
- Prefer primary sources: the vendor's own documentation, the regulator's or government's site, the text of the law. Blogs only for industry practice.
- State uncertainty. If sources disagree or are old, say so. Do not present research as legal advice.
- Research never decides what the client wants. Where it changes their options or obligations, it becomes a proposal or a question — in the proposal it reaches the client in plain words through *Our suggestions* or *What we need from you*, never as a regulations section.
- If web search is not available, say so in the PRD and the run summary, and list the research still to do as internal action items.

## When to research

- **First run:** after digesting the material and before writing the PRD, for every area that applies.
- **Later runs:** only for topics that are new or changed (a newly mentioned integration, a new user group, a new country).
- Keep it proportionate: a small internal tool needs a few sources; a regulated, payment-handling system needs many more.
