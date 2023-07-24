# Collagen

*Note: This documentation is a work in progress.*

Collagen is a virtual stack machine that lets you write procedures in configuration files, like JSON or YAML, that generate outputs like data,
images, or documents. 
A procedure defines a sequence of operations that run in the Python environment, and the operations in a procedure pass data to each other by pushing, popping, and swapping data on the stack.
The standard toolkit (built-in) defines a turning complete set of operations that provide the backbone for scripting logic in your procedures.
You can add methods with new functionality by adding toolkits, which add methods by implementing Python functions with the new functionality and using the `@cvm.method` decorator.

## Installation
You can install collagen via `pip`. Note that the basic installation only supports JSON procedures.

```console
pip install collagen
```

Procedures written in JSON5, HSON, or YAML can have comments and multi-line strings. You can install support for additional configuration file formats via extra requirements.

```console
pip install collagen[json5,hson]
```

If you're developing a collagen toolkit, include the `dev` and `docs` extra
requirements.

```console
pip install "collagen[dev,docs]"
```
