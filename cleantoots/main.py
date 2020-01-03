import logging.config
import os
import sys

import click

from cleantoots.commands import clean as clean_commands, config as config_commands
from cleantoots.utils import CleanTootsConfig

DEFAULT_CONFIG_DIR = click.get_app_dir("cleantoots")
DEFAULT_CONFIG_FILENAME = "config.ini"

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


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
@click.version_option(version=__import__("cleantoots").__version__)
@click.pass_context
def cli(ctx, config_dir, config_file):
    """
    Provide an easy interface for deleting old toots.

    \b
    Steps, in order:
    1. run `config setup`
    2. run `login`
    3. run `clean --delete`
    """
    ctx.obj = CleanTootsConfig(config_dir, config_file)
    log_file = os.path.join(config_dir, "cleantoots.log")
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "precise": {
                    "format": "{asctime} | {name} | {levelname} | {message}",
                    "style": "{",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "level": "INFO",
                    "formatter": "precise",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": log_file,
                    "maxBytes": 1024 * 100,
                    "backupCount": 3,
                    "level": "INFO",
                    "formatter": "precise",
                },
            },
            "loggers": {
                "cleantoots": {"level": "INFO", "handlers": ["console", "file"]}
            },
        }
    )


cli.add_command(config_commands.config_command)
cli.add_command(clean_commands.clean)

if __name__ == "__main__":
    cli()
