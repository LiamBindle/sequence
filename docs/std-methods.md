# Methods

## Stack Manipulation
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


## Comparison
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


## Looping
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


## Branching
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - if
          - else
          - endif


## External data
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - get
          - put
          - del


## Conversion
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - asbool
          - asint
          - asfloat


## Arithmetic
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


## Miscellaneous
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - fstring
          - assert
          - set_next_params
