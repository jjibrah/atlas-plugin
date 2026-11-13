# Architecture & quality attributes — depth by size

Use the size class from Step 3 for the system as a whole. Cover each column cumulatively (Medium includes everything in Small; Large includes everything in Medium). **Then apply rigour per module:** a Critical module gets the Large column's security and reliability items that touch it (threat notes, failure modes, audit trail, idempotency, rollback) even in a Small system; a Light module needs nothing beyond the system's column. Write each item as a concrete decision, not a generic platitude: "Passwords hashed with argon2id" not "use secure password storage".

## Architecture choices

**Default to the simplest thing that meets the requirements.**

- Start from a monolith. Split out a separate service only if a requirement forces it (independent scaling of a hot path, different runtime, isolation for compliance, separate team ownership) — and write that reason down.
- Use a relational database (e.g. PostgreSQL) unless requirements clearly favour something else. Add a cache, queue, search engine, or object storage only when a specific requirement needs it — cite the REQ.
- Respect stated constraints (mandated stack, hosting, budget). If the sources say nothing about stack and it affects the design, recommend one with a short reason and list it as an assumption the user can override.
- Prefer managed services over self-hosted infrastructure for Small/Medium.

## Security

| Small | Medium (+) | Large (+) |
|---|---|---|
| Authentication method chosen (email+password, OTP, SSO) | Role-based access control matrix enforced server-side | Threat model (STRIDE-style table for each platform & integration) |
| Passwords hashed (argon2id/bcrypt); sessions/tokens with expiry | Audit log for sensitive actions (who, what, when) | Data classification (public / internal / confidential / restricted) per entity |
| HTTPS everywhere; secrets in env/secret manager, never in code | Rate limiting on auth & public endpoints | Encryption at rest for restricted data; key management |
| Input validation & output encoding (OWASP Top 10 basics) | PII inventory & minimisation; data retention rules | 2FA for privileged roles; least-privilege service accounts |
| Authorisation check on every endpoint | Secure file upload handling (type/size checks, private storage) | Compliance mapping (e.g. data protection law, PCI DSS, HIPAA) with responsibilities |
| | Dependency vulnerability scanning in CI | Webhook signature verification, idempotency keys for payments |
| | | Pen-test / security review before launch |

## Performance & scalability

| Small | Medium (+) | Large (+) |
|---|---|---|
| Indexes on foreign keys & common filters | Explicit targets (e.g. p95 API < 500 ms, page load < 2 s) | Capacity estimate (users, requests/sec, data growth per year) |
| Pagination on all lists | Background jobs for slow work (emails, exports, reports) | Caching strategy (what, where, invalidation) |
| | N+1 query avoidance noted for heavy screens | Horizontal scaling plan; stateless app servers |
| | File/media via object storage + CDN if user uploads | Read replicas / reporting database if analytics are heavy |
| | | Load test plan for critical flows |

## Reliability

| Small | Medium (+) | Large (+) |
|---|---|---|
| Daily automated DB backups | Restore tested; retry with backoff for integrations | Failure-mode table: each dependency → impact → mitigation |
| Basic error handling & user-facing error messages | Idempotent handlers for webhooks and payments | Availability target (e.g. 99.9%), RPO/RTO |
| | Transactions around multi-step state changes | Circuit breakers / graceful degradation for third parties |
| | | Disaster recovery plan; multi-AZ deployment |

## Observability & operations

| Small | Medium (+) | Large (+) |
|---|---|---|
| Error tracking (e.g. Sentry) | Structured logs; uptime monitoring & alerts | Metrics dashboards (business + technical), tracing across services |
| Environments: dev + production | Environments: dev, staging, production; CI/CD pipeline | On-call/runbooks for critical failures |
| | Feature flags if phased rollout needed | Zero-downtime deployments & DB migration strategy |

## Usability

| Small | Medium (+) | Large (+) |
|---|---|---|
| Responsive layout; clear empty/error/loading states | Accessibility (WCAG 2.1 AA basics: contrast, keyboard, labels) | Full accessibility review; localisation/i18n framework if multi-language |
| Confirmation on destructive actions | Role-tailored navigation (users only see what they can use) | Offline/poor-connectivity strategy if users are mobile/field-based |
| | Search & filters on large lists | Usability testing plan with real users per role |

## Over-engineering red flags (remove if found in a Small/Medium design)

- Microservices, Kubernetes, service mesh, event sourcing, CQRS without a cited requirement
- Separate databases per module
- Message brokers (Kafka/RabbitMQ) where a simple job queue or cron is enough
- Multi-region deployments without an availability requirement
- Custom auth instead of a proven library/provider
- GraphQL federation, plugin architectures, or "future-proof" abstractions nobody asked for
