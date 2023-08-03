from agentgraph import template_function, template_function_with_handler, SimpleGraph


def test_template_function():
    template = "Hello {name}!"
    func = template_function("some_name", template)
    assert func(name="world") == "Hello world!"
    assert func("world") == "Hello world!"
    assert func.__name__ == "some_name"


def test_template_function_no_args():
    template = "Hello world!"
    func = template_function("some_name", template)
    assert func() == "Hello world!"


def test_template_function_two_args():
    template = "{greeting} {name}!"
    func = template_function("some_name", template)
    assert func(greeting="Hello", name="world") == "Hello world!"
    assert func("Hello", "world") == "Hello world!"


def test_template_function_no_args_with_args():
    template = "Hello {name}!"
    func = template_function("some_name", template)
    try:
        func()
    except TypeError:
        pass
    else:
        raise AssertionError("Expected TypeError")


def test_template_function_repeats():
    template = "Hello {name}! {name}!"
    func = template_function("some_name", template)
    assert func(name="world") == "Hello world! world!"
    assert func("world") == "Hello world! world!"


def test_template_function_graph():
    graph = SimpleGraph()

    graph.add_template_function("format", "Hello {input}!")
    output = graph.execute({"input": "world"})
    assert output["format"] == "Hello world!"


def test_template_function_graph_two_inputs():
    graph = SimpleGraph()

    graph.add_template_function("format", "Hello {input1} {input2}!")
    output = graph.execute({"input1": "world", "input2": "again"})
    assert output["format"] == "Hello world again!"


def test_template_function_mixed():
    graph = SimpleGraph()

    def upper(input1):
        return input1.upper()

    def lower(input2):
        return input2.lower()

    graph.add_functions([lower, upper])
    graph.add_template_function("greeting", "{upper} {lower}!")

    output = graph.execute({"input1": "hello", "input2": "WORLD"})
    assert output["greeting"] == "HELLO world!"


def test_template_function_with_handler():
    def handler(expanded_template):
        return expanded_template.upper()

    template = "Hello {name}!"
    func = template_function_with_handler("some_name", handler, template)
    assert func(name="world") == "HELLO WORLD!"
    assert func("world") == "HELLO WORLD!"
    assert func.__name__ == "some_name"


def test_template_function_with_handler_no_args():
    def handler(expanded_template):
        return expanded_template.upper()

    template = "Hello world!"
    func = template_function_with_handler("some_name", handler, template)
    assert func() == "HELLO WORLD!"


def test_add_template_function_with_handler():
    graph = SimpleGraph()

    def handler(expanded_template):
        return expanded_template.upper()

    graph.add_template_function_with_handler(
        "format", handler, "Hello {input} {input2}!"
    )
    output = graph.execute({"input": "world", "input2": "again"})
    assert output["format"] == "HELLO WORLD AGAIN!"
