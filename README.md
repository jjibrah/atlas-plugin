# ATLAS

**A team of AI agents that runs client software projects from the first meeting to handover**, for [Claude Code](https://claude.com/claude-code) and [OpenAI Codex](https://developers.openai.com/codex).

You build the software. ATLAS:
- does the discovery, design, planning, testing and paperwork around it;
- keeps a tamper-evident record of everything that happened;
- reads the real state of your code from git, so the tracker stays accurate even when nobody updates it.

📖 **[Read the usage guide](https://jjibrah.github.io/atlas-plugin/)** — installation, agent roles, diagrams, and an end-to-end walkthrough. You can also open [`docs/index.html`](docs/index.html) locally.

| Agent | Role | Produces |
|---|---|---|
| **Atlas** | Project manager | Project record, event log, status, attention list, next step, change requests, releases |
| **Alice** | Discovery and client communication | Internal PRD, client proposal, questions for the client, progress updates, handover pack |
| **Stark** | Design | Architecture, data model, API contracts, state machines, modules with rigour levels |
| **Jarvis** | Planning | Phases, work packages, dependencies, agent briefs, audit of existing code |
| **Sentinel** | Test and release | Test plan from acceptance criteria, client UAT script, go-live checklist |
| **Spartan** | Risk and security | Security reviews of Critical modules, explanations and waivers for the checks G1–G5 |

```
Alice ─G1→ Stark ─G2→ Jarvis ─G3→ [you build] ─G4→ Sentinel ─G5→ release ─(next phase)→ … → Alice handover
             Atlas watches git, PRs and CI the whole way and runs the checks · Spartan reviews Critical work
```

## Install

You need:
- **git**;
- **Python 3.9+**;
- **Claude Code and/or Codex**;
- optionally **Google Chrome, Edge or Chromium**, for client PDFs;
- optionally the **GitHub CLI**, for GitHub storage mode.

**From GitHub:**

```bash
# Claude Code
claude plugin marketplace add jjibrah/atlas-plugin
claude plugin install atlas@atlas

# Codex
codex plugin marketplace add jjibrah/atlas-plugin
codex plugin add atlas@atlas
```

**From a local clone:**

```bash
git clone https://github.com/jjibrah/atlas-plugin.git
cd atlas-plugin && ./install.sh        # installs into every CLI it finds
```

After installation, start a new Claude Code or Codex session so it loads the plugin.

## Set up (once per device)

Open Claude Code or Codex and say **"set up atlas"**, or run the setup yourself. Choose where project records live:

| Mode | Command | Best for |
|---|---|---|
| **GitHub** (recommended) | `gh auth login`, then `python3 lib/atlasctl.py setup --mode github` | Teams and several devices. Each project is a **private repo**, and a private `atlas-registry` repo lists them all |
| **Folder** | `python3 lib/atlasctl.py setup --mode folder --path ~/AtlasProjects` | Working alone, offline, or with a Dropbox, iCloud or shared drive |

The Python commands above run from the repository root. If you installed directly from the marketplace, ask the agent to run setup for you.

Setup also creates `~/.atlas/venv`, with PyMuPDF for reading PDFs. Run `python3 lib/atlasctl.py doctor` to check everything.

## Use it

`/atlas` shows where the project stands. `/atlas go` does whatever comes next. That is most of it.

| Step | Say / run | What happens |
|---|---|---|
| 1 | `/atlas new Bakery Orders` | Atlas creates `PRJ-0001` and asks for the client, size, author and code repo. Existing PRD or codebase: add `--prd file.md` or `--start build` |
| 2 | `atlas intake ./client-files`, then `/alice` | You get the PRD, the proposal and the client questions. Alice asks you about anything unclear and never guesses |
| 3 | Client approves: *"record sign-off"* | The approved documents are snapshotted. The ready-for-design check passes by itself |
| 4 | `/atlas go` (twice) | Stark designs and proposes a rigour level per module; you confirm them with one command. Jarvis plans. On a Small project both happen in one run |
| 5 | **You build** (alone, with a team, or with coding agents) | Branches named `WP-07-…` are matched exactly; nothing is required |
| 6 | `/atlas` in chat, or `atlas status` in a terminal | Atlas reads new commits, pull requests and CI, moves the work packages, runs any pending check, and shows what needs you |
| 7 | `/atlas go` → client UAT → `atlas release P1` | Sentinel writes the tests and the client's acceptance script; the phase is released. Repeat per phase |
| 8 | `/alice report`, `/alice handover` | Client updates and the handover pack, as PDFs in `~/Desktop/<PRJ>-<name>-for-client/` |

- **Checks (G1–G5) run by themselves** when an agent finishes and on every status. You see only what is still open. `/spartan` explains a failing check, records a waiver, or runs a security review.
- **In Codex,** mention skills with `$atlas`, `$alice`, and so on, or ask in plain words.
- **In a terminal,** `atlas status` uses no tokens. Setup installs the `atlas` command in `~/.local/bin`.

## What makes it different

- **Derived, not declared.** Progress comes from commits, pull requests and CI. A work package is marked done when its branch or pull request is merged; you can override it. Collaborators need nothing installed.
- **Asks instead of guessing.** When the evidence is ambiguous, Atlas asks you once and remembers the answer (`atlas learn`).
- **Agents talk to each other.** A question for the client goes from Stark to Alice as a note, not through you. Status tells you when the plan has fallen behind the design, or the design behind the PRD.
- **Cheap to run.** Each agent starts from a 30-line brief and reads only the rows it needs (`atlas pack`). Routine checks run in the terminal.
- **Rigour per module.** Payments and logins get Critical scrutiny; a settings page stays Light. Depth of design, size of work packages, tests and checks all scale with it.
- **A `.git`-style tracker.** `log/events.jsonl` is append-only and hash-chained, so editing past events is detectable (`atlas verify-log`). Snapshots prove what the client approved.
- **Private by design.** Client material lives in project storage, never in code repositories. Web research never includes client details. No credentials are stored.
- **Extensible.** The flow is the table in [`pipeline.md`](pipeline.md). Add an agent by adding a skill folder and a row.

## Repository layout

```
.claude-plugin/   Claude Code plugin + marketplace manifests
.codex-plugin/    Codex plugin manifest
.agents/plugins/  Codex marketplace
skills/           atlas · alice · stark · jarvis · sentinel · spartan
lib/              shared scripts: atlasctl (core), flow (begin/finish/pack/notes), gates, convert_docs, pdf_export
CONTRACT.md       the run interface, folders, IDs and events every agent follows
CHANGELOG.md
pipeline.md · rigour.md · gates.md
docs/index.html   the guide (GitHub Pages)
```

## Contributing

**Improvements go to `dev`; tested releases go to `main`.**
`main` is protected: changes must arrive through a pull request, review
conversations must be resolved, and force pushes and deletion are blocked.
These protections also apply to administrators.

- **Contributors with write access:** work on `dev`, or open a feature-branch
  pull request targeting `dev`.
- **Outside contributors:** fork the repository, branch from `dev`, and open a
  pull request targeting this repository's `dev` branch. A public repository
  does not grant visitors permission to push directly.
- **Maintainer:** test the changes on `dev`, then open a pull request from
  `dev` to `main` and merge when ready. Keep `dev` after merging so development
  can continue. An additional reviewer's approval is optional; no automated
  status checks are currently required.

For collaborators with write access:

```bash
git fetch origin
git switch dev
git pull --ff-only origin dev
# Make and test your improvements.
git add <changed-files>
git commit -m "Describe your improvement"
git push origin dev
```

For the maintainer, once the changes have been tested:

```bash
gh pr create --base main --head dev
# Review and merge the pull request on GitHub when ready.
# After merging, bring main back into dev before continuing development:
git fetch origin
git switch dev
git merge origin/main
git push origin dev
```

Each agent can be improved on its own. Read [`CONTRACT.md`](CONTRACT.md) first; agents interoperate only through it. Run a full flow on a sample project before opening a pull request:

```bash
export ATLAS_HOME=$(mktemp -d) ATLAS_OUTBOX=$(mktemp -d)
python3 lib/atlasctl.py setup --mode folder --path "$ATLAS_HOME/projects" --no-deps
python3 lib/atlasctl.py new "Sample" --client "Sample Co" --size Small --author "You"
```

## Guide hosting

The usage guide is published at **https://jjibrah.github.io/atlas-plugin/**.
GitHub Pages serves the `docs/` folder on `main`; merging guide changes into
`main` publishes them automatically. Changes on `dev` do not update the live site. `docs/.nojekyll` keeps the guide as plain static HTML.
No build tools or application server are needed.

To update the guide, edit `docs/index.html`, `docs/assets/style.css` (design),
or `docs/assets/guide.js` (interactions), then commit and push to `dev`.
Test the changes, then merge a `dev` → `main` pull request to publish.
The guide uses a light theme, responsive navigation, copyable setup commands,
and a searchable command reference.

## Licence

[MIT](LICENSE)
