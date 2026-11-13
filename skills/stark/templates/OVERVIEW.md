# {{Project name}} — System Overview

> A plain-language guide to what we're building, for the team and anyone joining it. For the full technical detail, see [TECHNICAL.md](TECHNICAL.md). The client-facing description of the work is Alice's proposal, not this file.

| | |
|---|---|
| Version | {{v1.0 — YYYY-MM-DD}} |
| System | {{Small / Medium / Large}} · {{new system / extends the existing system}} |

---

## 1. What we're building

{{2–4 sentences: what the system is, who it's for, and the problem it solves.}}

**Main goals**
- {{goal 1}}
- {{goal 2}}

**Not included in this version:** {{out-of-scope items, or "Nothing excluded so far."}}

## 2. Who uses it

| Who | What they do in the system |
|---|---|
| {{Customer}} | {{browses products, places and pays for orders, tracks delivery}} |

## 3. The parts of the system

{{1–2 sentences summary, e.g. "There are three apps that all share one central system."}}

```mermaid
flowchart LR
    %% {{people, the parts of the system, outside services}}
```

| Part | Who uses it | What it's for |
|---|---|---|
| {{Customer mobile app}} | {{Customers}} | {{…}} |

**Outside services we connect to:** {{payment provider for card/mobile payments, SMS for notifications…}}

## 4. How the main processes work

<!-- TEMPLATE NOTE — delete before finishing. 3–8 of the most important processes: one-line summary, numbered steps, optional simple diagram. -->

### 4.1 {{Placing an order}}
{{One-sentence summary.}}

1. {{Customer adds items and pays.}}
2. {{…}}

```mermaid
stateDiagram-v2
```

## 5. Build order — what comes first

{{1–2 sentences on the approach, e.g. "We build the foundations first, then the booking journey, then the reports that depend on it." The phases and their dates are in the build plan (PLAN.md, written next).}}

```mermaid
flowchart LR
    %% {{foundations --> core journey --> reporting; plain words, ≤ 12 nodes}}
```

**Parts that need the most care:** {{the Critical modules in plain words — e.g. payments and patient records — and why}}

## 6. Keeping it safe, fast, and easy to use

- **Security:** {{e.g. only finance staff can see salary data; every sensitive change is logged}}
- **Speed & growth:** {{e.g. designed for up to 5,000 users at launch}}
- **Ease of use:** {{e.g. works on phones; available in English and Swahili}}

## 7. Questions we need answered

<!-- TEMPLATE NOTE — delete before finishing. List only the blocking questions (at most ~8), each answerable in one line.
The rest stay in the technical documents. -->

| # | Question | Why it matters | What we will assume if unanswered |
|---|---|---|---|
| {{OQ-1}} | {{…}} | {{…}} | {{…}} |

**Things we've assumed (please confirm):** {{the 3–6 assumptions with the biggest impact, in plain words}}

**More detail:** {{the full list of decisions and questions is in DECISIONS.md — or "in the technical blueprint" for a small system.}}

## 8. Glossary

| Term | Meaning |
|---|---|
| {{…}} | {{…}} |

## Changelog
| Version | Date | Change |
|---|---|---|
| v1.0 | {{YYYY-MM-DD}} | First version |
