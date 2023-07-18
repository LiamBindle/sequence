# Data Methods


## Variables
These methods are used to store, load, and delete local and global variables. Local variables are procedure-scoped.
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        data:
          - locals
          - globals


## JSON
These methods are used to store, load, and delete JSON files.
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        data:
          - http:application/json
          - https:application/json
          - file:application/json


## JSON5
JSON5 is an extension of JSON that adds functionality such as comments, multiline strings, trailing commas, and unquoted strings. You can read more about JSON5 [here](https://json5.org/).

To use these methods, you need to install ZVM with JSON5 support (i.e., `pip install 'zvm[json5]'`).

::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        data:
          - http:application/json5
          - https:application/json5
          - file:application/json5

## HJSON
HJSON is an extension of JSON that is less prone to syntax errors and adds functionality such as comments, multiline strings, trailing commas, and unquoted strings. You can read more about HJSON [here](https://hjson.github.io/).

To use these methods, you need to install ZVM with HJSON support (i.e., `pip install 'zvm[hjson]'`).
::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        data:
          - http:application/hjson
          - https:application/hjson
          - file:application/hjson
