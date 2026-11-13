# Pipeline

Atlas reads this table to know the flow. To add an agent: add its skill under `skills/`, then add a row here. Rows run top to bottom; `build`, `test` and `release` repeat for each phase.

| Stage | Agent | Needs | Produces | Gate after | Interactive | Per phase |
|---|---|---|---|---|---|---|
| define | alice | files in discovery/sources/ | discovery/PRD.md, discovery/PROPOSAL.md, discovery/QUESTIONS.md | G1 | yes | no |
| design | stark | discovery/PRD.md | design/TECHNICAL.md, design/MODULES.md | G2 | some | no |
| plan | jarvis | design/TECHNICAL.md | plan/PLAN.md | G3 | little | no |
| build | user | plan/PLAN.md | code in the code repositories | G4 | no | yes |
| test | sentinel | plan/PLAN.md, design/TECHNICAL.md | test/TEST-PLAN.md, test/UAT.md, test/GO-LIVE.md | G5 | little | yes |
| release | atlas | test/GO-LIVE.md | phase.released event | - | little | yes |
| handover | alice | reports/, views/ | reports/HANDOVER.md | - | little | no |

Change requests (`atlasctl cr`) re-enter at `define` and touch only the items `atlasctl impact` lists.
