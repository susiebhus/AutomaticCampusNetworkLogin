from pathlib import Path
import tempfile
import unittest

from njust_campus_login.core import Credentials, get_credentials, parse_credentials_file


class CredentialsTest(unittest.TestCase):
    def write_temp(self, body: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "password.txt"
        path.write_text(body, encoding="utf-8")
        return path

    def test_parse_env_style_file(self) -> None:
        path = self.write_temp('CAMPUS_USER="alice"\nCAMPUS_PASS="secret"\n')
        self.assertEqual(parse_credentials_file(path), Credentials("alice", "secret"))

    def test_parse_label_style_file(self) -> None:
        path = self.write_temp("account\nbob\npassword\nhunter2\n")
        self.assertEqual(parse_credentials_file(path), Credentials("bob", "hunter2"))

    def test_parse_two_line_file(self) -> None:
        path = self.write_temp("carol\ns3cr3t\n")
        self.assertEqual(parse_credentials_file(path), Credentials("carol", "s3cr3t"))

    def test_args_override_file(self) -> None:
        path = self.write_temp("carol\ns3cr3t\n")
        credentials = get_credentials(path, username="dave", password="pw", emit=lambda _: None)
        self.assertEqual(credentials, Credentials("dave", "pw"))


if __name__ == "__main__":
    unittest.main()
