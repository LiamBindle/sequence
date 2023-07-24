# Writing a Toolkit

A toolkit is a Python package that provides methods and procedures. You should write your own toolkits to create
the methods you need for your scripting. To load your toolkit, include it in the `import` list in your JSON scripts.

<hr>

## Writing your own methods
A method is a Python function that uses the `@cvm.op` decorator. The decorator takes one argument, which is the name of the method.

To create a method, write a Python function with one positional argument for the `cvm.State` which is the object you
use to interact with the Collagen Virtual Machine (CVM) for things like popping items from the stack. Any parameters for your method should
be keyword-only arguments (i.e., after the `*` in the signature).

```python
import collagen.vm as cvm

@cvm.op("divide")
def my_divide(state: cvm.State, *, reciprocal: bool = False):
    y = state.pop()
    x = state.pop()
    if reciprocal:
        result = y / x
    else:
        result = x / y
    return result
```

Whatever your function returns is pushed to the stack, except for lists which expand onto the stack (the last element is the new TOS). If your function returns `None`, nothing is pushed to the stack.

<hr>

## Using `cvm.State`

The `cvm.State` is the object you use to interact with the Collagen Virtual Machine (CVM). It's a simple object and it's functions are listed below

```python
state: cvm.State

# pop/push data
x = state.pop()          # pops an item from the top-of-stack (TOS)
z, y, x = state.popn(3)  # pops N items from the stack (last was the TOS)
state.push(x)            # pushes an item to the TOS

# local/global variables
x = state.get("x", global_var=False)       # retrieves varible "x"
state.set("x", x, global_var=False)        # sets variable "x"
state.delete("x", global_var=False)        # deletes variable "x"
exists = state.has("x", global_var=False)  # checks if variable "x" exists
```

<hr>

## Writing data methods

To extend `get`, `put`, and `del` to work with your own data types you write Python functions to load, store, or delete data and use
the `@cvm.getter`, `@cvm.putter`, and `@cvm.deleter` wrappers.

The wrapper's take two arguments, `schemes` which is a list of URI schemes that the function works with (e.g., http, https), and
`media_type` which is the type identifier for your data type.

A getter function must have exactly two positional arguments, 
the first is the `cvm.State`, and the second is a URI. 
Your getter can include required/optional parameters as keyword-only arguments.

```python
import urllib.parse
import pathlib
import collagen

@cvm.getter(schemes=['file'], media_type='application/json')
def get_json_file(state: State, uri: str):
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = json.load(f)
    return data
```

A putter function must have exactly three positional arguments, 
the first is the `cvm.State`, the second is the data object, and the third is a URI.
Your putter can include required/optional parameters as keyword-only arguments.

```python
@cvm.putter(schemes=['file'], media_type='application/json')
def store_json_file(state: State, data, uri: str):
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        json.dump(data, f)
```

A deleter function must have exactly two positional arguments, 
the first is the `cvm.State`, and the second is a URI.
Your deleter can include required/optional parameters as keyword-only arguments.
```python
@cvm.deleter(schemes=['file'], media_type='application/json')
def delete_json_file(state: State, uri: str, *, missing_ok: bool = False):
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    pathlib.Path(path).unlink(missing_ok)
```

Note that you can set `media_type=None` to match any media types.

<hr>

## Documenting your methods

Method docstrings can specify the following sections: Parameters, Inputs, Outputs, and References. Docstrings should follow numpy-style.

```python
@cvm.op("divide")
def my_divide(state: cvm.State, *, reciprocal: bool = False):
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
[mkdocstrings](https://mkdocstrings.github.io/) plugin. Collagen automatically provides the `collagen` handler for mkdocstrings, which parses method docstrings. Package imports are specified by `options.imports` and procedures are included by `options.includes`. Data methods are included via `options.data` and methods/procedures are included via `options.ops`.

```
::: my_toolkit
    handler: collagen
    options:
        imports:
          - my_toolkit
        data:
          - http:application/foo
          - https:application/foo
        ops:
          - process_foo
```
