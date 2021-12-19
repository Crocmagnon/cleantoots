import os
import unittest

from click.testing import CliRunner

from cleantoots.main import cli


class SetupConfigTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_setup_config(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            assert result.exit_code == 0
            assert "config.ini written" in result.output
            assert os.path.isfile(os.path.join(".", "config.ini"))

    def test_setup_config_twice_fails(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            assert os.path.isfile(os.path.join(".", "config.ini"))
            result = self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            assert result.exit_code == 0
            assert "Not touching anything" in result.output
            assert "cleantoots config edit" in result.output

    def test_config_output(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            result = self.runner.invoke(cli, ["-d", ".", "config", "list"])
            expected = [
                "Mastodon.social",
                "api_base_url",
                "app_secret_file",
                "user_secret_file",
                "protected_toots",
                "boost_limit",
                "favorite_limit",
                "days_count",
                "timezone",
            ]
            for exp in expected:
                assert exp in result.output

    def test_config_list_no_file(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["-d", ".", "config", "list"])
            assert "cleantoots config setup" in result.output
            assert result.exit_code == 0

    def test_config_edit_no_file(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["-d", ".", "config", "edit"])
            assert "cleantoots config setup" in result.output
            assert result.exit_code == 0

    def test_login_output(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            result = self.runner.invoke(
                cli, ["-d", ".", "config", "login"], input="\nFAKECODE"
            )
            assert "Enter code for" in result.output

    def test_clean_exists(self):
        result = self.runner.invoke(cli, ["-d", ".", "clean"])
        assert result.exit_code == 0


if __name__ == "__main__":
    unittest.main()
