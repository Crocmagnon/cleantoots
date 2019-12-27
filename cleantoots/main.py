import configparser
import functools
import os
import pathlib
import subprocess
import webbrowser

import click
import pendulum
from mastodon import Mastodon


def config_file(filename):
    return os.path.join(CONFIG_DIR, filename)


HOME = pathlib.Path.home()
CONFIG_DIR = click.get_app_dir("cleantoots")
CONFIG_FILE = config_file("config.ini")
EDITOR = os.getenv("EDITOR", "vim")


@click.group()
def cli():
    """
    Provide an easy interface for deleting old toots.

    Steps, in order:

    1. run `setup-config`

    2. run `login`

    3. run `clean --delete`
    """
    pass


def load_config(function):
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    func = functools.partial(function, config=config)
    func.__name__ = function.__name__
    func.__doc__ = function.__doc__
    return func


@cli.command()
def setup_config():
    """Initial setup for configuration directories and files."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.isfile(CONFIG_FILE):
        click.secho("{} found. Not touching anything.".format(CONFIG_FILE), fg="red")
        return

    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "boost_limit": 5,
        "favorite_limit": 5,
        "days_count": 30,
        "timezone": "Europe/Paris",
    }
    config["Mastodon.social"] = {
        "api_base_url": "https://mastodon.social",
        "app_secret_file": "mastodon_social_app.secret",
        "user_secret_file": "mastodon_social_user.secret",
        "protected_toots": "1234\n5678",
    }
    with open(CONFIG_FILE, "w") as _file:
        config.write(_file)
        click.secho("{} written.".format(CONFIG_FILE), fg="green")
    click.echo()
    click.secho("Next steps", bold=True)
    click.echo(
        "You'll need to edit the config file in order to set some settings such as:"
    )
    click.echo("* The base URL of your Mastodon instance")
    click.echo("* The toots you want to protect")
    click.echo()
    click.secho("We're going to open the file for you now.")
    click.pause()
    subprocess.run([EDITOR, CONFIG_FILE])


@cli.command()
@load_config
def config(config):
    """Display parsed config."""
    for section_name in config.sections():
        click.secho(section_name, bold=True)
        section = config[section_name]
        for key, value in section.items():
            click.secho("{} = {}".format(key, value))
        click.echo()


@cli.command()
@load_config
def login(config):
    """Fetch credentials for each app described in config file."""
    for section in config.sections():
        section = config[section]
        Mastodon.create_app(
            "cleantoots",
            api_base_url=section.get("api_base_url"),
            to_file=config_file(section.get("app_secret_file")),
        )
        mastodon = Mastodon(client_id=config_file(section.get("app_secret_file")))
        click.echo(
            "We will now open a browser for each account set in the config file."
        )
        click.echo(
            "You'll need to authenticate and then copy the code provided in the web "
            "page back into this terminal, upon prompt."
        )
        click.pause()
        webbrowser.open(mastodon.auth_request_url())
        code = click.prompt("Enter code for {}".format(section.get("api_base_url")))
        mastodon.log_in(code=code, to_file=config_file(section.get("user_secret_file")))


@cli.command()
@click.option(
    "--delete",
    help="Delete toots that match the rules without confirmation. This is a destructive operation. "
    "Without this flags, toots will only be listed.",
    is_flag=True,
)
@load_config
def clean(delete, config):
    """
    Delete Toots based on rules in config file.

    Without the `--delete` flag, toots will only be displayed.
    """
    for section in config.sections():
        section = config[section]
        user_secret_file = config_file(section.get("user_secret_file"))
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
