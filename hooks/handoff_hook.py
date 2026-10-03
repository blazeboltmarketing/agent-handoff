#!/usr/bin/env python3
"""Session-start hook for agent-handoff.

Reads a JSON payload with `cwd` on stdin. If HANDOFF.md exists at the
repository root, prints one line telling the agent to read it, or archives it
to .handoff-archive/ once its `Done when:` command exits 0. That command runs
only when HANDOFF.md is not tracked by git, so a cloned repository can never
make your agent run a command it shipped. Any failure leaves the file in place.

Env: HANDOFF_DISABLED=1 turns it off; HANDOFF_DONE_TIMEOUT sets the check
timeout in seconds (default 10).
"""

import json
import os
import re
import signal
import subprocess
import sys
import time


def repo_root(cwd):
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else cwd
    except (OSError, subprocess.SubprocessError):
        return cwd


def tracked(root, name):
    try:
        return subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", name],
                              capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def done(path, root):
    with open(path, encoding="utf-8", errors="replace") as fh:
        m = re.search(r"^Done when:\s*(.+?)\s*$", fh.read(), re.M)
    if not m:
        return False
    try:
        proc = subprocess.Popen(m.group(1), shell=True, cwd=root, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        try:
            return proc.wait(timeout=float(os.environ.get("HANDOFF_DONE_TIMEOUT", "10"))) == 0
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            return False
    except (OSError, ValueError):
        return False


def main():
    if os.environ.get("HANDOFF_DISABLED") == "1":
        return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    root = repo_root(payload.get("cwd") or os.getcwd())
    path = os.path.join(root, "HANDOFF.md")
    if not os.path.isfile(path):
        return 0
    if tracked(root, "HANDOFF.md"):
        print("Handoff: HANDOFF.md is tracked by git, so its Done-when check was not run. "
              "Read it first and continue from its Next action.")
        return 0
    if done(path, root):
        rel = os.path.join(".handoff-archive", time.strftime("HANDOFF-%Y-%m-%d-%H%M%S.md"))
        try:
            os.makedirs(os.path.join(root, ".handoff-archive"), exist_ok=True)
            os.replace(path, os.path.join(root, rel))
            print(f"Handoff: the work in HANDOFF.md is done (its check passed); archived to {rel}.")
            return 0
        except OSError:
            pass
    age = (time.time() - os.path.getmtime(path)) / 3600
    print(f"Handoff: state in HANDOFF.md (updated {age:.0f}h ago). Read it first and continue "
          "from its Next action. Only the user starts a new handoff.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
