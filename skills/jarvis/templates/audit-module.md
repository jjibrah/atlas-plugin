# Audit — {{M# Module name}}

> Evidence for [AUDIT.md](../AUDIT.md). Spec: {{[mNN-name.md](../../design/technical/mNN-name.md) / ../../design/TECHNICAL.md §6.x}}. Rigour: {{Light / Standard / Critical}}.

**Audited:** {{YYYY-MM-DD}} · **Result:** {{N}} done · {{N}} partial · {{N}} missing · {{N}} deviates · {{N}} unclear

| REQ | Status | Evidence | Gap / notes |
|---|---|---|---|
| REQ-… | done | `backend/orders/service.py:88` | |
| REQ-… | partial | `backend/orders/api.py:41` | No server-side permission check; no test |
| REQ-… | missing | | |
| REQ-… | deviates | `frontend/src/checkout/Pay.tsx:120` | Requirement: 3 attempts. Code: unlimited. See note 1 |

Status is one of: `done` · `partial` · `missing` · `deviates` · `unclear`. Every status except `missing` needs at least one `path:line`, relative to the code repository root.

## Notes

1. {{Longer explanations referenced from the table.}}

## State machine check

| Entity | Specified | Built | Difference |
|---|---|---|---|

## Risks noticed in this module

| Severity | Risk | Where |
|---|---|---|
