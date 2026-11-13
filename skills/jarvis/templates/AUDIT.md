# {{Project name}} — Requirements Audit

> How much of the requirements (the register in `design/_work/requirements.md`) the current code really implements. Evidence for every requirement is in `audit/<module>.md`. The work needed to close the gaps is in [PLAN.md](PLAN.md), which also lists what is already built. Read-only: the audit never changes code.

| | |
|---|---|
| Version | {{v1.0 — YYYY-MM-DD}} |
| Code audited | {{repository}} · {{branch @ commit}} · tests: {{N passed / N failed / could not run}} |

## 1. Summary

{{5–8 plain sentences anyone can follow: how complete the system is, what works, what is missing, the biggest risks, and the recommended next step.}}

## 2. Scorecard

| Module | Requirements | Done | Partial | Missing | Deviates | Unclear | Complete |
|---|---|---|---|---|---|---|---|
| {{M1 Identity}} | {{26}} | | | | | | {{%}} |
| **Total** | | | | | | | **{{%}}** |

Complete % counts done as 1 and partial as ½. Evidence: [audit/](audit/).

## 3. What works today

{{By module, in plain words — capabilities a user can actually use.}}

## 4. What is missing or incomplete

{{By module, in plain words: the capability, what is absent, and what it means for users. Group requirements — do not list every ID here; the per-module files do that.}}

## 5. Where the code differs from the requirements

| # | Requirement says | Code does | Recommendation | Decision |
|---|---|---|---|---|
| {{REQ-…}} | {{…}} | {{…}} | {{change the code / update the requirement (Stark, or Alice if the client decides)}} | {{open / decided: AD-#}} |

## 6. State machines — specified vs. built

| Entity | Missing states / transitions | Extra states / transitions | Evidence |
|---|---|---|---|

## 7. Built but not required

| Feature | Where | Keep, document, or remove? |
|---|---|---|

## 8. Quality & security risks

| # | Severity | Risk | Where | Suggested fix |
|---|---|---|---|---|
| H1 | High | {{…}} | {{`path/file.ext:line`}} | {{…}} |

## 9. Next step

{{One paragraph: what to do first and why. The full completion plan — phases and work packages covering every partial, missing and deviating requirement — is in PLAN.md.}}

## 10. Questions for the client

| Question | For | What it blocks |
|---|---|---|
| {{…}} | {{the user / the client via Alice}} | |

## Changelog
| Version | Date | Change |
|---|---|---|
| v1.0 | {{YYYY-MM-DD}} | First audit |
