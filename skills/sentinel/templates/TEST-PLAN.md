# Test plan — {{Project name}}

| Field | Value |
|---|---|
| Project | {{PRJ-id}} {{Project name}} |
| Version | v1.0 — {{YYYY-MM-DD}} |
| Last TC issued | TC-000 |

<!-- SENTINEL. `sentinel.py seed <P> --phase P#` creates this file and adds one `## P# — <phase name>` section per
     phase; rows are never renumbered and a TC id is never reused (`sentinel.py next <P>` gives the next one).
     Covers = the criterion and its requirement ("AC-003, REQ-002"). Level = the module's rigour.
     Type = unit | integration | e2e | manual | security | performance. Status = todo | pass | fail.
     Retire a test in place: Steps "Retired: <reason>", Covers "—". -->

**For whoever writes the automated tests:** put the test's id in the test name — `test_TC_012_refund_is_capped`, `it("TC-012 refund is capped")` — and produce a JUnit-style XML report. Results are then read with `sentinel.py results <P> <report.xml>`. Manual tests are reported by hand ("TC-004 pass, TC-007 fail: total wrong").
