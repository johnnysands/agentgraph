from agentgraph import make_template_function, SimpleGraph


def test_make_template_function():
    template = "Hello {name}!"
    func = make_template_function("some_name", template)
    assert func(name="world") == "Hello world!"
    assert func("world") == "Hello world!"
    assert func.__name__ == "some_name"


def test_make_template_function_no_args():
    template = "Hello world!"
    func = make_template_function("some_name", template)
    assert func() == "Hello world!"


def test_make_template_function_two_args():
    template = "{greeting} {name}!"
    func = make_template_function("some_name", template)
    assert func(greeting="Hello", name="world") == "Hello world!"
    assert func("Hello", "world") == "Hello world!"


def test_make_template_function_no_args_with_args():
    template = "Hello {name}!"
    func = make_template_function("some_name", template)
    try:
        func()
    except TypeError:
        pass
    else:
        raise AssertionError("Expected TypeError")


def test_make_template_function_repeats():
    template = "Hello {name}! {name}!"
    func = make_template_function("some_name", template)
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
