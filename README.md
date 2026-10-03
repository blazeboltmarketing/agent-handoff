# agent-handoff

**Auto-compaction lets your agent decide what it remembers. A handoff lets you decide.**

When a long agent session gets heavy, don't compact it. Type `/handoff`. The
agent writes a header and six lines of checked state: the goal, what is proven done, what
already failed, the exact next step, the one open question, and a shell
command that says when the task is finished. Then you start a fresh session
that picks up from that file. Nothing gets lost in a summary, nothing gets
re-asked, and every turn after it is cheaper.

Works with any agent that loads [Agent Skills](https://agentskills.io) or reads
[AGENTS.md](https://agents.md). Tested on Claude Code 2.1.288 and Codex CLI 0.159.3.

## Why not compaction

- A compacted summary is the model summarizing itself, mid-task. The exact
  error, the approach you already rejected, the decision from an hour ago:
  those are what drop out.
- A handoff file is short. You can read it, fix it, and trust it before you
  clear.
- `Done when:` turns "finished" into a command instead of a feeling. Once it
  passes, the hook archives the file so the next handoff starts clean.
- A fresh session re-reads a few hundred tokens of state, not 150k of history,
  on every turn.

## The file

```
# Handoff — <task> — <YYYY-MM-DD HH:MM>
Goal: <one sentence, the finished state>
Done: <what is verified done, with the check that proved it>
Dead ends: <what was tried and rejected, one line each, with why>
Next action: <the exact first step: file:line or command>
Open: <the one question only you can answer, or "none">
Done when: <one shell command; exit 0 = finished>
```

The full rules live in [`skills/handoff/SKILL.md`](skills/handoff/SKILL.md).
A project can keep its state in a tracked document instead (named in its
AGENTS.md, e.g. `docs/decisions.md`). That document is kept current, never
archived; the hook only handles `HANDOFF.md`.

## Install

Every level is optional on top of the one before it. Add this to each
project's `.gitignore` either way:

```
HANDOFF.md
.handoff-archive/
```

### 1. Any agent: the skill and an AGENTS.md rule

```bash
git clone https://github.com/blazeboltmarketing/agent-handoff ~/agent-handoff
# Codex, Cursor, Copilot, Gemini CLI, OpenCode, Amp, Goose:
mkdir -p ~/.agents/skills && ln -sfn ~/agent-handoff/skills/handoff ~/.agents/skills/handoff
# Claude Code, unless you use the plugin below (it ships the skill too):
mkdir -p ~/.claude/skills && ln -sfn ~/agent-handoff/skills/handoff ~/.claude/skills/handoff
```

Then paste [`snippets/agents-md.md`](snippets/agents-md.md) into your
project's `AGENTS.md`, so the next session reads the handoff first even
without a hook. Run it with `/handoff`, or `$handoff` in Codex.

### 2. Session-start hook: resume and archive automatically

[`hooks/handoff_hook.py`](hooks/handoff_hook.py) (Python 3, standard library)
tells the new session to read `HANDOFF.md` first, and archives the file once
its `Done when:` check passes.

For Claude Code pick ONE of the plugin or the by-hand setup; both together
run the hook twice.

**Claude Code, as a plugin** (skill and hook together; skip the
`~/.claude/skills` link above):

```
/plugin marketplace add blazeboltmarketing/agent-handoff
/plugin install agent-handoff@agent-handoff
```

**Claude Code, by hand**: merge this into `~/.claude/settings.json`. If you
already have `hooks` or `SessionStart`, add the entry to the existing array
instead of replacing it:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "python3 ~/agent-handoff/hooks/handoff_hook.py", "timeout": 15 }] }
    ]
  }
}
```

**Codex**: merge the same way into `~/.codex/hooks.json`, then run `/hooks`
once to trust it:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "python3 ~/agent-handoff/hooks/handoff_hook.py", "timeout": 15 }] }
    ]
  }
}
```

Other harnesses with a session-start hook (Gemini CLI, Copilot CLI) should
work the same way but are untested. A PR with a tested config is welcome.

### 3. Claude Code extra: a context meter

[`extras/statusline.sh`](extras/statusline.sh) shows context used, and turns
red with `→ /handoff` past 120k tokens (`HANDOFF_AT` to change it). It
replaces any statusline you already have:

```json
"statusLine": { "type": "command", "command": "bash ~/agent-handoff/extras/statusline.sh" }
```

## Safety

- The hook runs a `Done when:` command only when `HANDOFF.md` is **not
  tracked by git**. A repository you clone cannot ship a command that your
  agent runs at startup.
- It fails safe: no check, a failing check, a 10-second timeout or any error
  leaves the file where it is.
- The skill is user-only: `disable-model-invocation` (Claude Code, Cursor) and
  `agents/openai.yaml` (Codex) stop the agent from starting a handoff on its
  own. Elsewhere, the skill's description says so.
- `HANDOFF_DISABLED=1` turns the hook off.

## Develop

```bash
python3 -m unittest discover tests
```

## License

[MIT](LICENSE)
