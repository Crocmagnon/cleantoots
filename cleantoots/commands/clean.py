import logging.handlers
from typing import Optional, List

import click
import html2text
import pendulum
from mastodon import Mastodon

from cleantoots.utils import _config_has_sections, CleanTootsConfig

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
def clean(config: CleanTootsConfig, delete: bool, headless: bool):
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
        protected = []
        while page:
            for toot in page:
                protection_reason = _toot_protection_reason(toot, section)
                if protection_reason:
                    protected.append({"toot": toot, "reason": protection_reason})
                else:
                    would_delete.append(toot)

            page = mastodon.fetch_next(page)

        _delete_or_log(delete, h, headless, mastodon, protected, would_delete)


def _delete_or_log(delete, html_handler, headless, mastodon, protected, would_delete):
    if not delete:
        _log_item_list(
            would_delete,
            headless,
            html_handler,
            no_item_message="No toot would be deleted given the rules.",
            count_message_format="Would delete {count} toots/boost:",
        )
        _log_item_list(
            protected,
            headless,
            html_handler,
            no_item_message="No toot would be protected given the rules.",
            count_message_format="Would protect {count} toots/boost:",
        )
    else:
        log("Deleting toots...", headless)
        with click.progressbar(would_delete) as bar:
            for toot in bar:
                mastodon.status_delete(toot)
                log("Deleted {}".format(_format_toot(toot)), headless, fg="green")


def _log_item_list(
    items: List[dict],
    headless: bool,
    html_handler: html2text.HTML2Text,
    no_item_message: str,
    count_message_format: str,
):
    if not items:
        log(no_item_message, headless, fg="blue")
    else:
        log(
            count_message_format.format(count=len(items)), headless, fg="blue",
        )
        for toot in items:
            _log_item(toot, headless, html_handler)


def _log_item(item, headless, html_handler):
    if "reason" in item and "toot" in item:
        toot = item["toot"]
        reason = item["reason"]
    else:
        toot = item
        reason = ""
    message = _format_toot(toot, reason)
    log(message, headless, bold=True)
    content = html_handler.handle(toot["content"]).replace("\n", " ").strip()
    if len(content) > CONTENT_PREVIEW:
        content = content[: CONTENT_PREVIEW - 3] + "..."
    else:
        content = content[:CONTENT_PREVIEW]
    log(content, headless)
    log("", headless)


def _format_toot(toot: dict, protection_reason: str = ""):
    if toot.get("reblog"):
        message = f"boost of toot {toot['reblog']['url']}"
    else:
        message = f"original toot {toot['url']}"
    if protection_reason:
        message = f"{message} protected because of {protection_reason}"
    return message


def log(message: str, headless: bool, level: int = logging.INFO, *args, **kwargs):
    if headless:
        if message and message.strip():
            logger.log(level, message)
    else:
        click.secho(message, *args, **kwargs)


def _toot_protection_reason(toot: dict, section) -> Optional[str]:
    """
    Return a protection reason or None if the toot should not be protected.

    :param toot: The toot to check.
    :param section: The section of the config file to check against.
    :return: The protection reason or None.
    """
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
    if boost_count >= section.getint("boost_limit"):
        return "boost count"
    if favorite_count >= section.getint("favorite_limit"):
        return "favorite count"
    if id_ in protected_toots or original_id in protected_toots:
        return "protected id"
    if created_at >= time_limit:
        return "creation time"

    return None
