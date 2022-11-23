#!/usr/bin/env python

"""
Validate and assemble spec files.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from re import split, sub
from urllib.error import HTTPError
from urllib.request import urlopen

import git
import yaml
from openapi_resolver import OpenapiResolver

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SKIP_FILES = ("definitions.yaml",)


def get_yaml(f):
    body = f.read_bytes()
    return yaml.safe_load(body)


def write_yaml(src, dst):
    p = Path(dst)
    p.write_text(OpenapiResolver.yaml_dump_pretty(src))


def bundler(repo):
    commit = repo.head.commit

    definitions = {}
    doc_dir = Path("docs")
    for f in doc_dir.rglob("*.yaml"):
        if f.name in SKIP_FILES:
            continue
        component = f.parent.name
        if component not in definitions:
            definitions[component] = {}
        definitions[component].update(get_yaml(f))
    definitions = {"components": definitions}
    write_yaml(definitions, "tests/tmp.bundle.yaml")

    r = OpenapiResolver(definitions, str(f))
    resolved = r.resolve()
    write_yaml(resolved, "tmp.bundle.resolverd.yaml")

    # Prepare metadata output.
    info = get_yaml(Path("info.yaml"))
    if "info" not in info:
        raise ValueError("Error: info.yaml does not contain 'info' section.")

    if not repo.head.is_detached:
        version = repo.active_branch.name
    else:
        version_tag = next(
            (tag for tag in repo.tags if tag.commit == repo.head.commit), None
        )
        if not version_tag:
            raise NotImplementedError(
                "The current state should be an active_branch or a tag."
            )
        version = version_tag.name

    info["info"].update(
        {
            "x-commit": str(commit),
            "x-date": commit.committed_date,
            "version": version,
        }
    )

    return (
        datetime.fromtimestamp(commit.committed_date).isoformat(),
        OpenapiResolver.yaml_dump_pretty(info),
        OpenapiResolver.yaml_dump_pretty(resolved)
        # .replace( "#/components/", "#/")
    )


def assemble(repo):
    committed_datetime, info, components = bundler(repo)
    d = Path(f"_build/{repo.active_branch.name}")
    d.mkdir(exist_ok=True)
    p = d / "definitions.yaml"
    with p.open("w") as fh:
        fh.write(f"#  {committed_datetime}\n")
        fh.write(info)
        fh.write(components)


def check_url(u):
    try:
        urlopen(u)  # nosec  this code runs locally
        return True
    except HTTPError as e:
        if e.code != 404:
            pass
    return False


def mkindex(repo):
    repo_url = next(repo.remote().urls)
    repo_url = sub(".git$", "", repo_url)

    owner, repo_name = split("[:./]", repo_url)[-2:]
    log.info("Creating index for repo: %r with tags: %r", repo_name, repo.tags)
    ret = []
    repo_tags = ["master"] + sorted([x.name for x in repo.tags], reverse=True)
    for t in repo_tags:
        u = f"https://{owner}.github.io/{repo_name}/{t}/definitions.yaml"
        if check_url(u):
            ret.append({"url": u, "comment": "OpenAPI 3.0"})
    p = Path("index.html")
    p.write_bytes(
        json.dumps(
            {
                "description": "Reusable OpenAPI definitions",
                "date": datetime.now().isoformat(),
                "entries": ret,
            },
            indent=4,
        ).encode()
    )


if __name__ == "__main__":
    repo = git.Repo(".")
    repo.git(work_tree="/tmp/foo").checkout("gh-pages")
    shutil.copytree("/tmp/foo", "_build")
    assemble(repo)
    mkindex(repo)
    for fpath in ("other",):
        shutil.copytree(fpath, Path("_build") / repo.active_branch.name / fpath)
