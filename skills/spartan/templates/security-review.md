# Security review — {{M#}} {{module name}} — {{YYYY-MM-DD}}

Phase: {{P#}} · Rigour: Critical · Reviewer: Spartan (read-only) · Repos: {{name @ short sha}}
Scope: changes to {{module Paths}} since {{last review date | first review}} — {{N}} commits, {{N}} files, {{N}} changed lines{{; reviewed in N parts by sub-folder: …}}.

## Summary
{{One or two sentences: overall verdict, number of findings by severity, whether anything blocks release.}}

| Blocker | High | Medium | Low |
|---|---|---|---|
| {{0}} | {{0}} | {{0}} | {{0}} |

## Findings

| # | Severity | Area | Evidence (path:line) | Problem | Fix | Status |
|---|---|---|---|---|---|---|
| 1 | {{High}} | {{Authorisation}} | `{{src/orders/api.ts:42}}` | {{…}} | {{…}} | open |

## Checked, nothing found
{{Areas from the checklist that were checked and are fine, one line each. Areas not applicable, with why.}}

## Questions for the user
{{Things that need intent clarified — not findings.}}

## Decision
{{"No blocking findings" | "User accepted findings #… because …" | "Blocked until #… fixed"}}
