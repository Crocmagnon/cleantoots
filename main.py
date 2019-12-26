import webbrowser

import click
import pendulum
from mastodon import Mastodon

from config import (
    USER_SECRET_FILE,
    APP_SECRET_FILE,
    API_BASE_URL,
    PROTECTED_TOOTS,
    BOOST_LIMIT,
    FAVORITE_LIMIT,
    DAYS_COUNT,
    TIMEZONE,
)


@click.group()
def cli():
    pass


@cli.command()
def create_app():
    Mastodon.create_app(
        "cleantoots", api_base_url=API_BASE_URL, to_file=APP_SECRET_FILE,
    )


@cli.command()
def get_credentials():
    mastodon = Mastodon(client_id=APP_SECRET_FILE)
    webbrowser.open(mastodon.auth_request_url())
    code = click.prompt("Enter code")
    mastodon.log_in(
        code=code, to_file=USER_SECRET_FILE,
    )


@cli.command()
@click.option("--delete", is_flag=True)
def clean_toots(delete):
    mastodon = Mastodon(access_token=USER_SECRET_FILE)
    user = mastodon.me()
    page = mastodon.account_statuses(user["id"])
    would_delete = []
    while page:
        for toot in page:
            if (
                toot["reblogs_count"] >= BOOST_LIMIT
                or toot["favourites_count"] >= FAVORITE_LIMIT
                or toot["id"] in PROTECTED_TOOTS
                or toot["created_at"]
                >= pendulum.now(tz=TIMEZONE).subtract(days=DAYS_COUNT)
            ):
                continue
            would_delete.append(toot)

        page = mastodon.fetch_next(page)

    if not delete:
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


if __name__ == "__main__":
    cli()
