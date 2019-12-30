import click
import html2text
import pendulum
from mastodon import Mastodon

from cleantoots.utils import _config_has_sections

CONTENT_PREVIEW = 78


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
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_emphasis = True
    h.ignore_images = True
    h.ignore_tables = True

    for section in config.sections():
        section = config[section]
        user_secret_file = config.file(section.get("user_secret_file"))
        mastodon = Mastodon(access_token=user_secret_file)
        user = mastodon.me()
        page = mastodon.account_statuses(user["id"])
        would_delete = []
        while page:
            for toot in page:
                boost_count = toot["reblogs_count"]
                favorite_count = toot["favourites_count"]
                id_ = toot["id"]
                original_id = None
                if toot.get("reblog"):
                    original_id = toot["reblog"].get("id")
                created_at = toot["created_at"]
                protected_toots = map(int, section.get("protected_toots", "").split())
                time_limit = pendulum.now(tz=section.get("timezone")).subtract(
                    days=section.getint("days_count")
                )
                if (
                    boost_count >= section.getint("boost_limit")
                    or favorite_count >= section.getint("favorite_limit")
                    or id_ in protected_toots
                    or original_id in protected_toots
                    or created_at >= time_limit
                ):
                    continue
                would_delete.append(toot)

            page = mastodon.fetch_next(page)

        if not delete:
            if not would_delete:
                click.secho("No toot would be deleted given the rules.", fg="blue")
                return
            click.secho(
                "Would delete {count} toots/boost:".format(count=len(would_delete)),
                fg="blue",
            )
            for toot in would_delete:
                message = format_toot(toot, prefix="=== ", separator=" ", suffix=" ===")
                click.echo(message)
                content = h.handle(toot["content"]).replace("\n", " ").strip()
                if len(content) > CONTENT_PREVIEW:
                    content = content[: CONTENT_PREVIEW - 3] + "..."
                else:
                    content = content[:CONTENT_PREVIEW]
                click.echo(content)
                click.echo()
        else:
            click.echo("Deleting toots...")
            with click.progressbar(would_delete) as bar:
                for toot in bar:
                    mastodon.status_delete(toot)
                    click.secho("Deleted {}".format(format_toot(toot)), fg="green")


def format_toot(toot, prefix="", separator="\t", suffix=""):
    if toot.get("reblog"):
        message = f"{prefix}boost of{separator}{toot['reblog']['url']}{suffix}"
    else:
        message = f"{prefix}original toot{separator}{toot['url']}{suffix}"
    return message
