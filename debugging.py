# For all decorators
from functools import wraps

# For benchmarking
import time

# For type checking
from typing import get_type_hints, get_origin, get_args, Union
import inspect
import types


def benchmark(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__}: {end-start:g}")
        return result

    return wrapper

def type_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        type_hints = get_type_hints(func)
        signature = inspect.signature(func)
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()

        def normalize_type(type_arg):
            return repr(type_arg.__name__)

        def type_checker(name, value, expected_type, unknown_type=False):
            origin = get_origin(expected_type)
            type_args = get_args(expected_type)

            expected_type_name = normalize_type(origin or expected_type)
            actual_type_name = normalize_type(type(value)) if not unknown_type else "something else"

            error_msg = (f"Expected {func.__name__} function to return value of type {expected_type_name}, returned {actual_type_name} instead."
                if name == "return" 
                else f"Expected type {expected_type_name} for {name} parameter, got {actual_type_name} instead."
            )

            if origin in (Union, types.UnionType):
                if not any(isinstance(value, arg) for arg in type_args):
                    raise TypeError(f"Parameter {name} is not of any allowed types: {', '.join(arg.__name__ for arg in type_args)}")

            elif origin:
                if not isinstance(value, origin):
                    raise TypeError(error_msg)
                if type_args:
                    if origin in (list, tuple):
                        for item in value:
                            type_checker(name, item, args[0], unknown_type=True)
                    if origin is dict:
                        key_type, val_type = args
                        for key, val in value.items():
                            type_checker(name, key, key_type, unknown_type=True)
                            type_checker(name, val, val_type, unknown_type=True)


            elif not isinstance(value, expected_type):
                raise TypeError(error_msg)

        for param_name, value in bound_args.arguments.items():
            expected_type = type_hints.get(param_name)

            if expected_type:
                type_checker(param_name, value, expected_type)

        result = func(*args, **kwargs)

        return_type = type_hints.get("return")
        if return_type:
            type_checker("return", result, return_type)

        return result

    return wrapper
