# A file to store app information obtained when running `create-app`
APP_SECRET_FILE = "cleantootsapp.secret"
# A file to store the user secrets obtained when running `get-credentials`
USER_SECRET_FILE = "cleantootsuser.secret"
# Your Mastodon server URL
API_BASE_URL = "https://fosstodon.org"

# IDs of toots you want to protect (never delete)
PROTECTED_TOOTS = [
    103361883565013391,
    103362008817616000,
    103363106195441418,
]
# Toots that have at least this number of boosts won't be deleted.
BOOST_LIMIT = 5
# Toots that have at least this number of favorites won't be deleted.
FAVORITE_LIMIT = 5
# Toots that are more recent than this number of days won't be deleted.
DAYS_COUNT = 30
# The timezone to use for dates comparisons.
TIMEZONE = "Europe/Paris"
