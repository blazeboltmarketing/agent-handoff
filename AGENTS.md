# AGENTS.md

- The handoff rules have one home: `skills/handoff/SKILL.md`. The README
  shows the format but links there for the rules; don't fork them.
- `hooks/handoff_hook.py` stays standard-library Python 3 and harness-neutral:
  read a JSON payload with `cwd` on stdin, print plain text.
- Never weaken the tracked-file guard: a `Done when:` command runs only for an
  untracked `HANDOFF.md`.
- Run `python3 -m unittest discover tests` before every commit.
