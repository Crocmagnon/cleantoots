# Cleantoots
[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2FCrocmagnon%2Fcleantoots%2Fbadge&style=flat)](https://actions-badge.atrox.dev/Crocmagnon/cleantoots/goto)

Cleantoots helps you delete your old toots. Because not everything we say on social medias should stay there for eternity.

## Config
### Initial setup
Only once

```bash
python -m pip install cleantoots
cleantoots config setup  # See the following section for config file options
cleantoots config login
```

### View and edit
You can later view the parsed config file with
```bash
cleantoots config list
```

You can edit the config file using 
```bash
cleantoots config edit
```

This will open the config file using your preferred editor (`EDITOR` env variable).

## Config options

```ini
# Any key in this section will serve as a default for other sections
[DEFAULT]

# Toots that have at least this number of boosts won't be deleted.
boost_limit = 5

# Toots that have at least this number of favorites won't be deleted.
favorite_limit = 5

# Toots that are more recent than this number of days won't be deleted.
days_count = 30

# The timezone to use for dates comparisons.
timezone = Europe/Paris

# Each section represents an account.
[Fosstodon]
# Your Mastodon server URL.
api_base_url = https://fosstodon.org

# These files are used to store app information obtained when running `login`.
# The files must be different between accounts. Two different files are required per account.
app_secret_file = fosstodon_app.secret
user_secret_file = fosstodon_user.secret

# IDs of toots you want to protect (never delete).
# You can find the toot ID in the URL when viewing a toot.
protected_toots = 103362008817616000
    103361883565013391
    103363106195441418

# Another account
[Mastodon.social]
api_base_url = https://mastodon.social
app_secret_file = mastodonsocial_app.secret
user_secret_file = mastodonsocial_user.secret

# Overriding some defaults
boost_limit = 10
favorite_limit = 30
days_count = 7
```

## Run

See `cleantoots config` for the current config.

```bash
cleantoots clean  # Defaults to a dry run. Does NOT delete.
cleantoots clean --delete  # Delete without prompt.
```

## Add an account
```bash
cleantoots config edit  # Opens editor so you can add your config
cleantoots config list  # Check your newly added account
cleantoots config login --only-missing  # Store credentials for your newly created account
cleantoots clean --delete
```

## Remove an account
```bash
# This deletes stored credentials for accounts described in the main config file.
cleantoots config clear-credentials

# You can then edit the config and remove some accounts:
cleantoots config edit

# Then login again for remaining accounts.
cleantoots config login
```

## Tested environments
Cleantoots test suite runs on Python 3.6, 3.7 and 3.8
on latest versions of macOS, Windows and Ubuntu as GitHub Actions understands it.

See
[the docs](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/workflow-syntax-for-github-actions#jobsjob_idruns-on)
for more information on what "latest" means.

## Inspiration
The idea behind cleantoots is highly inspired by [magnusnissel/cleantweets](https://github.com/magnusnissel/cleantweets).
