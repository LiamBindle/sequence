import sequence.vm as svm


# comparison
@svm.method("eq")
def equal(state: svm.State):
    """
    Checks if x == y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    xy_eq: bool
        The result of x == y.
    """
    x, y = state.popn(2)
    return x == y


@svm.method("neq")
def not_equal(state: svm.State):
    """
    Checks if x is not equal to y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    xy_neq: bool
        The result of x != y.
    """
    x, y = state.popn(2)
    return x != y


@svm.method("gt")
def greater_than(state: svm.State):
    """
    Checks if x is greater than y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_gt_y: bool
        The result of x > y.
    """
    x, y = state.popn(2)
    return x > y


@svm.method("ge")
def greater_than_or_equal_to(state: svm.State):
    """
    Checks if x is greater than or equal to y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_ge_y: bool
        The result of x >= y.
    """
    x, y = state.popn(2)
    return x >= y


@svm.method("lt")
def less_than(state: svm.State):
    """
    Checks if x is less than y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_lt_y: bool
        The result of x < y.
    """
    x, y = state.popn(2)
    return x < y


@svm.method("le")
def less_than_or_equal_to(state: svm.State):
    """
    Checks if x is less than or equal to y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_le_y: bool
        The result of x <= y.
    """
    x, y = state.popn(2)
    return x <= y


@svm.method("/")
def divide(state: svm.State):
    """
    Divides the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '/' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The denominator.
    x: number, Any
        The numerator.

    Outputs
    -------
    result: number, Any
        The result of the division.
    """
    x, y = state.popn(2)
    return x / y


@svm.method("*")
def multiply(state: svm.State):
    """
    Multiplies the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '*' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The second term.
    x: number, Any
        The first term.

    Outputs
    -------
    result: number, Any
        The result of the multiplication.
    """
    x, y = state.popn(2)
    return x * y


@svm.method("-")
def minus(state: svm.State):
    """
    Subtracts the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '-' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The second term.
    x: number, Any
        The first term.

    Outputs
    -------
    result: number, Any
        The result of the subtraction.
    """
    x, y = state.popn(2)
    return x - y


@svm.method("+")
def plus(state: svm.State):
    """
    Adds the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '+' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The second term.
    x: number, Any
        The first term.

    Outputs
    -------
    result: number, Any
        The result of the addition.
    """
    x, y = state.popn(2)
    return x + y


@svm.method("%")
def mod(state: svm.State):
    """
    Returns the modulous the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '%' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The divisor.
    x: number, Any
        The dividend.

    Outputs
    -------
    result: number, Any
        The result of x mod y.
    """
    x, y = state.popn(2)
    return x % y


@svm.method("not")
def not_(state: svm.State):
    """
    Inverts the True/False value at the top of the stack. If the item at the
    top of the stack is not a boolean value, it is coerced to a boolean and
    then inverted.

    Inputs
    ------
    x: bool, Any
        The boolean value to be inverted.

    Outputs
    -------
    x_inv: bool
        The inverse boolean value of x.
    """
    x = state.pop()
    return not x


@svm.method("and")
def and_(state: svm.State):
    """
    Logical AND of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    y: bool, Any
        The second term.
    x: bool, Any
        The first term.

    Outputs
    -------
    z: bool
        The result of the logical AND operation.
    """
    x, y = state.popn(2)
    return x and y


@svm.method("or")
def or_(state: svm.State):
    """
    Logical OR of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    y: bool, Any
        The second term.
    x: bool, Any
        The first term.

    Outputs
    -------
    z: bool
        The result of the logical OR operation.
    """
    x, y = state.popn(2)
    return x or y


@svm.method("xor")
def xor_(state: svm.State):
    """
    Logical XOR of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    y: bool, Any
        The second term.
    x: bool, Any
        The first term.

    Outputs
    -------
    z: bool
        The result of the logical XOR operation.
    """
    x, y = state.popn(2)
    return bool(x) != bool(y)
