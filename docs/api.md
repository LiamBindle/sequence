# Extending ZVM

## Writing your own methods
A method is a python function that is wrapped in the `@zvm.op` decorator. The decorator's argument defines the name of the method. The python function must have exactly one positional argument for
the `zvm.State`, which facilitates pushing/popping items from the stack.

```python
import zvm

@zvm.op("divide")
def my_divide(state: zvm.State):
    # this function corresponds to {"op": "divide"}
    y = state.pop()
    x = state.pop()
    result = x / y
    return result
```

Any item returned by the function is pushed to the stack, except for lists which expand onto the stack (the last element is the new TOS).

Method parameters are defined by keyword-only arguments.

```python
@zvm.op("divide")
def my_divide(state: zvm.State, *, reciprocal: bool = False):
    y = state.pop()
    x = state.pop()
    if reciprocal:
        result = y / x
    else:
        result = x / y
    return result
```

To access your methods, import your Python package in the `import` section of a procedure.

```json
{
    "import": [
        "my_package"
    ],
    "run": [
        5,
        3,
        {"op": "divide", "reciprocal": true}
    ]
}
```

## Documenting your methods

Method docstrings can specify the following sections: Parameters, Inputs, Outputs, and References. Docstrings should follow numpy-style.

```python
@zvm.op("divide")
def my_divide(state: zvm.State, *, reciprocal: bool = False):
    """
    Divides two numbers [1].

    Parameters
    ----------
    reciprocal: bool (default: false)
        If true, returns the reciprocal
    
    Inputs
    ------
    y: number
        The denominator
    x: number
        The numerator
    
    Outputs
    -------
    result: number
        The result of the division
    """
    # example usage: {"op": "divide", "reciprocal": true}
    y = state.pop()
    x = state.pop()
    if reciprocal:
        result = y / x
    else:
        result = x / y
    return result
```

You can generate documentation for your package using [MkDocs](https://www.mkdocs.org/) with the 
[mkdocstrings](https://mkdocstrings.github.io/) plugin. ZVM automatically provides the `zvm` handler for mkdocstrings, which parses method docstrings. Package imports are specified by `options.imports` and procedures are included by `options.includes`. Data methods are included via `options.data` and methods/procedures are included via `options.ops`.

```
::: my_package
    handler: zvm
    options:
        imports:
          - my_package
        data:
          - http:application/foo
          - https:application/foo
        ops:
          - process_foo
```
