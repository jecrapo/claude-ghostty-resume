# claude-ghostty-resume

A Claude Code plugin that brings your sessions back when Ghostty restores its
windows, each in the pane whose directory it ran in.

Ghostty with `window-save-state = always` reopens every window, tab, and split
at its old working directory after you quit it or restart the Mac. The Claude
Code sessions that ran in those panes do not come back. This plugin records
each session while it runs and, when a restored pane opens its shell, runs
`claude --resume <id>` for the session that ran in that directory.

Nothing runs at login and nothing scripts Ghostty. The shell in each restored
pane does the work. macOS, Ghostty, and zsh only.

## Install

In Claude Code:

```
/plugin marketplace add jecrapo/claude-ghostty-resume
/plugin install ghostty-resume@claude-ghostty-resume
/ghostty-resume:setup
```

The first two commands enable the hooks that record sessions. The third links
`~/.local/bin/claude-ghostty-resume` and appends a block to the end of
`~/.zshrc`:

```zsh
# >>> claude-ghostty-resume >>>
if _cgr_id=$(claude-ghostty-resume claim 2>/dev/null); then
  claude --resume "$_cgr_id"
fi
unset _cgr_id
# <<< claude-ghostty-resume <<<
```

Sessions already running when you install have no record. They are recorded
from their next start.

## Required settings

Set `window-save-state = always` in your Ghostty config. Without it Ghostty
opens one empty window and no pane matches a recorded directory.

Keep the `.zshrc` block after anything that changes `PATH`. It needs
`~/.local/bin` and `claude` on the path.

## How it works

- A `SessionStart` hook writes one JSON file per interactive session to
  `~/.claude/ghostty-resume/`: session id, working directory, transcript
  path, and name.
- A `SessionEnd` hook deletes the file on a deliberate exit (`/exit`,
  `/clear`, logout, switching sessions) and otherwise marks how the session
  ended. Quitting Ghostty hangs up the shell, so the session ends with reason
  `other` or with no hook at all. Either way the file survives.
- When a shell starts, `claude-ghostty-resume claim` walks up the process
  tree to the Ghostty process. If Ghostty has been running for more than 60
  seconds, the shell is an ordinary new tab and `claim` exits without output.
  Otherwise it looks for a surviving record whose directory matches the
  shell's, marks it claimed, and prints the session id. The `.zshrc` block
  passes that id to `claude --resume`.
- Two panes restored in the same directory each get one of that directory's
  sessions. Which pane gets which is not fixed. A claim that never leads to a
  running session, because `claude` failed or you pressed ctrl-c, expires
  after 10 minutes.
- Names come from the transcript, so a `/rename` done at any time is
  reflected in `list`.

Skipped: headless (`claude -p`) sessions, sessions already running, sessions
whose directory or transcript no longer exists, and records older than 30
days.

Panes that Ghostty does not restore are not resumed anywhere. `list` shows
the records that are still waiting.

## Commands

```
claude-ghostty-resume list               # every record and why it would or wouldn't resume
claude-ghostty-resume claim              # what the .zshrc block runs; says why when it declines
claude-ghostty-resume prune              # drop records that can never resume
```

## Uninstall

```
/ghostty-resume:setup uninstall
/plugin uninstall ghostty-resume@claude-ghostty-resume
```

The first removes the symlink and the `.zshrc` block, the second the hooks.
Records in `~/.claude/ghostty-resume/` are left for you to delete.

## Credit

A Ghostty port of Adrian Schmidt's
[claude-iterm2-resume-sessions](https://github.com/adrianschmidt/claude-iterm2-resume-sessions),
which types the resume command into iTerm2 panes over AppleScript. Ghostty
has no scripting interface on macOS, so this version lets each restored shell
find its own session instead.
