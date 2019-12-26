# Cleantoots

## Initial config

Only once

```bash
pipenv install
pipenv run python main.py create-app
pipenv run python main.py get-credentials
```

## Run

See `config.py` for options.

```bash
pipenv run python main.py clean-toots  # Defaults to a dry run. Does NOT delete.
pipenv run python main.py clean-toots --delete  # Delete without prompt.
```
