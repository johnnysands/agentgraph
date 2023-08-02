import inspect
import string


def make_template_function(name, format_string):
    """Creates a function from a format string template. The parameters of the function will be the keys in the template."""
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
        return format_string.format(**bound_values.arguments)

    func.__signature__ = sig
    func.__name__ = name
    return func
