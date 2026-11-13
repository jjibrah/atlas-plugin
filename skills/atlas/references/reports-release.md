# Reports, publishing, release, timeline

## Internal status report
`atlas status`, then write `<P>/reports/status-YYYY-MM-DD.md` (`<P>` from `atlas where`), one page: progress per phase, what changed since the last report (`atlas log --limit 30`), risks, attention items, decisions needed.

## Client update
Alice's job: load the alice skill in report mode (`/alice report`). She writes in plain language and exports the PDF.

## Publish the blueprint
`atlas publish` previews what would be copied into the code repository's `docs/blueprint/` (design and plan only, never client material). After the user confirms: `atlas publish --yes`. Add `--always` once and it re-publishes whenever the plan changes.

## Release a phase
1. Status must show G5 passed for the phase. If it lists open items, they come first.
2. Ask the user to confirm the deployment happened, then `atlas release P# --note "<version / date / where>"`.
3. Next is the following phase, or `/alice handover` after the last one.

## Timeline and integrity
`atlas log` (filters: `--type`, `--actor`, `--ref`, `--limit`) or point to `views/TIMELINE.md`. `atlas verify-log` checks that no past event was edited.
