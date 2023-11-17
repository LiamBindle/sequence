import sequence


def get_xy_operands(state: sequence.State, value):
    if value is None:
        y = state.pop()
    else:
        y = value
    x = state.pop()
    return x, y

# comparison
@sequence.method("eq")
def equal(state: sequence.State, *, value=None):
    """
    Checks if x == y.

    Inputs
    ------
    [y]: Any
        The RHS operand.
    [x]: Any
        The LHS operand.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    xy_eq: bool
        The result of x == y.
    """
    x, y = get_xy_operands(state, value)
    return x == y


@sequence.method("neq")
def not_equal(state: sequence.State, *, value=None):
    """
    Checks if x is not equal to y.

    Inputs
    ------
    [y]: Any
        The RHS operand.
    [x]: Any
        The LHS operand.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    xy_neq: bool
        The result of x != y.
    """
    x, y = get_xy_operands(state, value)
    return x != y


@sequence.method("gt")
def greater_than(state: sequence.State, *, value=None):
    """
    Checks if x is greater than y.

    Inputs
    ------
    [y]: Any
        The RHS operand.
    [x]: Any
        The LHS operand.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    x_gt_y: bool
        The result of x > y.
    """
    x, y = get_xy_operands(state, value)
    return x > y


@sequence.method("ge")
def greater_than_or_equal_to(state: sequence.State, *, value=None):
    """
    Checks if x is greater than or equal to y.

    Inputs
    ------
    [y]: Any
        The RHS operand.
    [x]: Any
        The LHS operand.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    x_ge_y: bool
        The result of x >= y.
    """
    x, y = get_xy_operands(state, value)
    return x >= y


@sequence.method("lt")
def less_than(state: sequence.State, *, value=None):
    """
    Checks if x is less than y.

    Inputs
    ------
    [y]: Any
        The RHS operand.
    [x]: Any
        The LHS operand.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    x_lt_y: bool
        The result of x < y.
    """
    x, y = get_xy_operands(state, value)
    return x < y


@sequence.method("le")
def less_than_or_equal_to(state: sequence.State, *, value=None):
    """
    Checks if x is less than or equal to y.

    Inputs
    ------
    [y]: Any
        The RHS operand.
    [x]: Any
        The LHS operand.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    x_le_y: bool
        The result of x <= y.
    """
    x, y = get_xy_operands(state, value)
    return x <= y


@sequence.method("/")
def divide(state: sequence.State, *, value=None, div0_result: float = None):
    """
    Divides the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '/' is applied to the
    objects.

    Inputs
    ------
    [y]: number, Any
        The denominator.
    [x]: number, Any
        The numerator.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.
    [div0_result]: float
        If div0_result ir provided and y is zero, result is set to div0_result.

    Outputs
    -------
    result: number, Any
        The result of the division.
    """
    x, y = get_xy_operands(state, value)
    if div0_result is not None and isinstance(y, (float, int)) and y == 0:
        return div0_result
    return x / y


@sequence.method("*")
def multiply(state: sequence.State, *, value=None):
    """
    Multiplies the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '*' is applied to the
    objects.

    Inputs
    ------
    [y]: number, Any
        The second term.
    [x]: number, Any
        The first term.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    result: number, Any
        The result of the multiplication.
    """
    x, y = get_xy_operands(state, value)
    return x * y


@sequence.method("-")
def minus(state: sequence.State, *, value=None):
    """
    Subtracts the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '-' is applied to the
    objects.

    Inputs
    ------
    [y]: number, Any
        The second term.
    [x]: number, Any
        The first term.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    result: number, Any
        The result of the subtraction.
    """
    x, y = get_xy_operands(state, value)
    return x - y


@sequence.method("+")
def plus(state: sequence.State, *, value=None):
    """
    Adds the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '+' is applied to the
    objects.

    Inputs
    ------
    [y]: number, Any
        The second term.
    [x]: number, Any
        The first term.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    result: number, Any
        The result of the addition.
    """
    x, y = get_xy_operands(state, value)
    return x + y


@sequence.method("%")
def mod(state: sequence.State, *, value=None):
    """
    Returns the modulous the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '%' is applied to the
    objects.

    Inputs
    ------
    [y]: number, Any
        The divisor.
    [x]: number, Any
        The dividend.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    result: number, Any
        The result of x mod y.
    """
    x, y = get_xy_operands(state, value)
    return x % y


@sequence.method("not")
def not_(state: sequence.State, *, value=None):
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


@sequence.method("and")
def and_(state: sequence.State, *, value=None):
    """
    Logical AND of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    [y]: bool, Any
        The second term.
    [x]: bool, Any
        The first term.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    z: bool
        The result of the logical AND operation.
    """
    x, y = get_xy_operands(state, value)
    return x and y


@sequence.method("or")
def or_(state: sequence.State, *, value=None):
    """
    Logical OR of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    [y]: bool, Any
        The second term.
    [x]: bool, Any
        The first term.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    z: bool
        The result of the logical OR operation.
    """
    x, y = get_xy_operands(state, value)
    return x or y


@sequence.method("xor")
def xor_(state: sequence.State, *, value=None):
    """
    Logical XOR of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    [y]: bool, Any
        The second term.
    [x]: bool, Any
        The first term.

    Parameters
    ----------
    [value]: Any
        Used to specify y as a parameter. Disables input y when specified.

    Outputs
    -------
    z: bool
        The result of the logical XOR operation.
    """
    x, y = get_xy_operands(state, value)
    return bool(x) != bool(y)
