# OpenAPI v3 schemas

[![CircleCI](https://circleci.com/gh/teamdigitale/openapi.svg?style=svg)](https://circleci.com/gh/teamdigitale/openapi)

This repo contains useful and reusable schemas to implement REST APIs
distributed via github pages.

## Getting the specs

Latest master is available at:

- https://teamdigitale.github.io/openapi/master/definitions.yaml

Tagged specs are here:

- https://teamdigitale.github.io/openapi/0.0.4/definitions.yaml


Specs are assebled from the following directories:

```
docs/
├── headers             # HTTP Headers
├── parameters          # HTTP query parameters
├── responses           # Responses
└── schemas             # Various schema files
    ├── money.yaml
    ├── ...
    └── problem.yaml
```

## Building the specs

Every commit is tested via the `tox` python framework.

master and tags trigger `make ghpages` which:

- generates definitions.yaml
- push it to gh-pages branch, under $tag/definitions.yaml

