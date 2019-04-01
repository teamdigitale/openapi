#!/usr/bin/env python

"""
Validate and assemble spec files.
"""

import logging
from pathlib import Path

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

    info["info"].update(
        {
            "commit": str(commit),
            "date": commit.committed_date,
            "version": repo.active_branch.name,
        }
    )
    p = Path("docs/definitions.yaml")
    with p.open("w") as fh:
        fh.write(OpenapiResolver.yaml_dump_pretty(info))
        fh.write(
            OpenapiResolver.yaml_dump_pretty(resolved).replace(
                "#/components/", "#/"
            )
        )


if __name__ == "__main__":
    assemble()
