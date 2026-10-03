"""Run: python3 -m unittest discover tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "handoff_hook.py"


def run(cwd, **env):
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"cwd": str(cwd)}),
                          capture_output=True, text=True, timeout=30,
                          env={**os.environ, "HANDOFF_DONE_TIMEOUT": "2", **env})


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t",
                    "-c", "core.hooksPath=/dev/null", *args], check=True, capture_output=True)


def handoff(cwd, done_line):
    body = "# Handoff — t\nGoal: g\n" + (f"Done when: {done_line}\n" if done_line else "")
    (Path(cwd) / "HANDOFF.md").write_text(body)
    return body


class HookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        git(self.d, "init", "-q")

    def tearDown(self):
        self.tmp.cleanup()

    def archived(self):
        return list((self.d / ".handoff-archive").glob("HANDOFF-*.md"))

    def test_silent_without_handoff(self):
        r = run(self.d)
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_unfinished_handoff_is_surfaced(self):
        for line in ("false", None, "sleep 5"):   # failing, missing, timed-out check
            with self.subTest(line=line):
                body = handoff(self.d, line)
                r = run(self.d)
                self.assertIn("Handoff: state in HANDOFF.md", r.stdout)
                self.assertEqual(((self.d / "HANDOFF.md").read_text(), self.archived()), (body, []))

    def test_done_handoff_is_archived(self):
        handoff(self.d, "true")
        r = run(self.d)
        self.assertIn("archived to .handoff-archive/", r.stdout)
        self.assertFalse((self.d / "HANDOFF.md").exists())
        self.assertRegex(self.archived()[0].name, r"^HANDOFF-\d{4}-\d{2}-\d{2}-\d{6}\.md$")

    def test_found_from_a_subdirectory(self):
        handoff(self.d, "false")
        (self.d / "src").mkdir()
        self.assertIn("Handoff: state in HANDOFF.md", run(self.d / "src").stdout)

    def test_tracked_handoff_never_runs_its_command(self):
        handoff(self.d, "touch ran && true")
        git(self.d, "add", "HANDOFF.md")
        git(self.d, "commit", "-qm", "ship a handoff")
        r = run(self.d)
        self.assertIn("tracked by git", r.stdout)
        self.assertFalse((self.d / "ran").exists())
        self.assertEqual(self.archived(), [])

    def test_disabled(self):
        handoff(self.d, "true")
        self.assertEqual(run(self.d, HANDOFF_DISABLED="1").stdout, "")
        self.assertTrue((self.d / "HANDOFF.md").exists())


if __name__ == "__main__":
    unittest.main()
