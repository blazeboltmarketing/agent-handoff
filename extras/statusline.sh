#!/usr/bin/env bash
# Claude Code statusline: context used/size, red with "→ /handoff" past HANDOFF_AT
# tokens (default 120000). settings.json: "statusLine": {"type": "command",
# "command": "bash /path/to/statusline.sh"}
python3 -c '
import json, os, sys
d = json.load(sys.stdin)
cw = d.get("context_window") or {}
size = cw.get("context_window_size")
used = (cw.get("total_input_tokens") or 0) + (cw.get("total_output_tokens") or 0)
k = lambda n: f"{n / 1000:.0f}k"
if not size:
    print("ctx ?")
elif used > int(os.environ.get("HANDOFF_AT", "120000")):
    print(f"\033[1;31mctx {k(used)}/{k(size)} → /handoff\033[0m")
else:
    print(f"\033[1;36mctx {k(used)}/{k(size)}\033[0m \033[2m({k(size - used)} left)\033[0m")
' 2>/dev/null || echo "ctx ?"
