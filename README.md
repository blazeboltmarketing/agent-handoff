# agent-handoff

**Start a fresh agent session without losing your place.**

Long agent sessions get slow, then they compact and forget things: the error
you were fixing, the approach you already ruled out, what you decided. So you
explain it all again.

Type `/handoff` instead. The agent saves where you are to a short file: the
goal, what's done, what didn't work, and the next step. Start a fresh session
and it picks up right where you left off, without the re-explaining.

Works with any agent that loads [Agent Skills](https://agentskills.io) or reads
[AGENTS.md](https://agents.md). Tested on Claude Code 2.1.288 and Codex CLI 0.159.3.

## Why not compaction

Compaction is the agent summarizing itself, and you can't see what it left out.
A handoff is a file you can read and fix before you start over, so you decide
what carries over. A fresh session is also cheaper, because every turn
re-reads the whole conversation.

The file ends with a `Done when:` check. Once the work passes it, the hook
archives the file.

## The file

```
# Handoff — <task> — <YYYY-MM-DD HH:MM>
Goal: <one sentence, the finished state>
Done: <what is verified done, with the check that proved it>
Dead ends: <what was tried and rejected, one line each, with why>
Next action: <the exact first step: file:line or command>
Open: <the one question only the user can answer, or "none">
Done when: <one shell command; exit 0 = finished>
```

The rules are in [`skills/handoff/SKILL.md`](skills/handoff/SKILL.md). A
project can keep its state in a tracked document instead, named in its
AGENTS.md (say `docs/decisions.md`). The agent keeps that document current and
never archives it; the hook only touches `HANDOFF.md`.

## Install

Each level is optional and builds on the one before. Either way, add this to
each project's `.gitignore`:

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
project's `AGENTS.md` so the next session reads the handoff first, even
without a hook. Run it with `/handoff`, or `$handoff` in Codex.

### 2. Session-start hook: resume and archive automatically

[`hooks/handoff_hook.py`](hooks/handoff_hook.py) (Python 3, standard library only)
tells the new session to read `HANDOFF.md` first and archives the file once
its `Done when:` check passes.

For Claude Code, pick ONE of the plugin or the by-hand setup. With both, the
hook runs twice.

**Claude Code, as a plugin.** It ships the skill and the hook, so skip the
`~/.claude/skills` link above:

```
/plugin marketplace add blazeboltmarketing/agent-handoff
/plugin install agent-handoff@agent-handoff
```

**Claude Code, by hand.** Merge this into `~/.claude/settings.json`. If you
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

**Codex.** Merge the same way into `~/.codex/hooks.json`, then run `/hooks`
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
work the same way, but I haven't tested them. A PR with a tested config is
welcome.

### 3. Claude Code extra: a context meter

[`extras/statusline.sh`](extras/statusline.sh) shows context used and turns
red with `→ /handoff` past 120k tokens (set `HANDOFF_AT` to change that). It
replaces any statusline you already have:

```json
"statusLine": { "type": "command", "command": "bash ~/agent-handoff/extras/statusline.sh" }
```

## Safety

The hook runs a `Done when:` command only when `HANDOFF.md` is **not tracked
by git**, so a repository you clone cannot ship a command that your agent runs
at startup. It fails safe: no check, a failing check, a 10-second timeout or
any error leaves the file where it is. `HANDOFF_DISABLED=1` turns the hook
off.

The skill is user-only. `disable-model-invocation` (Claude Code, Cursor) and
`agents/openai.yaml` (Codex) stop the agent from starting a handoff on its
own; elsewhere, the skill's description tells it not to.

## Develop

```bash
python3 -m unittest discover tests
```

## License

[MIT](LICENSE)
