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

## Stack Manipulation Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - dup
          - swap
          - drop
          - size
          - pack
          - unpack


## Comparison Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - eq
          - neq
          - gt
          - ge
          - lt
          - le


## Looping Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - begin
          - while
          - break
          - repeat
          - recurse


## Branching Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - if
          - else
          - endif


## Loading/Storing/Deleting Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - load
          - store
          - delete


## Conversion Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - asbool
          - asint
          - asfloat


## Arithmetic Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - "/"
          - "*"
          - "-"
          - "+"
          - "%"


## Miscellaneous Ops
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - fstring
          - assert
          - set_next_params

<!-- ::: test-section
    handler: zvm
    options:
      imports:
        - zvm.zvm
      includes:
        "factorial": "file:./tests/json/test-recurse.json"
      filter:
        - "factorial"
        - "drop" -->
