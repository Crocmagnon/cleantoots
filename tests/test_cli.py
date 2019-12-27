import os
import unittest

from click.testing import CliRunner

from cleantoots.main import cli


class SetupConfigTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_setup_config(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["-d", ".", "setup-config"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("config.ini written", result.output)
            self.assertTrue(os.path.isfile(os.path.join(".", "config.ini")))

    def test_setup_config_twice_fails(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "setup-config"])
            self.assertTrue(os.path.isfile(os.path.join(".", "config.ini")))
            result = self.runner.invoke(cli, ["-d", ".", "setup-config"])
            self.assertEqual(result.exit_code, 1)
            self.assertIn("Not touching anything", result.output)

    def test_config_output(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "setup-config"])
            result = self.runner.invoke(cli, ["-d", ".", "config"])
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

    def test_login_output(self):
        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["-d", ".", "setup-config"])
            result = self.runner.invoke(cli, ["-d", ".", "login"], input="\nFAKECODE")
            self.assertIn("Enter code for", result.output)


if __name__ == "__main__":
    unittest.main()
