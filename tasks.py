import os
from pathlib import Path

from invoke import task

BASE_DIR = Path(__file__).parent.resolve(strict=True)


@task
def test(ctx):
    with ctx.cd(BASE_DIR):
        ctx.run("pytest", pty=True, echo=True)


@task
def test_cov(ctx):
    with ctx.cd(BASE_DIR):
        ctx.run(
            "pytest --cov=. --cov-report term-missing:skip-covered",
            pty=True,
            echo=True,
        )


@task
def full_test(ctx):
    with ctx.cd(BASE_DIR):
        ctx.run("tox", pty=True, echo=True)


@task
def publish(ctx):
    username = os.getenv("PYPI_USERNAME")
    password = os.getenv("PYPI_TOKEN")
    with ctx.cd(BASE_DIR):
        args = ""
        if username and password:
            args = f"--username {username} --password {password}"
        ctx.run(f"poetry publish --build {args}", pty=True, echo=False)


@task
def tag(ctx, tag_name):
    with ctx.cd(BASE_DIR):
        ctx.run(f'git tag {tag_name} -am "{tag_name}"', pty=True, echo=True)
        ctx.run(f"git push origin {tag_name}", pty=True, echo=True)
