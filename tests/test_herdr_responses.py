from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import subprocess
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "git-wt"
LOADER = SourceFileLoader("git_wt", str(SCRIPT))
SPEC = spec_from_loader("git_wt", LOADER)
assert SPEC is not None
git_wt = module_from_spec(SPEC)
LOADER.exec_module(git_wt)


class HerdrResponseTests(unittest.TestCase):
    def test_normalizes_bare_ticket_number(self):
        self.assertEqual(git_wt._normalize_from_target("605"), "TES-605")

    def test_leaves_explicit_targets_intact(self):
        self.assertEqual(git_wt._normalize_from_target("tes-605"), "TES-605")
        self.assertEqual(git_wt._normalize_from_target("pr"), "PR")

    def test_successful_agent_exit_hands_off_to_a_shell(self):
        command = git_wt._bootstrap_launcher_command("true")
        result = subprocess.run(
            ["/bin/sh", "-lc", command],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertNotIn("Bootstrap failed", result.stdout)
        self.assertTrue(command.endswith('exec "${SHELL:-/bin/sh}"'))

    def test_extracts_created_workspace_id(self):
        response = {
            "result": {
                "type": "workspace_created",
                "workspace": {"workspace_id": "w4G"},
            }
        }

        self.assertEqual(git_wt._herdr_created_workspace_id(response), "w4G")

    def test_extracts_started_agent_pane_id(self):
        response = {
            "result": {
                "type": "agent_started",
                "agent": {"pane_id": "w4G:p2"},
            }
        }

        self.assertEqual(git_wt._herdr_started_agent_pane_id(response), "w4G:p2")


if __name__ == "__main__":
    unittest.main()
