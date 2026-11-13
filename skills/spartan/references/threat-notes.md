# Threat notes — STRIDE-lite prompts (for Stark, read by Spartan)

Use for every **Critical** module (G2 checks the module spec mentions threats and failure/rollback). Optional for Standard modules with an outside integration. Light modules: skip.

Write threat notes as a short table in the module spec, under a heading containing "Threat notes":

| Threat | Where | Mitigation | AC |
|---|---|---|---|
| Someone uses another customer's order id | GET /orders/{id} | Check the order belongs to the caller | AC-0xx |

Only list threats that apply. Each mitigation should become an acceptance criterion so Sentinel can test it. Unsure whether something applies → ask the user, don't guess.

## Prompts (answer the ones that apply)

**Spoofing (who is it?)**
- How does each role log in? Password rules, MFA for admins, session expiry, password reset abuse?
- Webhooks / callbacks from outside: is the signature verified?

**Tampering (can data be changed by the wrong party?)**
- Can a user change prices, totals, roles or ids sent from the browser/app? Server recomputes?
- Input that reaches SQL, shell, HTML, file paths, templates?

**Repudiation (can we prove who did what?)**
- Which actions need an audit trail (money, permissions, personal-data access, deletions)? Who/what/when/before/after.

**Information disclosure (what could leak?)**
- Personal/health/payment data: where stored, who can read it, is it in logs, exports, error messages, URLs?
- Can one customer/tenant see another's data (object-level authorisation)?

**Denial of service (can it be stopped or abused?)**
- Rate limits on login, sign-up, OTP, expensive searches, file uploads (size/type)?
- What happens when the outside service is down or slow (timeouts, retries, queue)?

**Elevation of privilege (can someone do more than allowed?)**
- Every endpoint/screen: which roles may use it? Default deny? Admin functions separated?

## Failure and rollback (always for Critical)
- Each step of a multi-step operation (payment → order → email): what if it fails halfway? Idempotency key? Compensation?
- Data changes: how are they undone (backup, reversible migration, feature flag)?

## Scale
- Critical with money/auth/health data: all six letters + failure/rollback (typically 5–12 rows).
- Critical for other reasons (complex state machine, migration): the letters that apply + failure/rollback (3–6 rows).
