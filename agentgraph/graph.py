import collections
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import inspect

# The basic idea here is that we can define a computation graph as a set of nodes
# and edges.  The nodes each process their input and emit their output.  The system
# routes the output to the downstream nodes.


class Node:
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
    """InputNodes are supplied with their value at execution time."""

    def __init__(self, name):
        self.name = name

    def execute(self):
        raise NotImplementedError("InputNodes cannot be executed!")


class DAG:
    def __init__(self):
        self.nodes = {}
        self.edges = collections.defaultdict(list)
        self.inverse_edges = collections.defaultdict(list)

        # input mapping is what helps us map the input from other nodes to the right function arguments.
        # the format is {node_name: {arg_name: input_node_name}}
        self.input_mapping = collections.defaultdict(dict)

    def add_node(self, node):
        if node.name in self.nodes:
            raise ValueError("Node with name {} already exists!".format(node.name))
        self.nodes[node.name] = node

    def add_edge(self, from_node, to_node, arg_name):
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist within the graph!")

        # strictly speaking this is legal, but it most likely indicates an
        # error in the user's code, so we raise an error because I don't think
        # there's a particularly good reason to do this.
        if to_node in self.edges[from_node]:
            raise ValueError("Edge already exists!")

        self.edges[from_node].append(to_node)
        self.inverse_edges[to_node].append(from_node)

        # update input mapping
        if arg_name in self.input_mapping[to_node]:
            raise ValueError(
                f"Tried to map to {to_node}:{arg_name} from {from_node} but already mapped from {self.input_mapping[to_node][arg_name]}!"
            )
        if arg_name not in self.nodes[to_node].signature.parameters:
            raise ValueError(
                f"Argument {arg_name} not in function signature for {to_node}!"
            )
        self.input_mapping[to_node][arg_name] = from_node

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
            # Adding this edge created a cycle, so remove it and raise an error
            self.edges[from_node].remove(to_node)
            self.inverse_edges[to_node].remove(from_node)
            self.input_mapping[to_node].pop(arg_name)
            raise ValueError(
                f"adding edge from {from_node} to {to_node} would create a cycle"
            )

    def _execute_node(self, node_name, node_outputs):
        # During parallel execution node_outputs is a copy
        inputs = {}
        for arg_name, input_node in self.input_mapping[node_name].items():
            try:
                inputs[arg_name] = node_outputs[input_node]
            except KeyError:
                raise KeyError(
                    f"Node {node.name} expected input {arg_name} from node {input_node} but it was not provided!"
                )
        return (node_name, self.nodes[node_name].execute(**inputs))

    def execute_parallel(self, input_values=None):
        # Compute the values from inputs to outputs.
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
                        self._execute_node, node, node_outputs
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
        for node in post_order:
            if isinstance(node, InputNode):
                if input_values is None or node.name not in input_values:
                    raise ValueError(f"Input value not provided for node {node.name}")
                node_outputs[node.name] = input_values[node.name]
            else:
                _, output = self._execute_node(node.name, node_outputs)
                node_outputs[node.name] = output

        return node_outputs
