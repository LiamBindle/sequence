# Welcome to MkDocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Commands

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

<!-- ::: zvm.zvm
    handler: python
    selection:
      docstring_style: numpy -->

::: test-section
    handler: zvm
    options:
      imports:
        - zvm.zvm
      includes:
        "factorial": "file:./tests/json/test-recurse.json"
      filter:
        - "factorial"
        - "drop"
