# Rigour levels

Set per module in `design/MODULES.md` (Stark proposes, the user confirms with `atlasctl rigour`). The project size class sets the default; a module can be raised or lowered.

## Signals that raise a module to Critical
money or payments · personal or health data · login, roles or permissions · an outside integration that moves data or money · a state machine with more than ~5 states · a regulation applies · data migration from an old system · many other modules depend on it.

One strong signal (money, health data, auth) is enough for Critical. Two or more moderate signals → at least Standard. None → Light (or the project default if higher).

## What each level means

| | Light | Standard | Critical |
|---|---|---|---|
| Stark spec | Purpose, use cases, acceptance criteria | + data model, flows, API contracts, state machines where states exist | + every error and edge case, failure and rollback behaviour, threat notes, audit trail |
| Jarvis plan | 1–2 work packages | Normal work packages (S/M) | Small work packages, each ending in a review checkpoint |
| Atlas "done" | Code exists and matches (likely) | Tests pass (verified) | Verified + each acceptance criterion checked + user sign-off |
| Spartan | Basic gate checks | Standard gate list | Full list + security review of every change touching the module |
| Sentinel | Smoke test + UAT step | Unit + integration tests on main paths | + edge, failure, permission, end-to-end; migration rehearsal |

## Defaults by project size
Small → Light · Medium → Standard · Large → Standard. Critical is never a default — it is always earned by a signal and confirmed by the user.
