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
| **Spartan** | Risk and security | Pass/fail gates G1–G5, security reviews of Critical modules |

```
Alice ─G1→ Stark ─G2→ Jarvis ─G3→ [you build] ─G4→ Sentinel ─G5→ release ─(next phase)→ … → Alice handover
                         Atlas watches git, PRs and CI the whole way · Spartan runs every gate
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

| Step | Say / run | What happens |
|---|---|---|
| 1 | `/atlas new Bakery Orders` | Atlas creates `PRJ-0001` and asks for the client, size, author and code repo |
| 2 | Drop transcripts and documents into `discovery/sources/`, then run `/alice` | You get the PRD, the proposal and the client questions. Alice asks you about anything unclear and never guesses |
| 3 | Client approves the proposal: *"record sign-off"* | The documents are snapshotted, and the sign-off is logged |
| 4 | `/spartan G1`, then `/stark` | Architecture is designed and modules get rigour levels. You confirm Light, Standard or Critical |
| 5 | `/spartan G2`, `/jarvis`, `/spartan G3`, then `atlasctl publish` | Phases and work packages are planned, and the blueprint is copied into your code repo's `docs/blueprint/` |
| 6 | **You build** (alone, with a team, or with coding agents) | Branch names like `WP-07-…` help matching, but nothing is required |
| 7 | `/atlas` at any time | Atlas reconciles git, pull requests and CI, then shows progress, what needs attention and the next step |
| 8 | `/spartan G4`, `/sentinel`, then client UAT, `/spartan G5` and `/atlas release P1` | Phase 1 is tested and released. Repeat for each phase |
| 9 | `/alice report` and `/alice handover` | Client updates and the final handover pack, as PDFs in `~/Desktop/<PRJ>-<name>-for-client/` |

In Codex, mention skills with `$atlas`, `$alice`, and so on, or simply ask in plain words.

## What makes it different

- **Derived, not declared.** Progress comes from commits, pull requests and CI, not from people remembering to update a board. Collaborators need nothing installed.
- **Asks instead of guessing.** When the evidence is ambiguous, Atlas asks you once and remembers the answer (`atlasctl learn`).
- **Rigour per module.** Payments and logins get Critical scrutiny; a settings page stays Light. Depth of design, size of work packages, tests and gates all scale with it.
- **A `.git`-style tracker.** `log/events.jsonl` is append-only and hash-chained, so editing past events is detectable (`atlasctl verify-log`). Snapshots prove what the client approved.
- **Private by design.** Client material lives in project storage, never in code repositories. Web research never includes client details. No credentials are ever stored.
- **Extensible.** The flow is the table in [`pipeline.md`](pipeline.md). Add an agent by adding a skill folder and a row.

## Repository layout

```
.claude-plugin/   Claude Code plugin + marketplace manifests
.codex-plugin/    Codex plugin manifest
.agents/plugins/  Codex marketplace
skills/           atlas · alice · stark · jarvis · sentinel · spartan
lib/              shared scripts: atlasctl (core), gates, convert_docs, pdf_export, mdtables
CONTRACT.md       folders, IDs and events every agent follows
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
