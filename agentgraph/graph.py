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

import collections
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
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


class DAG:
    """DAG is the core class that represents a computation graph.

    Nodes are added to the graph using add_node().  Edges are added using add_edge().
    The execute() method is used to execute the graph.  It takes an optional input_values
    dictionary that is used to populate the values for any InputNode's in the graph. The
    output of the graph is a dictionary returned by the execute() method which contains the
    output of each node in the graph, keyed by the node name.
    """

    def __init__(self):
        # TODO this should be refactored.  edges originally were just node-to-node mappings,
        # but we started mapping to arguments as well, but we're keeping track of arguments
        # seperately in input_mapping. Probably this should just be a list of 3-tuples or something.
        self.nodes = {}
        # list of edges: {from_node: [to_node, to_node, ...]}
        self.edges = collections.defaultdict(list)
        # inverse list of edges for cycle detection and dependency counting
        # {to_node: [from_node, from_node, ...]}
        self.inverse_edges = collections.defaultdict(list)

        # input mapping is what helps us map the input from other nodes to the right function arguments.
        # the format is {node_name: {arg_name: input_node_name}} where input_node_name is either a single
        # node name or a list of node names in the case of an AggregateNode.
        # the output of input_node_name is passed to the function argument arg_name for node_name.
        self.input_mapping = collections.defaultdict(dict)

    def add_node(self, node):
        if node.name in self.nodes:
            raise ValueError("Node with name {} already exists!".format(node.name))
        self.nodes[node.name] = node

    def add_edge(self, from_node, to_node, arg_name):
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist within the graph!")

        # strictly speaking wecould allow this, but it most likely indicates an
        # error in the user's code, so we raise an error because I don't think
        # there's a situation where you would really need to do this.
        if to_node in self.edges[from_node]:
            raise ValueError(f"Edge already exists from {from_node} to {to_node}!")

        self.edges[from_node].append(to_node)
        self.inverse_edges[to_node].append(from_node)

        # update input mapping
        if arg_name in self.input_mapping[to_node]:
            # if to_node is an AggregateNode, append from_node.
            if isinstance(self.nodes[to_node], AggregateNode):
                self.input_mapping[to_node][arg_name].append(from_node)
            else:
                raise ValueError(
                    f"Tried to map to {to_node}:{arg_name} from {from_node} but already mapped from {self.input_mapping[to_node][arg_name]}!"
                )
        else:
            # create a list for an AggregateNode, single value for others
            if isinstance(self.nodes[to_node], AggregateNode):
                self.input_mapping[to_node][arg_name] = [from_node]
            else:
                self.input_mapping[to_node][arg_name] = from_node

        if arg_name not in self.nodes[to_node].signature.parameters:
            raise ValueError(
                f"Argument {arg_name} not in function signature for {to_node}!"
            )

        # check for cycles
        visited = set()

        def dfs(node):
            if node == from_node:
                return True
            if node in visited:
                return False
            visited.add(node)
            return any(dfs(next_node) for next_node in self.edges[node])

        if dfs(to_node):
            raise ValueError(
                f"adding edge from {from_node} to {to_node} created a cycle"
            )

    def _execute_node(self, node_name, node_outputs):
        # During parallel execution node_outputs is a copy
        inputs = {}
        for arg_name, input_node in self.input_mapping[node_name].items():
            if isinstance(input_node, list):
                # AggregateNode
                inputs[arg_name] = {n: node_outputs[n] for n in input_node}
            else:
                # all other nodes
                inputs[arg_name] = node_outputs[input_node]
        return (node_name, self.nodes[node_name].execute(**inputs))

    def execute_parallel(self, input_values=None):
        node_outputs = {}

        with ThreadPoolExecutor() as executor:
            # Count the number of dependencies for each node
            num_dependencies = {
                node_name: len(self.inverse_edges[node_name])
                for node_name in self.nodes
            }

            # We use the futures to track which nodes have just completed execution,
            # and then we decrement the dependency count for each of their children.
            futures = {}

            # Run all nodes with zero dependencies.
            for node_name, count in num_dependencies.items():
                if count > 0:
                    continue

                node = self.nodes[node_name]
                if isinstance(node, InputNode):
                    if input_values is None or node_name not in input_values:
                        raise ValueError(
                            f"Input value not provided for node {node.name}"
                        )
                    # Create a completed future that immediately returns the input value
                    input_future = Future()
                    input_future.set_result((node_name, input_values[node_name]))
                    futures[node_name] = input_future
                else:
                    futures[node_name] = executor.submit(
                        self._execute_node, node_name, node_outputs
                    )

            # loop over futures until all nodes have been executed.
            # futures will always have at least one element until all work is done.
            # this is because as soon as a future completes, we decrement the dependency
            # counts and enqueue futures for any new jobs that are ready to run.
            while futures:
                for future in as_completed(futures.values()):
                    # record results
                    node_name, result = future.result()
                    node_outputs[node_name] = result

                    # update dependency counts and enqueue new futures
                    for dependent_node_name in self.edges[node_name]:
                        num_dependencies[dependent_node_name] -= 1

                        # is the node ready to run?
                        if num_dependencies[dependent_node_name] == 0:
                            futures[dependent_node_name] = executor.submit(
                                self._execute_node,
                                dependent_node_name,
                                node_outputs,
                            )

                    # remove this node from the futures list
                    del futures[node_name]
        return node_outputs

    def execute(self, input_values=None):
        # Perform topological sort
        visited = set()
        post_order = []

        def dfs(node_name):
            visited.add(node_name)
            for child_name in self.edges[node_name]:
                if child_name not in visited:
                    dfs(child_name)
            post_order.append(self.nodes[node_name])

        for node_name in self.nodes:
            if node_name not in visited:
                dfs(node_name)

        post_order = list(reversed(post_order))

        # Compute the values from inputs to outputs.
        node_outputs = {}
        if input_values is not None:
            # validate that input is provided for all nodes without input edges
            for node_name in self.nodes:
                if node_name in self.inverse_edges:
                    # validate that each node with an incoming edge has no input values
                    if node_name in input_values:
                        raise ValueError(
                            f"Input value provided for node {node_name} with input edges"
                        )
                else:
                    # validate that each node without an incoming edge has an input value
                    if node_name not in input_values:
                        raise ValueError(
                            f"Input value not provided for node {node_name}"
                        )
            for node_name, value in input_values.items():
                node_outputs[node_name] = value

        # Run all nodes in post order
        for node in post_order:
            if isinstance(node, InputNode):
                pass
            else:
                _, output = self._execute_node(node.name, node_outputs)
                node_outputs[node.name] = output

        return node_outputs


class SimpleGraph:
    """A wrapper for DAG that makes it easier to define a graph.

    Functions are added to the graph, and the edges are defined automatically by
    looking at the name of the functions and the name of the inputs to the functions.

    Example:

        def embedding(query):
            ...

        def similar_documents(embedding):
            ...

        def completion(query, similar_documents):
            ...

        def safety_check(query, completion, similar_documents):
            ...

        def log(query, completion, safety_check):
            ...

        graph = SimpleGraph()
        graph.add_functions([embedding, similar_documents, completion, safety_check, log])
        graph.execute_parallel({"query": "Hello world!"})
    """

    def __init__(self):
        self.dag = DAG()
        self.prepared = False

    def add_function(self, function):
        if self.prepared:
            raise ValueError("Cannot add functions after graph has been prepared!")
        node = Node(function.__name__, function)
        self.dag.add_node(node)
        return function

    def add_functions(self, functions):
        for function in functions:
            self.add_function(function)

    def _create_edges(self):
        for node in self.dag.nodes:
            if isinstance(self.dag.nodes[node], InputNode):
                continue
            for arg in self.dag.nodes[node].signature.parameters:
                if arg in self.dag.nodes:
                    self.dag.add_edge(arg, node, arg)

    def _execute_prep(self, input_values=None):
        if not self.prepared:
            for node_name in input_values.keys():
                self.dag.add_node(InputNode(node_name))

            self._create_edges()
            self.prepared = True

    def execute(self, input_values=None):
        self._execute_prep(input_values)
        print(self.dag.edges)
        return self.dag.execute(input_values)

    def execute_parallel(self, input_values=None):
        self._execute_prep(input_values)
        return self.dag.execute_parallel(input_values)
