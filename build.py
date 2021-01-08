#!/usr/bin/env python

"""
Validate and assemble spec files.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from re import split
from urllib.error import HTTPError
from urllib.request import urlopen

import git
import yaml
from openapi_resolver import OpenapiResolver

logging.basicConfig(level=logging.DEBUG)

SKIP_FILES = ("definitions.yaml",)


def get_yaml(f):
    body = f.read_bytes()
    return yaml.safe_load(body)


def write_yaml(src, dst):
    p = Path(dst)
    p.write_text(OpenapiResolver.yaml_dump_pretty(src))



def assemble():
    repo = git.Repo(".")
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
            "commit": str(commit),
            "date": commit.committed_date,
            "version": version,
        }
    )

    committed_datetime = datetime.fromtimestamp(
        commit.committed_date
    ).isoformat()

    p = Path("docs/definitions.yaml")
    with p.open("w") as fh:
        fh.write(f"#  {committed_datetime}\n")
        fh.write(OpenapiResolver.yaml_dump_pretty(info))
        fh.write(
            OpenapiResolver.yaml_dump_pretty(resolved).replace(
                "#/components/", "#/"
            )
        )


def check_url(u):
    try:
        urlopen(u)
        return True
    except HTTPError as e:
        if e.code != 404:
            pass
    return False


def mkindex():
    repo = git.Repo(".")
    owner, repo_name = split("[:./]", next(repo.remote().urls))[-2:]

    ret = []
    for x in repo.tags:
        u = f"https://{owner}.github.io/{repo_name}/{x.name}/definitions.yaml"
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
    assemble()
    mkindex()
