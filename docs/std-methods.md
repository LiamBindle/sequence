# Logic Methods

## Stack Manipulation
These methods perform operations to the stack such as duplicating items, reordering items, droping items, etc.

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
These methods are used to perform comparison of items on the stack.

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
These methods facilitate looping and recursion. Loops start with `begin` and end with `repeat`. Loops are terminated by `break`. 
The `while` method is provided for convenience, and effectively guards a `break` in an if-block.

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
These methods facilitate branching.

::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - if
          - else
          - endif


## Conversion
These methods are used to convert data types.

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
These methods are used to perform arithmetic.

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
These don't fit into the other categories.

::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        ops:
          - fstring
          - assert
          - set_next_params
