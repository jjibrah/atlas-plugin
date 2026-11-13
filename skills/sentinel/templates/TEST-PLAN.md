# Test plan — {{Project name}}

<!-- SENTINEL. One section per phase; later phases are appended below, never renumbered.
     Columns are fixed (CONTRACT.md §3). Covers = AC ids, plus the REQ they belong to, e.g. "AC-003, REQ-002".
     Level = the module's rigour. Type = unit | integration | e2e | manual | security | performance.
     Status = todo | pass | fail (update with `sentinel.py set <P> TC-001=pass`). Get the next id with `sentinel.py next <P>`.
     Depth (rigour.md): Light → smoke + UAT step · Standard → unit + integration on main paths ·
     Critical → + edge, failure, permission, end-to-end, migration rehearsal. -->

How to record results: the team (or its coding agents) runs the tests; tell Sentinel "TC-004 pass, TC-007 fail: <why>".

## {{P1}} — {{phase name}}

Phase goal: {{exit criterion from PLAN.md}}

| TC | Covers | Module | Level | Type | Steps / expectation | Status |
|---|---|---|---|---|---|---|
| TC-001 | AC-001, REQ-001 | M1 | Standard | unit | Given … when … → expect … | todo |

### Notes for {{P1}}
- Test data / accounts needed: {{…}}
- Not testable as written (asked the user): {{none}}
