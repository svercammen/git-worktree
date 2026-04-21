# git-wt — Claude Code Instructions

## Project layout

```
~/code/wt/
├── git-wt          # main Python script (symlinked from ~/bin/git-wt)
├── completions/
│   └── _wt         # zsh completion function
├── README.md       # user-facing docs
└── CLAUDE.md       # this file
```

## How the script is invoked

- `git wt <cmd>` — git finds `git-wt` on PATH via `~/bin/git-wt` symlink
- `wt [args]` — shell function defined by `eval "$(git wt shell-init)"` in ~/.zshrc

The `wt()` shell function wraps `git wt` to enable:
- **cd after create/switch** — via `--cd-file` temp file mechanism
- **Atuin history injection** — via `atuin history start/end` after TUI commands
- **zsh native history** — via `print -s`

## Commands

| Command | Description |
|---------|-------------|
| `create <branch>` | Create worktree, install deps, setup IDE, symlink .env |
| `remove <branch>` | Remove worktree, clean venvs/node_modules |
| `switch <name>` | cd into worktree by partial branch/path match |
| `<name>` / `-` | Shorthand for switch; `-` goes to main worktree |
| `list` | Show all worktrees with status |
| `shell-init` | Print shell integration code for eval in .zshrc |
| (no args) | Open TUI |

## Key implementation details

### Global pre-argparse flags
`--cd-file=PATH` and `--cmd-file=PATH` are extracted from sys.argv before argparse sees them. They're injected by the `wt()` shell function for TUI mode. After TUI produces argv, `--cd-file` is re-injected for `create` and `switch` subparsers.

### TUI (curses)
- `run_tui()` returns a list of argv tokens or None on cancel
- Field types: `False` = text input, `True` = checkbox, `"select"` = ←/→ picker, `"multi"` = vertical list with Space toggle (↑/↓ moves cursor, wrapping to adjacent fields at boundaries)
- Tab/Shift-Tab switch tabs; ↑/↓ navigate fields (or within a focused multi-select); Enter always runs (never toggles)
- Worktrees fetched once via `get_worktrees()` at TUI start
- `remove` accepts multiple targets — the TUI emits all checked branches into argv; the CLI resolves each, confirms once, then loops removal

### Worktree path resolution
`resolve_worktree(name, config)` tries: direct path → git worktree list branch match → computed config path (catches orphaned dirs not registered with git).

### Orphaned directory handling
In `cmd_create`, if the target path exists but isn't in `git worktree list`, it's treated as an orphaned leftover and removed before proceeding.

### Shell integration (shell-init output)
The output uses `autoload -Uz _wt` + `compdef _wt wt` to explicitly register the completion, so it works even when `eval` runs after oh-my-zsh/compinit.

### Atuin history
- When TUI is used via `wt` (shell function): `--cmd-file` is passed; shell function calls `atuin history start/end`
- When TUI is used via `git wt` (direct): Python script calls `atuin history start/end` itself
- Guarded by `command -v atuin` check (shell) and `FileNotFoundError` catch (Python)

## Config file
`~/.config/git-wt/config` — keys: `EDITOR`, `BASE_DIR` (supports `{repo}`), `OPEN_EDITOR`
Default worktree location: `../worktrees/{repo}/<branch>` relative to git root's parent.

### In-project virtualenvs
The script sets `poetry config --local virtualenvs.in-project true` before `poetry install` in each sub-project. This places venvs at `<project>/.venv/` instead of Poetry's centralized cache (`~/Library/Caches/pypoetry/virtualenvs/`). Benefits:
- Predictable paths — no hash-based venv directories
- Self-contained — deleting a worktree removes its venvs
- IDE-friendly — IntelliJ/VS Code auto-detect `.venv` directories

**To revert to centralized venvs**: remove `poetry.toml` from each sub-project (or set `in-project = false`), then `poetry env remove --all` + `poetry install` in each. Also remove the `poetry config --local` line from `install_dependencies()` in this script.

### JetBrains SDK registration
IntelliJ/.iml files and run configs reference SDKs by name (e.g. `Python 3.13 (my-service)`), which resolve via IntelliJ's global SDK table (`jdk.table.xml`). The script:
- **On create**: clones source SDK entries in jdk.table.xml with worktree venv paths, named `<source> [wt:<dir>]`. Patches .iml and run config `SDK_NAME` references.
- **On remove**: removes `[wt:<dir>]` SDK entries from all JetBrains config dirs.
- Iterates all JetBrains config dirs (IntelliJ, PyCharm, etc.) — skips IDEs where the source SDK isn't found.

## Known issues / decisions
- `wt -` goes to main worktree (`-` is the shorthand, matching the original git-worktree-switcher behaviour)
- The old `git-worktree-switcher` package at `~/bin/git-worktree-switcher` is still on PATH; user intends to remove it
- `exec $SHELL` (old switcher's cd approach) is intentionally NOT used; `--cd-file` keeps the same shell session
