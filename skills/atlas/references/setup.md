# First use on a device

Ask the user which storage they want (one question):

- **GitHub (recommended for teams and several devices):** each project is a private repo in their account, and a private `atlas-registry` repo lists them all. They must be logged in to the GitHub CLI. If `gh auth status` fails, tell them to run `gh auth login` themselves — never ask for a token. Then `atlas setup --mode github`.
- **Folder:** they give a path (local, Dropbox, iCloud or a shared drive). `atlas setup --mode folder --path "<path>"`.

Setup also:
- installs an `atlas` terminal command in `~/.local/bin`, so `atlas status` works outside a chat and costs nothing;
- creates `~/.atlas/venv` for reading PDFs;
- checks for a Chrome-family browser, used to make client PDFs.

Report anything `atlas doctor` lists as missing. A folder-mode project can move to GitHub later: `atlas migrate --to github`.

On another device, a code repository given as a URL is cloned to `~/.atlas/repos/` automatically; to use the user's own clone: `atlas link-repo <name> <local path>`.
