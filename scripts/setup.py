#!/usr/bin/env python3
"""Install or remove the shell side of ghostty-resume.

Puts `claude-ghostty-resume` on the PATH and appends a block to ~/.zshrc that
claims and resumes a session when a restored Ghostty pane opens its shell.
Safe to re-run.

Usage: setup.py [--uninstall]
"""
import os
import sys

BIN_DIR = os.path.expanduser("~/.local/bin")
COMMAND_LINK = os.path.join(BIN_DIR, "claude-ghostty-resume")
SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claude-ghostty-resume")
ZSHRC = os.path.expanduser(os.environ.get("CLAUDE_GHOSTTY_RESUME_ZSHRC", "~/.zshrc"))

BEGIN = "# >>> claude-ghostty-resume >>>"
END = "# <<< claude-ghostty-resume <<<"
# Not `exec`: the shell must survive so the pane is usable after claude exits.
BLOCK = """%s
if _cgr_id=$(claude-ghostty-resume claim 2>/dev/null); then
  claude --resume "$_cgr_id"
fi
unset _cgr_id
%s
""" % (BEGIN, END)


def read_zshrc():
    try:
        with open(ZSHRC) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def strip_block(text):
    start = text.find(BEGIN)
    stop = text.find(END)
    if start == -1 or stop == -1:
        return text
    stop += len(END)
    if text[stop : stop + 1] == "\n":
        stop += 1
    return text[:start] + text[stop:]


def install():
    if sys.platform != "darwin":
        sys.exit("ghostty-resume relies on Ghostty's macOS window restoration and only works on macOS.")
    os.makedirs(BIN_DIR, exist_ok=True)
    if os.path.lexists(COMMAND_LINK):
        os.remove(COMMAND_LINK)
    os.symlink(SCRIPT, COMMAND_LINK)
    print("linked %s -> %s" % (COMMAND_LINK, SCRIPT))
    if BIN_DIR not in os.environ.get("PATH", "").split(os.pathsep):
        print("note: %s is not on your PATH; the .zshrc block needs it there" % BIN_DIR)

    text = strip_block(read_zshrc()).rstrip("\n")
    with open(ZSHRC, "w") as f:
        f.write(text + "\n\n" + BLOCK if text else BLOCK)
    print("added the resume block to the end of %s" % ZSHRC)
    print(
        "\nGhostty must restore its windows for panes to come back:\n"
        "  window-save-state = always   in your Ghostty config\n"
        "\nSessions running right now have no record yet; register them with\n"
        "  claude-ghostty-resume import-live"
    )


def uninstall():
    if os.path.lexists(COMMAND_LINK):
        os.remove(COMMAND_LINK)
        print("removed %s" % COMMAND_LINK)
    text = read_zshrc()
    stripped = strip_block(text)
    if stripped != text:
        with open(ZSHRC, "w") as f:
            f.write(stripped)
        print("removed the resume block from %s" % ZSHRC)
    print("Session records in ~/.claude/ghostty-resume were left in place.")


if __name__ == "__main__":
    if "--uninstall" in sys.argv[1:]:
        uninstall()
    else:
        install()
