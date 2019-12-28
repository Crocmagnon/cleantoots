import configparser
import os
import sys

import click
from mastodon import Mastodon


@click.group()
@click.pass_obj
def config(config):
    """Manage cleantoot's config."""
    pass


@config.command()
@click.pass_obj
def setup(config):
    """Initial setup for configuration directories and files."""
    os.makedirs(config.dir, exist_ok=True)
    if os.path.isfile(config.main_file):
        click.secho(
            "{} found. Not touching anything.".format(config.main_file), fg="yellow"
        )
        command = click.style("cleantoots config edit", bold=True)
        click.echo("You may want to edit the file. Use: {}.".format(command))
        return

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


@config.command(name="list")
@click.pass_obj
def list_(config):
    """Display parsed config."""
    if not config.sections():
        click.secho("The config file doesn't seem to have any section.", fg="yellow")
        command = click.style("cleantoots config setup", bold=True)
        click.secho("You should set it up first. Use: {}".format(command))
        return
    for section_name in config.sections():
        click.secho(section_name, bold=True)
        section = config[section_name]
        for key, value in section.items():
            click.secho("{} = {}".format(key, value))
        click.echo()


@config.command()
@click.pass_obj
def edit(config):
    """Edit config file."""
    if not config.sections():
        click.secho("The config file doesn't seem to have any section.", fg="yellow")
        command = click.style("cleantoots config setup", bold=True)
        click.secho("You should set it up first. Use: {}".format(command))
        return
    if sys.stdout.isatty() and sys.stdin.isatty():
        click.edit(filename=config.main_file)
    else:
        click.secho("Not running in a terminal, can't open file.", fg="red")


@config.command()
@click.pass_obj
def login(config):
    """Fetch credentials for each app described in config file."""
    if not config.sections():
        click.secho("The config file doesn't seem to have any section.", fg="yellow")
        command = click.style("cleantoots config setup", bold=True)
        click.secho("You should set it up first. Use: {}".format(command))
        return
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
