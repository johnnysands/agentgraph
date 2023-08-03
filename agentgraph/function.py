import inspect
import openai
import string


def identity_handler(expanded_template):
    """Returns its input without modification."""
    return expanded_template


def template_function(name, format_string):
    """Creates a function from a format string template. The parameters of the function will be the keys in the template."""
    return template_function_with_handler(name, identity_handler, format_string)


def template_function_with_handler(name, handler, format_string):
    """Creates a function from a format string template and a handler.  The parameters of the function will be the keys in the template.
    The handler is called with the formatted string and the function's return value is the handler's return value.
    """
    fields = [
        fname for _, fname, _, _ in string.Formatter().parse(format_string) if fname
    ]
    fields = list(dict.fromkeys(fields))  # remove duplicates. Python 3.7+ only

    params = [
        inspect.Parameter(field, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for field in fields
    ]
    sig = inspect.Signature(params)

    def func(*args, **kwargs):
        bound_values = sig.bind(*args, **kwargs)
        expanded_template = format_string.format(**bound_values.arguments)
        return handler(expanded_template)

    func.__signature__ = sig
    func.__name__ = name
    return func
