import configparser
import os
import pathlib

import click

from cleantoots.commands import clean as clean_commands, config as config_commands

HOME = pathlib.Path.home()
DEFAULT_CONFIG_DIR = click.get_app_dir("cleantoots")
DEFAULT_CONFIG_FILENAME = "config.ini"
EDITOR = os.getenv("EDITOR", "vim")

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class CleanTootsConfig(configparser.ConfigParser):
    def __init__(self, config_dir, config_file_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dir = config_dir
        self.main_file = os.path.join(config_dir, config_file_name)
        self.read(self.main_file)

    def file(self, filename):
        return os.path.join(self.dir, filename)

    def isfile(self, filename):
        return os.path.isfile(self.file(filename))


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-d",
    "--config-dir",
    help="Custom configuration directory.",
    default=DEFAULT_CONFIG_DIR,
    show_default=True,
)
@click.option(
    "-c",
    "--config-file",
    help="Custom configuration file name. "
    "Must only contain the filename, not the whole path.",
    default=DEFAULT_CONFIG_FILENAME,
    show_default=True,
)
@click.version_option()
@click.pass_context
def cli(ctx, config_dir, config_file):
    """
    Provide an easy interface for deleting old toots.

    \b
    Steps, in order:
    1. run `setup-config`
    2. run `login`
    3. run `clean --delete`
    """
    ctx.obj = CleanTootsConfig(config_dir, config_file)


cli.add_command(config_commands.config_command)
cli.add_command(clean_commands.clean)

if __name__ == "__main__":
    cli()
