import logging.handlers

import click
import html2text
import pendulum
from mastodon import Mastodon

from cleantoots.utils import _config_has_sections

logger = logging.getLogger(__name__)

CONTENT_PREVIEW = 78


@click.command()
@click.option(
    "--delete",
    help="Delete toots that match the rules without confirmation. This is a destructive operation. "
    "Without this flags, toots will only be listed.",
    is_flag=True,
)
@click.option(
    "--headless", help="Use to make output more logging friendly.", is_flag=True
)
@click.pass_obj
def clean(config, delete, headless):
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
                log("No toot would be deleted given the rules.", headless, fg="blue")
                return
            log(
                "Would delete {count} toots/boost:".format(count=len(would_delete)),
                headless,
                fg="blue",
            )
            for toot in would_delete:
                message = format_toot(toot)
                log(message, headless, bold=True)
                content = h.handle(toot["content"]).replace("\n", " ").strip()
                if len(content) > CONTENT_PREVIEW:
                    content = content[: CONTENT_PREVIEW - 3] + "..."
                else:
                    content = content[:CONTENT_PREVIEW]
                log(content, headless)
                log("", headless)
        else:
            log("Deleting toots...", headless)
            with click.progressbar(would_delete) as bar:
                for toot in bar:
                    mastodon.status_delete(toot)
                    log("Deleted {}".format(format_toot(toot)), headless, fg="green")


def format_toot(toot):
    if toot.get("reblog"):
        message = f"boost of toot {toot['reblog']['url']}"
    else:
        message = f"original toot {toot['url']}"
    return message


def log(message, headless, level=logging.INFO, *args, **kwargs):
    if headless:
        if message and message.strip():
            logger.log(level, message)
    else:
        click.secho(message, *args, **kwargs)
