import os
import sys

import click
from mastodon import Mastodon

from cleantoots.utils import (
    _config_has_sections,
    _open_url,
    _get_default_config,
    _is_tty,
    CleanTootsConfig,
)


@click.group("config")
def config_command():
    """Manage cleantoot's config."""
    pass


@config_command.command()
@click.pass_obj
def setup(config: CleanTootsConfig):
    """Initial setup for configuration directories and files."""
    if os.path.isfile(config.main_file):
        click.secho(
            "{} found. Not touching anything.".format(config.main_file), fg="yellow"
        )
        command = click.style("cleantoots config edit", bold=True)
        click.echo("You may want to edit the file. Use: {}.".format(command))
        return

    default_config = _get_default_config()
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
    if _is_tty():
        click.echo()
        click.secho("We're going to open the file for you now.")
        click.pause()
        click.edit(filename=config.main_file)


@config_command.command(name="list")
@click.pass_obj
def list_(config: CleanTootsConfig):
    """Display parsed config."""
    if not _config_has_sections(config):
        return
    for section_name in config.sections():
        click.secho(section_name, bold=True)
        section = config[section_name]
        for key, value in section.items():
            click.secho("{} = {}".format(key, value))
        click.echo()


@config_command.command()
@click.pass_obj
def edit(config: CleanTootsConfig):
    """Edit config file."""
    if not _config_has_sections(config):
        click.pause()
    if sys.stdout.isatty() and sys.stdin.isatty():
        click.edit(filename=config.main_file)
    else:
        click.secho("Not running in a terminal, can't open file.", fg="red")


@config_command.command()
@click.pass_obj
def path(config: CleanTootsConfig):
    """Print config path and exit."""
    click.echo(config.dir)


@config_command.command()
@click.option(
    "-m",
    "--only-missing",
    help="Prompt for login only on accounts that miss a credentials file.",
    is_flag=True,
)
@click.pass_obj
def login(config: CleanTootsConfig, only_missing: bool):
    """Fetch credentials for each app described in config file."""
    if not _config_has_sections(config):
        return
    prompt = True
    for section in config.sections():
        section = config[section]
        app_file_exists = config.isfile(section.get("app_secret_file"))
        user_file_exists = config.isfile(section.get("user_secret_file"))

        if not (only_missing and app_file_exists):
            Mastodon.create_app(
                "cleantoots",
                api_base_url=section.get("api_base_url"),
                to_file=config.file(section.get("app_secret_file")),
            )

        mastodon = Mastodon(client_id=config.file(section.get("app_secret_file")))
        if not (only_missing and user_file_exists and app_file_exists):
            _open_url(mastodon.auth_request_url(), echo=prompt)
            prompt = False
            code = click.prompt("Enter code for {}".format(section.get("api_base_url")))
            mastodon.log_in(
                code=code, to_file=config.file(section.get("user_secret_file"))
            )


@config_command.command()
@click.confirmation_option(
    prompt="Are you sure you want to delete all credential files? "
    "You will need to run `cleantoots config login` to re-authenticate."
)
@click.pass_obj
def clear_credentials(config: CleanTootsConfig):
    """Delete all credential files described in config file."""
    if not _config_has_sections(config):
        return
    for section_name in config.sections():
        section = config[section_name]
        try:
            os.remove(config.file(section.get("app_secret_file")))
        except FileNotFoundError:
            pass
        try:
            os.remove(config.file(section.get("user_secret_file")))
        except FileNotFoundError:
            pass
        click.secho("Removed files for {}".format(section_name), fg="green")
