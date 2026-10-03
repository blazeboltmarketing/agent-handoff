---
name: handoff
description: User-invoked only. Run when the user types /handoff (Codex - $handoff) or explicitly asks for a handoff; never on your own initiative, never because the context is getting long. Saves the state the next session needs (goal, done, dead ends, next action, open question, a done-check) to HANDOFF.md, then tells the user to start a fresh session. A state file, never a transcript or a summary of the conversation.
license: MIT
disable-model-invocation: true
---

# /handoff — state to a file, then a fresh session

Every turn re-reads the whole conversation, so a long session costs more per
step and drifts. Auto-compaction "fixes" that with a summary the agent writes
about itself, and the details that matter get lost. A handoff is the opposite:
a few lines of checked state the user can read, edit and trust, and a clean
session that starts from them. The handoff itself takes 10-15k tokens, so run
it while there is headroom.

## Where the state goes

1. If the project's AGENTS.md names a tracked state document (e.g.
   `docs/decisions.md`), update its current-work section in place.
2. Otherwise `HANDOFF.md` at the repository root. Keep it out of git: add
   `HANDOFF.md` and `.handoff-archive/` to `.gitignore`. It is working state,
   and the session-start hook only runs the `Done when:` check on an
   untracked file.

## What it contains

Six lines. Expand a line only where the next session would otherwise have to
work something out again.

```
# Handoff — <task> — <YYYY-MM-DD HH:MM>
Goal: <one sentence, the finished state>
Done: <what is verified done, with the check that proved it>
Dead ends: <what was tried and rejected, one line each, with why>
Next action: <the exact first step: file:line or command>
Open: <the one question only the user can answer, or "none">
Done when: <one shell command; exit 0 = finished>
```

`Done when:` is ONE deterministic, read-only check, run from the repository
root, that passes exactly when the task is finished, for example
`git merge-base --is-ancestor my-branch main` or
`test -f dist/app.js && npm test --silent`. Run it once before saving: the
work is unfinished, so it must fail now.

## Steps

1. Commit uncommitted work on the working branch. A preservation commit is
   not permission to merge, push or deploy.
2. Write the state file. If it is a tracked state document, commit it.
3. Print a starting prompt for the next session in one fenced block the user
   can paste: the state file to read first, the goal in one line, the pending
   next actions in order (mark anything irreversible "ask first"), and the
   decisions already made so nothing gets asked again. No history, no
   done-list; the state file holds that.
4. Check that it is safe to close: state saved, no uncommitted tracked
   changes in any repository you touched, no background job the next session
   depends on still running. All pass: end with
   **"state saved — safe to close — start a fresh session when ready"**.
   Any fail: say **"NOT safe to close"** and name what is still open.
5. Stop. Do not start the next action.

## Next session

Read `HANDOFF.md` first and do its next action. Once its `Done when:` check
exits 0, move it to `.handoff-archive/HANDOFF-<YYYY-MM-DD-HHMM>.md` so the
next handoff starts clean. The session-start hook in this repository does
both automatically where it is installed.
