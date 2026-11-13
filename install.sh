#!/usr/bin/env bash
# Install the ATLAS plugin into Claude Code and/or Codex from this folder.
# Usage: ./install.sh            (installs into every CLI it finds)
#        ./install.sh claude     (only Claude Code)
#        ./install.sh codex      (only Codex)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WANT="${1:-all}"
done_any=0

if [[ "$WANT" == "all" || "$WANT" == "claude" ]] && command -v claude >/dev/null 2>&1; then
  echo "→ Claude Code"
  claude plugin marketplace add "$DIR" || true
  claude plugin install atlas@atlas
  done_any=1
fi
if [[ "$WANT" == "all" || "$WANT" == "codex" ]] && command -v codex >/dev/null 2>&1; then
  echo "→ Codex"
  codex plugin marketplace add "$DIR" || true
  codex plugin add atlas@atlas
  done_any=1
fi
if [[ $done_any == 0 ]]; then
  echo "Neither the 'claude' nor the 'codex' CLI was found. Install one, then re-run." >&2
  exit 1
fi
python3 "$DIR/lib/atlasctl.py" doctor || true
cat <<'MSG'

Installed. Next, choose where project records live (once per device):
  python3 lib/atlasctl.py setup --mode github          # private repo per project (run `gh auth login` first)
  python3 lib/atlasctl.py setup --mode folder --path ~/AtlasProjects
…or just open Claude Code / Codex and say "set up atlas".
MSG
