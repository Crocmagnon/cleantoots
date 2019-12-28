import click
import pendulum
from mastodon import Mastodon

from cleantoots.utils import _config_has_sections


@click.command()
@click.option(
    "--delete",
    help="Delete toots that match the rules without confirmation. This is a destructive operation. "
    "Without this flags, toots will only be listed.",
    is_flag=True,
)
@click.pass_obj
def clean(config, delete):
    """
    Delete Toots based on rules in config file.

    Without the `--delete` flag, toots will only be displayed.
    """
    if not _config_has_sections(config):
        return
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
