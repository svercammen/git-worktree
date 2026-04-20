# git-wt

A git worktree manager with automatic dependency setup, IDE configuration, and a terminal UI.

## Installation

The script lives at `~/bin/git-wt`. Make sure `~/bin` is on your `PATH`:

```zsh
export PATH="$HOME/bin:$PATH"
```

### Shell integration

Add the following to your `.zshrc`:

```zsh
eval "$(git wt shell-init)"
```

This installs the `wt` shell function (required for `cd` to work after create/switch) and registers tab completion. It works regardless of where it appears relative to `compinit` or `oh-my-zsh`. After editing `.zshrc`, reload it:

```zsh
source ~/.zshrc
```

---

## Usage

All commands work as both `git wt <command>` and `wt <command>`. Using `wt` is recommended — it enables directory changing after create/switch and Atuin/zsh history injection when using the TUI.

### Interactive TUI

```zsh
wt
```

Running `wt` with no arguments opens a terminal UI.

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Switch between create / remove / list tabs |
| `↑` / `↓` | Navigate fields |
| `←` / `→` | Cycle options in a selector |
| `Space` | Toggle a checkbox |
| `Enter` | Run the command |
| `Esc` | Quit |

The preview line at the bottom shows the exact command that will run.

### Switch to a worktree

```zsh
wt <name>           # shorthand: partial branch or path match
wt switch <name>    # explicit form
wt -                # switch to the main worktree
```

Matches case-insensitively against branch names and paths. Errors if the pattern matches multiple worktrees.

### Create a worktree

```zsh
wt create <branch>
wt create <branch> --base <ref>
```

Creates a new worktree, installs dependencies, sets up IDE config, symlinks `.env` files, and changes directory into the new worktree.

| Option | Description |
|--------|-------------|
| `--base <ref>` | Branch, commit SHA, or HEAD to base the new branch on (defaults to `main`) |
| `--no-install` | Skip `poetry install` / `npm install` |
| `--no-open` | Don't launch the editor after creation |
| `--no-cd` | Don't change directory into the new worktree |
| `--no-ide` | Skip IDE configuration (`.idea/`, `.vscode/`) |
| `--copy-env` | Copy `.env` files instead of symlinking |

### Remove a worktree

```zsh
wt remove <branch>
wt remove <branch> --force   # skip confirmation prompt
```

Cleans up virtual environments and `node_modules` before removing. Handles orphaned directories (path exists on disk but not registered with git).

### List worktrees

```zsh
wt list
```

Shows all worktrees with branch names, IDE config status, venv count, and `node_modules` presence.

---

## Configuration

Edit `~/.config/git-wt/config`:

```ini
# Editor to open after creating a worktree
EDITOR=idea

# Base directory for worktrees (relative to repo parent)
# {repo} is replaced with the repository name
BASE_DIR=../worktrees/{repo}

# Whether to open editor after create (overridden by --no-open)
OPEN_EDITOR=true
```

---

## How shell integration works

The `wt` function wraps `git wt` to solve three problems:

**Directory changing** — a child process cannot change the parent shell's working directory. The shell function passes a temp file path (`--cd-file`) to the script; the script writes the target path into it, and the shell function reads it and calls `builtin cd`.

**Atuin history** — when the TUI produces a command, the expanded form (e.g. `git wt create my-branch --no-open`) is recorded in Atuin via `atuin history start/end`. When calling `git wt` directly (without the shell function), the script handles this itself.

**Native zsh history** — the expanded command is also added to zsh's history ring via `print -s`, so it appears when pressing the up arrow.
