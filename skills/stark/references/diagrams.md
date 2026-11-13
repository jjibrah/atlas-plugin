# Diagrams — the pack and the Mermaid rules

## 1. The diagram pack (`/stark diagrams`)

Pictures of how the system will work, for the client and non-engineers. Begun with `--stage none`: ignore the brief's small-track and "When done" lines.

1. **Read.** First run: the PRD once (people, workflows, solution, requirement and rule tables, data). Later runs: `atlas pack stark --changed`, and redraw only the pictures those rows touch.
2. **Choose** from `templates/DIAGRAMS.md`, scaled to the project:

   | Picture | Type | Small | Medium / Large |
   |---|---|---|---|
   | Who uses it, for what | `flowchart LR`, people left, goals as rounded nodes | yes | yes |
   | How the work will flow | `flowchart TD` | 1–2 workflows | one per important workflow |
   | Who talks to whom | `sequenceDiagram` | no | 1–2 |
   | The information it keeps | `classDiagram` (or `erDiagram`) | if records matter | yes |
   | The life of the main record | `stateDiagram-v2` | yes | yes |
   | The parts of the system | `flowchart LR` | if outside services | yes |

3. **Write `<D>/DIAGRAMS.md`.** Plain words, the proposal's vocabulary, one name per thing in every picture. No internal IDs in labels or text. A "What this picture shows" sentence above each picture, no caption under it. Arrows run one way; none points back at a person. Draw only what the requirements say: a gap is a note to Alice, never a guess.
4. **Check and deliver.** `verify.py <D> --diagrams` until it passes → `atlas export design/DIAGRAMS.md` (prints the PDF's path; "Syntax error" in a picture means a rule in §2 was broken) → `atlas finish stark --stage none --summary "Diagram pack v1.0: 4 pictures"`.
5. Tell the user, in plain words, which pictures are in the pack and where the PDF is.

## 2. Mermaid rules that avoid render errors

All types:
- One diagram per code block; its first line is the type. Split one that passes ~25 nodes (the pack: ~15).
- IDs are letters, digits and underscores (`admin_web`): no hyphens, no spaces, never `end`.
- Put every label in double quotes when it has spaces, punctuation or parentheses: `a["Admin screen (web)"]`. No double quotes inside a label.

By type:
- `flowchart`: edge text as `a -- "Yes" --> b`; rounded node `a("…")`, start or end `a(["…"])`, decision `a{"…"}`, stored data `a[("…")]`; close every `subgraph name["Title"]` with `end`.
- `sequenceDiagram`: declare each party first (`actor c as Customer`, `participant s as The system`); `c->>s: text` for a request, `s-->>c: text` for a reply; no semicolons or `#` in the text.
- `classDiagram`: class names without spaces (`class OrderLine["Order line"]`); one attribute per line inside `{ }`; `Customer "1" --> "many" Order : places`.
- `erDiagram`: entity names without spaces; attributes as `type name PK "comment"`; `CUSTOMER ||--o{ ORDER : places`.
- `stateDiagram-v2`: single-word state IDs (`state "Awaiting payment" as awaiting_payment`); `[*]` for start and end; no colons inside a transition label.
