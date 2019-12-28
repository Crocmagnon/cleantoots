import configparser
import sys

import click


def _is_tty():
    return sys.stdout.isatty() and sys.stdin.isatty()


def _config_has_sections(config):
    if not config.sections():
        click.secho("The config file doesn't seem to have any section.", fg="yellow")
        command = click.style("cleantoots config setup", bold=True)
        click.secho("You should set it up first. Use: {}".format(command))
        return False
    return True


def _open_url(url, echo):
    if _is_tty():
        if echo:
            click.echo(
                "We will now open a browser for each account set in the config file."
            )
            click.echo(
                "You'll need to authenticate and then copy the code provided in the web "
                "page back into this terminal, upon prompt."
            )
            click.pause()
        click.launch(url)
    else:
        click.echo("Go to {}, authenticate and enter the code below.".format(url))


def _get_default_config():
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
    return default_config
