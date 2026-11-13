# Threat notes — questions by signal

<!-- Read through `spartan.py threats <signal> …`: it prints "How to write them", the sections named and "Always".
     Each `## ` heading below is a signal name from MODULES.md; the script looks sections up by heading. -->

## How to write them

For every **Critical** module (gate G2 checks that its spec mentions threats and failure/rollback); optional for a Standard module with an outside integration; skip for Light. Write a short table in the module spec under a heading containing "Threat notes":

| Threat | Where | Mitigation | AC |
|---|---|---|---|
| Someone uses another customer's order id | GET /orders/{id} | Check the order belongs to the caller | AC-0xx |

List only threats that apply: 3–6 rows, or 5–12 with money, logins or health data. Each mitigation becomes an acceptance criterion so Sentinel can test it. Unsure whether one applies → ask the user, don't guess.

## money
- Can a user change a price, total, quantity or discount sent from the browser or app? Does the server recompute from stored prices? Currency and rounding explicit?
- Charge, refund, payout: is there an idempotency key? Can a refund exceed the charge? Is there any path to "paid" without the provider's confirmation?
- Provider webhooks: signature verified, handler safe to run twice and out of order?
- Which money actions need an audit trail (who, what, when, before and after)?

## personal data
- Where is personal, health or payment data stored, and which roles can read it?
- Does it appear in logs, exports, error messages, URLs or analytics?
- Can one customer or tenant see another's data (ownership checked on every read and write)?
- Exports and downloads: authorised and audited? Retention and deletion as specified? Encrypted where the spec says?

## auth
- How does each role log in? Password rules, MFA for admins, session expiry, logout?
- Password reset and one-time codes: rate limited, no hint whether an account exists?
- Every endpoint and screen: which roles may use it? Default deny, enforced on the server? Admin functions separated?
- Can a user raise their own role, or act on an id they do not own? Are permission changes audited?

## integration
- Incoming calls (webhooks, callbacks): signature verified, replays rejected?
- The outside service is down or slow: timeouts, retries, queue? Can a retry apply the same thing twice?
- What data leaves the system — is it the minimum? Where are the credentials kept (never in code) and how are they rotated?
- Does input from the outside system reach SQL, a shell, HTML, file paths or templates? Are URLs fetched on a user's behalf restricted?

## states
- Which transitions are allowed, and by which role? Can a state be skipped or re-entered by replaying a request?
- Two people act on the same record at once: who wins?
- A transition fails halfway: what state is left, and how is it resumed or undone?
- Are state changes audited (who, when, from, to)?

## regulation
- Which rule applies (the PRD's regulations section), and which data or action does it cover?
- What must be provable later: consent, access log, retention, deletion on request?
- Who may see regulated data, and where must it be hosted?
- Anything that needs legal advice is a question for the client (`atlas note --to alice …`), never a guess.

## migration
- Is source data validated before loading? What happens to rows that fail (a rejected list, never silently dropped)?
- Rehearsed on a copy of real data, with record counts and totals compared?
- Can it be run again safely, and undone (backup taken, restore tested)?
- Personal data in migration files and temporary copies: where kept, when deleted?
- Cut-over: what happens to changes made in the old system while the migration runs?

## always
- Each step of a multi-step operation (for example payment → order → email): what if it fails halfway? Idempotency key? Compensation?
- How is a data change undone (backup, reversible migration, feature flag)?
- Abuse: rate limits on login, sign-up, expensive searches and uploads (size, type)?
