## Handoff

- At session start, if `HANDOFF.md` exists at the repository root, read it
  first and continue from its `Next action:`. Do not re-ask decisions it
  records.
- Its `Done when:` line is a shell check. Run it only if `HANDOFF.md` is not
  tracked by git (`git ls-files --error-unmatch HANDOFF.md` fails) and the
  command is a read-only check. If it exits 0, move the file to
  `.handoff-archive/HANDOFF-<YYYY-MM-DD-HHMMSS>.md` and say so.
- Only the user starts a handoff (`/handoff`). Never start one yourself.
