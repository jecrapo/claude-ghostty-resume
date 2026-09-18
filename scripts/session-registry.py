#!/usr/bin/env python3
"""Record interactive Claude Code sessions so a restored Ghostty pane can resume them.

SessionStart hook: upsert a record for the session and drop any claim marker
                   left by the pane that resumed it.
SessionEnd hook:   delete the record on a deliberate exit, otherwise mark how
                   it ended. Quitting Ghostty hangs up the shell, which ends
                   the session with reason "other" or with no hook at all, so
                   those records survive and are what a restored pane claims.

Usage: session-registry.py start|end   (hook JSON on stdin)
"""
import json
import os
import sys
import time

REGISTRY_DIR = os.path.expanduser("~/.claude/ghostty-resume")
COMMAND_LINK = os.path.expanduser("~/.local/bin/claude-ghostty-resume")
PLUGIN_CACHE = os.path.expanduser("~/.claude/plugins/")
DELIBERATE_END_REASONS = {"clear", "logout", "prompt_input_exit", "resume"}


def refresh_command_link():
    """Plugin updates land in a new versioned directory, which would strand the
    command symlink that setup created; repoint it whenever it lags behind."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not root or not os.path.islink(COMMAND_LINK):
        return
    current = os.readlink(COMMAND_LINK)
    wanted = os.path.join(root, "scripts", "claude-ghostty-resume")
    if current == wanted or not current.startswith(PLUGIN_CACHE):
        return
    tmp = COMMAND_LINK + ".tmp"
    os.symlink(wanted, tmp)
    os.replace(tmp, COMMAND_LINK)


def record_path(session_id):
    return os.path.join(REGISTRY_DIR, session_id + ".json")


def claim_path(session_id):
    return os.path.join(REGISTRY_DIR, session_id + ".claim")


def write_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def remove_quietly(path):
    try:
        os.remove(path)
    except OSError:
        pass


def on_start(payload):
    entrypoint = os.environ.get("CLAUDE_CODE_ENTRYPOINT")
    if entrypoint not in (None, "cli"):
        return
    session_id = payload["session_id"]
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    path = record_path(session_id)
    record = load(path)
    record.update(
        {
            "session_id": session_id,
            "cwd": payload.get("cwd"),
            "transcript_path": payload.get("transcript_path"),
            "title": payload.get("session_title") or record.get("title"),
            "entrypoint": entrypoint,
            "last_start_source": payload.get("source"),
            "updated_at": int(time.time()),
            "ended_at": None,
            "end_reason": None,
        }
    )
    record.setdefault("started_at", record["updated_at"])
    write_atomic(path, record)
    remove_quietly(claim_path(session_id))


def on_end(payload):
    session_id = payload["session_id"]
    path = record_path(session_id)
    if not os.path.exists(path):
        return
    if payload.get("reason") in DELIBERATE_END_REASONS:
        os.remove(path)
        remove_quietly(claim_path(session_id))
        return
    record = load(path)
    record["ended_at"] = int(time.time())
    record["end_reason"] = payload.get("reason")
    write_atomic(path, record)


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = json.load(sys.stdin)
    if event == "start":
        refresh_command_link()
        on_start(payload)
    elif event == "end":
        on_end(payload)
    else:
        sys.exit("usage: session-registry.py start|end")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a registry failure must never block a session
        print("session-registry: %s" % exc, file=sys.stderr)
    sys.exit(0)
