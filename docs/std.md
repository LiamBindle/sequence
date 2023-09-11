# Standard Toolkit

The standard toolkit is the collection of methods that are built into Sequence. The standard toolkit provides
the methods for scripting logic such as branching (if-else-endif), looping (begin-while-repeat), and working
with the stack, and data methods for loading/storing/deleting variables, and JSON data.

## Stack Manipulation
These methods are used to perform actions on the stack. They include operations such as duplicating items, reordering items, droping items, etc.

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        ops:
          - dup
          - swap
          - drop
          - size
          - pack
          - unpack


## Comparison
These methods are used to compare items on the stack. These are useful as conditional leading before an if or while
statement.

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
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

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        ops:
          - begin
          - while
          - break
          - repeat
          - recurse


## Branching
These methods facilitate conditional branching.

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        ops:
          - if
          - else
          - endif


## Conversion
These methods are used to coerce the item at the top of the stack to a specific data type.

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        ops:
          - asbool
          - asint
          - asfloat


## Arithmetic
These methods are used to perform arithmetic.

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        ops:
          - "/"
          - "*"
          - "-"
          - "+"
          - "%"


## Miscellaneous
These methods don't fit into the other categories, but they are useful.

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        ops:
          - fstring
          - assert

<hr>

# Data Methods

The standard toolkit provides data methods for loading/storing/deleting local variables, and JSON data.


## Variables
These methods are used to store, load, and delete variables. Local variables are procedure-scoped.
::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        data:
          - variables


## JSON
These methods are used to store, load, and delete JSON files.
::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        data:
          - http:application/json
          - https:application/json
          - file:application/json


### JSON5
JSON5 is an extension of JSON that adds functionality such as comments, multiline strings, trailing commas, and unquoted strings. You can read more about JSON5 [here](https://json5.org/). These methods require that Sequence was installed with
JSON5 support (i.e., `pip install 'sequence[json5]'`).

::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        data:
          - http:application/json5
          - https:application/json5
          - file:application/json5

### HJSON
HJSON is an extension of JSON that is less prone to syntax errors and adds functionality such as comments, multiline strings, trailing commas, and unquoted strings. You can read more about HJSON [here](https://hjson.github.io/).
These methods require that Sequence was installed with HJSON support (i.e., `pip install 'sequence[hjson]'`).
::: sequence
    handler: sequence
    options:
        toolkits:
          - sequence.standard
        data:
          - http:application/hjson
          - https:application/hjson
          - file:application/hjson
