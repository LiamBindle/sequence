# Data

::: zvm.zvm
    handler: zvm
    options:
        imports:
          - zvm.zvm
        data:
          - http:application/json
          - https:application/json
          - file:application/json
          - locals
          - globals
