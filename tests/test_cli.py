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
            self.assertEqual(0, result.exit_code)
            self.assertIn("config.ini written", result.output)
            self.assertTrue(os.path.isfile(os.path.join(".", "config.ini")))

    def test_setup_config_twice_fails(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            self.assertTrue(os.path.isfile(os.path.join(".", "config.ini")))
            result = self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            self.assertEqual(0, result.exit_code)
            self.assertIn("Not touching anything", result.output)
            self.assertIn("cleantoots config edit", result.output)

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
                self.assertIn(exp, result.output)

    def test_config_list_no_file(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["-d", ".", "config", "list"])
            self.assertIn("cleantoots config setup", result.output)
            self.assertEqual(0, result.exit_code)

    def test_config_edit_no_file(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["-d", ".", "config", "edit"])
            self.assertIn("cleantoots config setup", result.output)
            self.assertEqual(0, result.exit_code)

    def test_login_output(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "config", "setup"])
            result = self.runner.invoke(
                cli, ["-d", ".", "config", "login"], input="\nFAKECODE"
            )
            self.assertIn("Enter code for", result.output)

    def test_clean_exists(self):
        result = self.runner.invoke(cli, ["-d", ".", "clean"])
        self.assertEqual(0, result.exit_code)


if __name__ == "__main__":
    unittest.main()
