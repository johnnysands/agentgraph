"""AgentGraph is a library for building computation graphs to enable complex multi-stage
processing of input. It is designed to be used in situations where you have a set of
functions that you want to execute in parallel, and then aggregate the results of those
functions into a single output, such as a chatbot that uses a multi-stage process for
generating responses.

To use AgentGraph there are two interfaces: SimpleGraph and DAG.  SimpleGraph is a wrapper
around DAG that makes it easier to define a graph.  DAG is the core class that implements
the computation graph.

Node names are used to identify nodes in the graph.  Node names must be unique within the
graph.
"""

import inspect


class Node:
    """Node is the core class that represents a node in the computation graph.

    Nodes are created by passing a function to the constructor.  The function must have
    a signature that matches the inputs to the node.  The function can return any value,
    and that value will be passed to the next node in the graph.

    Example:
        def static_fn(): # always returns the same value
            return "Hello world!"

        dag = DAG()
        dag.add_node(Node("static", static_fn))
        output = dag.execute()
        assert output["static"] == "Hello world!"
    """

    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.signature = inspect.signature(func)

    def execute(self, *argc, **kwargs):
        try:
            return self.func(*argc, **kwargs)
        except TypeError as e:
            raise TypeError(
                f"{self.name} got error calling {self.func.__name__} with args {argc} and kwargs {kwargs}"
            ) from e


class InputNode(Node):
    """InputNodes are how input is injected into the computation graph.

    They are essentially placeholder nodes.  Their value at computation time is
    determined by the input_values dictionary passed to DAG.execute().

    Example:
        dag = DAG()
        dag.add_node(InputNode("input"))
        dag.add_node(Node("output", lambda x: x * 2))
        dag.add_edge("input", "output", "x")

        output = dag.execute({"input": 2})
        assert output["output"] == 4
    """

    def __init__(self, name):
        self.name = name

    def execute(self):
        raise NotImplementedError("InputNodes cannot be executed!")


class AggregateNode(Node):
    """AggregateNode receives multiple inputs in a single value.  It's purpose is as a convenience
    when joining many related streams together.  It accomplishes this by defining an aggregate_func
    in addition to the normal processing_func.  the aggregate_func aggregates the values, and its output
    is then passed to the processing func.

    There is a design limitation that needs to be fixed here, which is that the aggregate_func and the
    processing_func have to have the same signature.

    Example:
        def aggregate_fn(x):
            return sum(x)

        def processing_fn(x):
            return x * 2

        dag = DAG()
        dag.add_node(InputNode("input"))
        dag.add_node(InputNode("input2"))
        dag.add_node(InputNode("input3"))
        dag.add_node(AggregateNode("aggregate", processing_fn, aggregate_fn))

        dag.add_edge("input", "aggregate", "x")
        dag.add_edge("input2", "aggregate", "x")
        dag.add_edge("input3", "aggregate", "x")

        dag.execute({"input": 1, "input2": 2, "input3": 3})
        assert dag.nodes["aggregate"].output == 12"""

    def __init__(self, name, func, aggregate_func):
        super().__init__(name, func)
        self.aggregate_func = aggregate_func

    def execute(self, *argc, **kwargs):
        # TODO: there is a bug here.  the aggregate fn and the input fn have to have the same signature
        # Maybe the aggregate function should be eliminated and we should only provide a processing function
        # that only performs the aggregation?
        aggregated = self.aggregate_func(*argc, **kwargs)
        return super().execute(aggregated)
