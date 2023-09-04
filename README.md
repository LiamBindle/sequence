# Overview

*Note: This documentation is a work in progress.*

Sequence is a library that lets you script Python by writing procedures in configuration file formats like JSON or YAML.
This is useful when you want to define the logic for generating some sort of output, like data or an image, in a configuration file.
In sequence, this type of configuration file is called a *procedure* and it defines a sequence of operations that do something.

Under the hood, sequence has a virtual stack machine, *SVM*, that runs procedures.
A procedure is a sequence of *operations*, where an operation is either another procedure (a subprocedure) or a *method*.
A method is a Python function that uses the `@svm.method` decorator and methods are what provide basic functionality.
Methods and procedures pass data to each other by using SVM's stack, via pushing, popping, and swapping data on the stack.

A *toolkit* is a Python package that provides a suite of methods.
The *standard toolkit* (built-in) is a suite of turing-complete methods that provide the backbone for scripting logic in procedures (e.g., if blocks, while loops, string formatting, data resources, etc.).
Additional functionality can be added by installing additional toolkits.

## About Stack Machines

If it isn't clear how operations pass data using the stack, a good way to get familiar with the concept is by playing around with an RPN calculator like [this](http://www.alcula.com/calculators/rpn/). Try calculating the hypotenuse of a triangle with side length of 3 and 4 using the Pythagorean Theorem (the answer is *3, Enter, X, Enter, 4, Enter, X, +, SQRT*). Every button-press is equivalent to an operation in sequence.

The design of sequence took inspiration from these old RPN-style calculators as well as the
[FORTH](https://en.wikipedia.org/wiki/Forth_(programming_language)) programming language.


## Installing sequence
Sequence can be install using `pip`. The basic install supports procedures written in
JSON.

```console
$ pip install sequence
```

It's oftentimes useful to add comments and use multi-line strings in procedures.
This can be done by writing your procedures in a configuration file format that supports comments and multi-line strings, such as JSON5, HSON, or YAML.
Additional configuration languages can be installed via the `json5`, `hson`, and/or `yaml` extras.

```console
$ pip install "sequence[json5,hson]"
```

If you are developing a Sequence Toolkit (STK), the `dev` and `docs` extras install the requirements for running tests and building documentation.

```console
$ pip install "sequence[dev,docs]"
```
