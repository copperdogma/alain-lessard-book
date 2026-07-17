from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.deploy_static_site import run_sftp


class FakeSftpChild:
    def __init__(self, *, exitstatus: int | None, transcript: str) -> None:
        self._final_exitstatus = exitstatus
        self.before = transcript
        self.after = ""
        self.exitstatus: int | None = None
        self.signalstatus: int | None = None
        self.closed = False

    def expect(self, _patterns: list[object]) -> int:
        return 2  # pexpect.EOF

    def sendline(self, _value: str) -> None:
        raise AssertionError("The EOF-only fixture should not prompt for input.")

    def close(self) -> None:
        self.closed = True
        self.exitstatus = self._final_exitstatus


class DeployStaticSiteTests(unittest.TestCase):
    def test_run_sftp_rejects_connection_failure_after_eof(self) -> None:
        child = FakeSftpChild(
            exitstatus=255,
            transcript="ssh: Could not resolve hostname example.test\nConnection closed\n",
        )
        with patch("scripts.deploy_static_site.pexpect.spawn", return_value=child):
            with self.assertRaisesRegex(SystemExit, "SFTP exited with 255"):
                run_sftp("ls\n", "example.test", "reader", "secret")
        self.assertTrue(child.closed)

    def test_run_sftp_accepts_zero_exit_after_waiting_for_child(self) -> None:
        child = FakeSftpChild(exitstatus=0, transcript="sftp> ls index.html\nindex.html\n")
        with patch("scripts.deploy_static_site.pexpect.spawn", return_value=child):
            transcript = run_sftp("ls\n", "example.test", "reader", "secret")
        self.assertTrue(child.closed)
        self.assertIn("index.html", transcript)


if __name__ == "__main__":
    unittest.main()
