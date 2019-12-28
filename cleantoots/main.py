import configparser
import os
import pathlib

import click
import pendulum
from mastodon import Mastodon

from cleantoots import config as config_commands

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


cli.add_command(config_commands.config)


@cli.command()
@click.option(
    "--delete",
    help="Delete toots that match the rules without confirmation. This is a destructive operation. "
    "Without this flags, toots will only be listed.",
    is_flag=True,
)
@click.pass_obj
def clean(delete, config):
    """
    Delete Toots based on rules in config file.

    Without the `--delete` flag, toots will only be displayed.
    """
    for section in config.sections():
        section = config[section]
        user_secret_file = config.file(section.get("user_secret_file"))
        mastodon = Mastodon(access_token=user_secret_file)
        user = mastodon.me()
        page = mastodon.account_statuses(user["id"])
        would_delete = []
        while page:
            for toot in page:
                if (
                    toot["reblogs_count"] >= section.getint("boost_limit")
                    or toot["favourites_count"] >= section.getint("favorite_limit")
                    or toot["id"]
                    in map(int, section.get("protected_toots", "").split())
                    or toot["created_at"]
                    >= pendulum.now(tz=section.get("timezone")).subtract(
                        days=section.getint("days_count")
                    )
                ):
                    continue
                would_delete.append(toot)

            page = mastodon.fetch_next(page)

        if not delete:
            if not would_delete:
                click.secho("No toot would be deleted given the rules.", fg="blue")
                return
            click.secho(
                "Would delete {count} toots:".format(count=len(would_delete)), fg="blue"
            )
            for toot in would_delete:
                click.echo(toot["id"])
                click.echo(toot["content"])
                click.echo()
        else:
            click.echo("Deleting toots...")
            with click.progressbar(would_delete) as bar:
                for toot in bar:
                    mastodon.status_delete(toot)
                    click.secho("Deleted toot {}".format(toot["id"]), fg="green")


if __name__ == "__main__":
    cli()
