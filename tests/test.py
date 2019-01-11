import logging
from pathlib import Path
from shlex import split
from subprocess import TimeoutExpired, run

import git
import yaml
from openapi_resolver import OpenapiResolver
from openapi_spec_validator import validate_spec

logging.basicConfig(level=logging.DEBUG)

# some global variables.
repo = git.Repo(".")
commit = repo.head.commit


def test_ensure_yaml_files():
    doc_dir = Path("docs")
    for f in doc_dir.rglob("*.yml"):
        assert False, "Files extension should be .yaml"


def test_validate_simple():
    oas = yaml_load_file("tests/simple.yaml", cb=replace_branch_name)
    validate_spec(oas)


def test_validate_info():
    oas = yaml_load_file("info.yaml")
    assert "info" in oas
    assert "description" in oas["info"]


def test_validate_resolved():
    simple_yaml = "tests/simple.yaml"
    oas = yaml_load_file(simple_yaml, cb=replace_branch_name)
    resolver = OpenapiResolver(oas)
    oas_resolved = resolver.dump_yaml()
    validate_spec(oas_resolved)

    Path("tests/out.simple.yaml").write_text(resolver.dump())


def test_check_build():
    run([str(Path("build.py").resolve())])
    definitions = yaml_load_file("docs/definitions.yaml")
    assert "info" in definitions
    for section in ("headers", "schemas", "parameters", "headers", "responses"):
        assert section in definitions, f"Missing {section} in definitions.yaml"


def test_run_connexion():
    try:
        execve("connexion run --stub tests/out.simple.yaml", timeout=5)
    except TimeoutExpired:
        pass


def execve(cmd, **kwargs):
    run(split(cmd), **kwargs)


def yaml_load_file(fpath, cb=None):
    txt = Path(fpath).read_text()
    if cb and callable(cb):
        txt = cb(txt)
    return yaml.load(txt)


def replace_branch_name(txt):
    return txt.replace("1-reorganize-repo", repo.active_branch.name)
