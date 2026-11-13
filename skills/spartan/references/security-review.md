# Security review checklist (Critical modules)

Read-only review of the changes touching a Critical module's Paths since its last review (`spartan.py changes`). Proportionate: check what the diff touches; skip sections that cannot apply and say so in one line. Every finding needs **path:line evidence** — no evidence, no finding (write it as a question instead).

Severity:
- **Blocker** — exploitable now or loses/leaks money or personal data; must be fixed before release.
- **High** — likely problem under realistic conditions; fix before release unless the user accepts the risk in writing.
- **Medium** — weakens defences; fix in the next phase.
- **Low / note** — hygiene.

## 1. Authentication and sessions
- New endpoints/screens require login unless explicitly public. Session/token expiry, logout invalidates.
- Password/OTP/reset flows: rate limited, no user enumeration in messages.
- Webhooks/callbacks verify signatures; timing-safe comparison.

## 2. Authorisation
- Every read/write checks the caller's role **and** ownership of the object (no "id from the URL trusted as is").
- Admin-only actions enforced on the server, not only hidden in the UI. Default deny.
- Multi-tenant: every query scoped to the tenant.

## 3. Input validation and injection
- SQL built with parameters/ORM, never string concatenation. Same for shell, LDAP, NoSQL, file paths.
- Output encoded for HTML (XSS); no `dangerouslySetInnerHTML`/`v-html`/`|safe` on user data.
- Uploads: type/size checked, stored outside the web root, names not trusted. Redirect targets allow-listed. SSRF on any fetched URL.
- Server-side validation of amounts, quantities, enums (client values never trusted).

## 4. Secrets and configuration
- No keys, passwords, tokens or connection strings in code, tests, fixtures, docs or CI files. Read from environment/secret store.
- Debug modes, verbose errors and test backdoors off in production config. CORS not `*` with credentials.

## 5. Sensitive data handling and logging
- Personal/health/payment data: only the fields needed; encrypted where the spec says; access limited to roles in the spec.
- Logs, analytics and error reports do not contain passwords, tokens, card data or unnecessary personal data.
- Exports/downloads authorised and audited. Deletion/retention as specified.

## 6. Payments and money (where relevant)
- Amounts computed on the server from stored prices; currency and rounding explicit.
- Idempotency keys on charge/refund/payout; webhook handlers idempotent and ordered-safe.
- Payment state machine: no path to "paid" without the provider's confirmation; refunds cannot exceed charges.

## 7. Error handling, failure and rollback
- Errors do not leak stack traces or internals to users.
- Multi-step operations are transactional or have compensation; partial failure leaves a consistent state (matches the spec's failure/rollback section).
- Timeouts and retries on outside calls; retries do not double-apply.
- Migrations reversible or backed up.

## 8. Dependencies
- New or upgraded packages: well-known, maintained, pinned in the lockfile; no typosquats. Note known critical advisories if a lockfile audit tool is available (`npm audit`, `pip-audit` — run only if the user agrees; read-only).

## 9. Audit trail
- Actions the spec lists as audited (money, permissions, personal-data access, deletes) write who/what/when (+ before/after where specified), and audit records cannot be edited by normal users.

## Report format — `<P>/reports/security-review-<M#>-<YYYY-MM-DD>.md`
Use `<skill>/templates/security-review.md`.
