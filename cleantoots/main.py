import configparser
import os
import pathlib
import sys

import click
import pendulum
from click import Abort
from mastodon import Mastodon

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


@cli.command()
@click.pass_obj
def setup_config(config):
    """Initial setup for configuration directories and files."""
    os.makedirs(config.dir, exist_ok=True)
    if os.path.isfile(config.main_file):
        click.secho(
            "{} found. Not touching anything.".format(config.main_file), fg="red"
        )
        raise Abort()

    default_config = configparser.ConfigParser()
    default_config["DEFAULT"] = {
        "boost_limit": 5,
        "favorite_limit": 5,
        "days_count": 30,
        "timezone": "Europe/Paris",
    }
    default_config["Mastodon.social"] = {
        "api_base_url": "https://mastodon.social",
        "app_secret_file": "mastodon_social_app.secret",
        "user_secret_file": "mastodon_social_user.secret",
        "protected_toots": "1234\n5678",
    }
    with open(config.main_file, "w") as _file:
        default_config.write(_file)
        click.secho("{} written.".format(config.main_file), fg="green")
    click.echo()
    click.secho("Next steps", bold=True)
    click.echo(
        "You'll need to edit the config file in order to set some settings such as:"
    )
    click.echo("* The base URL of your Mastodon instance")
    click.echo("* The toots you want to protect")
    if sys.stdout.isatty() and sys.stdin.isatty():
        click.echo()
        click.secho("We're going to open the file for you now.")
        click.pause()
        click.edit(filename=config.main_file)


@cli.command()
@click.pass_obj
def config(config):
    """Display parsed config."""
    for section_name in config.sections():
        click.secho(section_name, bold=True)
        section = config[section_name]
        for key, value in section.items():
            click.secho("{} = {}".format(key, value))
        click.echo()


@cli.command()
@click.pass_obj
def login(config):
    """Fetch credentials for each app described in config file."""
    for section in config.sections():
        section = config[section]
        Mastodon.create_app(
            "cleantoots",
            api_base_url=section.get("api_base_url"),
            to_file=config.file(section.get("app_secret_file")),
        )
        mastodon = Mastodon(client_id=config.file(section.get("app_secret_file")))
        if sys.stdout.isatty() and sys.stdin.isatty():
            click.echo(
                "We will now open a browser for each account set in the config file."
            )
            click.echo(
                "You'll need to authenticate and then copy the code provided in the web "
                "page back into this terminal, upon prompt."
            )
            click.pause()
            click.launch(mastodon.auth_request_url())
        else:
            click.echo(
                "Go to {}, authenticate and enter the code below.".format(
                    mastodon.auth_request_url()
                )
            )
        code = click.prompt("Enter code for {}".format(section.get("api_base_url")))
        mastodon.log_in(code=code, to_file=config.file(section.get("user_secret_file")))


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
