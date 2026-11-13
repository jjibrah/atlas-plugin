# {{M# Module name}} — Module Spec

> Part of [TECHNICAL.md](../TECHNICAL.md). **Read the sections its "How to load this blueprint" table lists for every task first** (stack and conventions, permissions, shared data model{{, and §5.x for the shared lifecycle this module uses}}). This file is complete for work inside this module.

| | |
|---|---|
| Purpose | {{one sentence}} |
| Rigour | {{Light / Standard / Critical}} — see [MODULES.md](../MODULES.md) |
| Status | {{Planned / Partial / Built — one line on what exists today}} |
| Depends on | {{M1 Identity, M2 Catalog}} |
| Used by | {{M6 Admin dashboard}} |
| Requirements | {{REQ-040–REQ-071}} ({{N}}) · upstream {{FR-010–FR-018}} |
| Code location | {{`backend/orders/`, `frontend/src/orders/` — same globs as MODULES.md → Paths}} |

<!-- TEMPLATE NOTE — delete before finishing. File name: technical/mNN-<name>.md (m01-identity.md) — gate G2 finds the
module's spec by that name. Depth follows rigour: Light → §3 use cases and §12 acceptance criteria (drop the rest with
"None — Light module."); Standard → + §1, §2, §4, §5, §6, §7, §8 where they apply; Critical → everything, including
§9 errors & edge cases, §10 failure & rollback and §11 threat notes and audit trail. -->

## 1. Entities owned by this module

```mermaid
erDiagram
```

### 1.1 {{Entity}} {{(Built / Planned)}}
| Field | Type | Constraints | Notes / REQ |
|---|---|---|---|

## 2. State machines

```mermaid
stateDiagram-v2
```

| From | Event / trigger | Actor | Guard | To | Side effects | REQ |
|---|---|---|---|---|---|---|

## 3. Use cases
| UC | Actor | Main flow | Alternates / errors | REQ |
|---|---|---|---|---|

## 4. Business rules
| # | Rule | REQ / BR |
|---|---|---|

## 5. API / interfaces
| Method & path | Auth (roles) | Request | Response | Errors | REQ |
|---|---|---|---|---|---|

Events emitted / consumed: {{`order.paid` → consumed by M7 Reports}}
Functions other modules may call: {{`orders.get_for_customer(id)` — never query this module's tables directly}}

## 6. Screens / dashboards
| Screen | Platform | Roles | Shows / actions | Data from modules | REQ |
|---|---|---|---|---|---|

## 7. Notifications & jobs
| Trigger | Channel / schedule | Recipient | Content | REQ |
|---|---|---|---|---|

## 8. Key flows
```mermaid
sequenceDiagram
```

## 9. Errors & edge cases
| Situation | Behaviour (status code, message, state) | REQ |
|---|---|---|

## 10. Failure & rollback
| Step or dependency | If it fails | Rollback / retry / compensation | What the user sees |
|---|---|---|---|

## 11. Threat notes & audit trail
| Threat / abuse case | Who could do it | Mitigation | REQ |
|---|---|---|---|

Audit trail: {{actions logged with who / what / when / before-after; who can read the log; retention}}

## 12. Acceptance criteria
<!-- TEMPLATE NOTE — delete before finishing. The one home of this module's acceptance criteria. Write AC-NEW; afterwards
`register.py number-ac <D>` gives global sequential IDs. Every row cites its REQ; work packages and tests cite the AC IDs. -->
| AC | REQ | Given / when / then |
|---|---|---|
| AC-NEW | {{REQ-…}} | {{Given …, when …, then …}} |

## 13. Open questions & assumptions affecting this module
{{IDs only, each with at most one line on the impact here — e.g. "OQ-3: decides whether `expires_at` is needed." Full text is in DECISIONS.md.}}
