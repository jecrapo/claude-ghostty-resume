---
name: setup
description: Install or remove the shell side of ghostty-resume (PATH symlink + .zshrc block). Use when the user asks to set up, install, enable, disable, or uninstall ghostty-resume, or asks why sessions are not coming back after Ghostty restarts.
---

# ghostty-resume setup

The plugin's hooks record sessions automatically. Resuming them when Ghostty
restores its panes needs a one-time install step, which this skill performs.

## Install

Run and show the user the output:

```bash
/usr/bin/python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py"
```

It links `~/.local/bin/claude-ghostty-resume` to the plugin's script and
appends a block to `~/.zshrc` that resumes a session in each restored pane.
Repeat the Ghostty setting the script prints: without `window-save-state =
always` Ghostty opens one empty window and nothing resumes.

## Uninstall

If the user asked to remove or disable it:

```bash
/usr/bin/python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" --uninstall
```

Tell them the hooks keep recording sessions until the plugin itself is
uninstalled with `/plugin`.

## Troubleshooting

- `claude-ghostty-resume list` shows every recorded session and why it would
  or would not be resumed.
- `claude-ghostty-resume claim --dry-run` run in a pane says what that pane
  would resume, or why it would not. Add `--window 999999` to ignore the check
  that Ghostty just started.
- Only zsh is supported. The block lives at the end of `~/.zshrc` and must
  stay after anything that sets `PATH`.
