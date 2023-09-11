# Overview

Sequence is a library that lets you build analysis tools that can be controlled by configuration files.
This is useful when you want to define the logic for generating some sort of output, like data or an image, in a configuration file.
This type of configuration file is called a *sequence* and it defines a sequence of operations that do something.


Under the hood, sequences are run by a virtual stack machine.
A sequence is a list of *operations*, where an operation is either another sequence or a *method*.
A method is a Python function that uses the `@sequence.method` decorator and methods provide basic functionality building blocks.
Methods and sequences pass data to each other on the virtual machine's stack, via pushing, popping, and swapping data.

A *sequence toolkit (STK)* is a Python package that provides a suite of methods.
The *standard toolkit* (built-in) is a suite of turing-complete methods that provide the backbone for scripting logic in sequences (e.g., if blocks, while loops, string formatting, data resources, etc.).
Additional functionality can be added by installing additional toolkits.

## About Stack Machines

If it isn't clear how operations pass data using the stack, a good way to get familiar with the concept is by playing around with an RPN calculator like [this](http://www.alcula.com/calculators/rpn/). Try calculating the hypotenuse of a triangle with side length of 3 and 4 using the Pythagorean Theorem (the answer is *3, Enter, X, Enter, 4, Enter, X, +, SQRT*). Every button-press is equivalent to an operation in sequence.

The design of sequence took inspiration from these old RPN-style calculators as well as the
[FORTH](https://en.wikipedia.org/wiki/Forth_(programming_language)) programming language.


## Installing sequence
Sequence can be install using `pip`. The basic install supports JSON.

```console
$ pip install sequence-stk
```

It's often useful to be able to write comments and use multi-line strings in sequences.
JSON5 and HSON are extensions of JSON that support these features. 
Additional configuration languages can be installed via the `json5`, and/ord `hson` extras.

```console
$ pip install "sequence[json5,hson]"
```

If you are developing an STK, the `dev` and `docs` extras install the requirements for running tests and building documentation.

```console
$ pip install "sequence[dev,docs]"
```
