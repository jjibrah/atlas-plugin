# {{Project name}} — Modules

> Read by Atlas. One row per module. **Rigour** is Stark's proposal; the user confirms all at once with `atlas rigour --accept [M2=Critical …]`, and the confirmed level wins. **Paths** are comma-separated globs relative to the code repository root (`**` allowed), or `?` until known — Atlas maps commits to modules with them. No REQ / FR / AC / WP IDs in this table.

| Module | Name | Rigour | Paths | Signals | Reason |
|---|---|---|---|---|---|
| M1 | {{Identity & roles}} | {{Critical}} | {{src/auth/**, src/users/**}} | {{login and roles, personal data}} | {{one strong signal (auth) is enough}} |
| M2 | {{…}} | {{Light}} | {{?}} | {{none}} | {{project default for a Small project}} |

Project size: {{Small / Medium / Large}} → default {{Light / Standard}}. Cross-cutting requirements (module `X` in the register) are not listed; they follow the strictest module they protect.
