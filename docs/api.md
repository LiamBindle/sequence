# Writing a Toolkit

The idea behind ZVM is you write your own toolkits that provide the methods and procedures that you need for your application.

A toolkit is a Python package that provides methods and procedures. You should write your own toolkits to create
the methods you need for your scripting. To load your toolkit, include it in the `import` list in your JSON scripts.

<hr>

## Writing your own methods
A method is a Python function that uses the `@zvm.op` decorator. The decorator takes one argument, which is the name of the method.

To create a method, write a Python function with one positional argument for the `zvm.State` which is the object you
use to interact with ZVM for things like popping items from the stack. Any parameters for your method should
be keyword-only arguments (i.e., after the `*` in the signature).

```python
import zvm

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

Whatever your function returns is pushed to the stack, except for lists which expand onto the stack (the last element is the new TOS). If your function returns `None`, nothing is pushed to the stack.

<hr>

## Using `zvm.State`

The `zvm.State` is the object you use to interact with ZVM. It's a simple object and it's functions are listed below

```python
state: zvm.State

# pop/push data
x = state.pop()          # pops an item from the top-of-stack (TOS)
z, y, x = state.popn(3)  # pops N items from the stack (last was the TOS)
state.push(x)            # pushes an item to the TOS

# local variables
state.set("x", x)        # sets local variable "x"
exists = state.has("x")  # checks if local variable "x" exists
x = state.get("x")       # retrieves local varible "x"
state.delete("x")        # deletes local variable "x"

# global variables
state.set_global("x", x)        # sets global variable "x"
exists = state.has_global("x")  # checks if global variable "x" exists
x = state.get_global("x")       # retrieves global varible "x"
state.delete_global("x")        # deletes global variable "x"
```

<hr>

## Writing data methods

To extend `get`, `put`, and `del` to work with your own data types you write Python functions to load, store, or delete data and use
the `@zvm.getter`, `@zvm.putter`, and `@zvm.deleter` wrappers.

The wrapper's take two arguments, `schemes` which is a list of URI schemes that the function works with (e.g., http, https), and
`media_type` which is the type identifier for your data type.

A getter function must have exactly two positional arguments, 
the first is the `zvm.State`, and the second is a URI. 
Your getter can include required/optional parameters as keyword-only arguments.

```python
import urllib.parse
import pathlib
import zvm

@zvm.getter(schemes=['file'], media_type='application/json')
def get_json_file(state: State, uri: str):
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = json.load(f)
    return data
```

A putter function must have exactly three positional arguments, 
the first is the `zvm.State`, the second is the data object, and the third is a URI.
Your putter can include required/optional parameters as keyword-only arguments.

```python
@zvm.putter(schemes=['file'], media_type='application/json')
def store_json_file(state: State, data, uri: str):
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        json.dump(data, f)
```

A deleter function must have exactly two positional arguments, 
the first is the `zvm.State`, and the second is a URI.
Your deleter can include required/optional parameters as keyword-only arguments.
```python
@zvm.deleter(schemes=['file'], media_type='application/json')
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
::: my_toolkit
    handler: zvm
    options:
        imports:
          - my_toolkit
        data:
          - http:application/foo
          - https:application/foo
        ops:
          - process_foo
```
