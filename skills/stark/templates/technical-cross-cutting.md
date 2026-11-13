# Cross-cutting requirements

> Part of [TECHNICAL.md](../TECHNICAL.md). Non-functional, operational and legal requirements that apply across modules (module `X` in the register). Depth follows the size class and the highest rigour level among the modules it protects.

| | |
|---|---|
| Requirements | {{REQ-570–REQ-585}} ({{N}}) · upstream {{PRD §14, §15, FR-…}} |
| Applies to | {{all modules / list}} |

## 1. Security & privacy
{{authentication, authorisation model, data classification, encryption, audit logging; threat model table for Large systems or Critical modules}}

## 2. Performance & scalability
| Target | Value | Where it applies | REQ |
|---|---|---|---|
| {{p95 API latency}} | {{< 500 ms}} | {{…}} | |

{{capacity estimate, caching, background work}}

## 3. Reliability
| Dependency or job | If it fails | Mitigation | REQ |
|---|---|---|---|

{{backups and restore, availability target, recovery objectives}}

## 4. Observability & operations
{{logging, metrics, alerts, environments, deployment, runbooks}}

## 5. Usability & accessibility
{{responsive behaviour, accessibility level, languages, offline behaviour}}

## 6. Test strategy
{{what is unit / integration / end-to-end tested; fakes for third parties; test data; what tests must never call for real}}

## 7. Data migration & seed data
{{imports, cut-over steps, first admin, seed catalogues — or "None — new system with no prior data."}}

## 8. Compliance & legal
{{regulations from PRD §15, who is responsible for what, prerequisites before go-live — or "None stated."}}

## 9. Acceptance criteria
| AC | REQ | Given / when / then |
|---|---|---|
| AC-{{0NN}} | REQ-… | Given …, when …, then … |
