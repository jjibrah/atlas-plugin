# {{Project name}} — Modules

> Read by `atlasctl` (CONTRACT §3). One row per module. **Rigour** is Stark's proposal (rigour.md); the user confirms each with `atlasctl rigour M# <Light|Standard|Critical> --reason "…"`, and the confirmed level wins. **Paths** are comma-separated globs relative to the code repository root (`**` allowed), or `?` until known — Atlas maps commits to modules with them. Do not put REQ/FR/WP IDs in this table.

| Module | Name | Rigour | Paths | Signals | Reason |
|---|---|---|---|---|---|
| M1 | {{Identity & roles}} | {{Critical}} | {{src/auth/**, src/users/**}} | {{login and roles, personal data}} | {{one strong signal (auth) is enough}} |
| M2 | {{…}} | {{Light}} | {{?}} | {{none}} | {{project default for a Small project}} |

Project size: {{Small / Medium / Large}} → default {{Light / Standard}}. Cross-cutting requirements (module `X` in the register) are not listed; they follow the strictest module they protect.
