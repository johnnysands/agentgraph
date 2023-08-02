import collections
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from .node import Node, InputNode, AggregateNode


class DAG:
    """DAG is the core class that represents a computation graph.

    Nodes are added to the graph using add_node().  Edges are added using add_edge().
    The execute() method is used to execute the graph.  It takes an optional input_values
    dictionary that is used to populate the values for any InputNode's in the graph. The
    output of the graph is a dictionary returned by the execute() method which contains the
    output of each node in the graph, keyed by the node name.
    """

    def __init__(self):
        self.nodes = {}
        self.edges = []
        # inverse list of edges for cycle detection and dependency counting
        # {to_node: [from_node, from_node, ...]}
        self.inverse_edges = collections.defaultdict(list)

    def add_node(self, node):
        if node.name in self.nodes:
            raise ValueError("Node with name {} already exists!".format(node.name))
        self.nodes[node.name] = node

    def add_edge(self, from_node, to_node, arg_name):
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist within the graph!")

        if any(edge[0] == from_node and edge[1] == to_node for edge in self.edges):
            raise ValueError(f"Edge already exists from {from_node} to {to_node}!")

        if arg_name not in self.nodes[to_node].signature.parameters:
            raise ValueError(
                f"Argument {arg_name} not in function signature for {to_node}!"
            )

        self.edges.append((from_node, to_node, arg_name))
        self.inverse_edges[to_node].append(from_node)
        self._cycle_check(to_node)

    def _execute_node(self, node_name, node_outputs):
        # Note: During parallel execution node_outputs is a copy and so should not be modified.
        inputs = {}

        for from_node, to_node, arg_name in self.edges:
            if to_node is not node_name:
                continue
            if isinstance(self.nodes[to_node], AggregateNode):
                if arg_name not in inputs:
                    inputs[arg_name] = {}
                inputs[arg_name][from_node] = node_outputs[from_node]
            else:
                inputs[arg_name] = node_outputs[from_node]
        return (node_name, self.nodes[node_name].execute(**inputs))

    def execute(self, input_values):
        """Execute the graph.

        Args:
            input_values: A dictionary of input values for the graph.  The keys are the
                node names, and the values are the input values for the nodes.  Provide
                an empty dictionary if there are no input values.
        """
        self._validate_input_values(input_values)

        # Compute the values from inputs to outputs.
        node_outputs = {}
        for node_name, value in input_values.items():
            node_outputs[node_name] = value

        # Run all nodes in post order
        post_order = self._topological_sort(self.nodes)
        for node in post_order:
            if isinstance(node, InputNode):
                pass
            else:
                _, output = self._execute_node(node.name, node_outputs)
                node_outputs[node.name] = output

        return node_outputs

    def execute_parallel(self, input_values=None):
        self._validate_input_values(input_values)

        node_outputs = {}
        with ThreadPoolExecutor() as executor:
            # We use the futures to track which nodes have just completed execution,
            # and then we decrement the dependency count for each of their children.
            futures = {}

            # Count the number of dependencies for each node
            dependencies = {
                node_name: len(self.inverse_edges[node_name])
                for node_name in self.nodes
            }

            # Run all nodes with zero dependencies, and populate the futures list
            # with initial values.
            for node_name, count in dependencies.items():
                if count > 0:
                    continue

                if isinstance(self.nodes[node_name], InputNode):
                    # Create a completed future that immediately returns the input value
                    # This feels unnecessary and can maybe be simplified.
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
            # counts and enqueue futures for any new nodes that are ready to run.
            while futures:
                for future in as_completed(futures.values()):
                    # record results
                    node_name, result = future.result()
                    node_outputs[node_name] = result

                    # update dependency counts and enqueue new futures
                    for _, dependent_node_name, _ in [
                        edge for edge in self.edges if edge[0] == node_name
                    ]:
                        dependencies[dependent_node_name] -= 1

                        # is the node ready to run?
                        if dependencies[dependent_node_name] == 0:
                            futures[dependent_node_name] = executor.submit(
                                self._execute_node,
                                dependent_node_name,
                                node_outputs,
                            )

                    # remove this node from the futures list
                    del futures[node_name]
        return node_outputs

    def _cycle_check(self, node_name):
        # Perform cycle check
        visited = set()

        def dfs(node_name):
            if node_name in visited:
                return True
            visited.add(node_name)
            return any(dfs(edge[1]) for edge in self.edges if edge[0] == node_name)

        if dfs(node_name):
            raise ValueError(f"Cycle in graph for {node_name}")

    def _topological_sort(self, nodes):
        # determine the order in which to execute the nodes
        visited = set()
        post_order = []

        def dfs(node_name):
            visited.add(node_name)
            for edge in self.edges:
                if edge[0] == node_name and edge[1] not in visited:
                    dfs(edge[1])
            post_order.append(self.nodes[node_name])

        for node_name in nodes:
            if node_name not in visited:
                dfs(node_name)

        post_order = list(reversed(post_order))
        return post_order

    def _validate_input_values(self, input_values):
        for node_name in input_values:
            if node_name not in self.nodes:
                raise ValueError(f"Input value provided for unknown node {node_name}")

        # validate that input is provided for all nodes without input edges
        for node_name in self.nodes:
            if node_name in input_values:
                if not isinstance(self.nodes[node_name], InputNode):
                    raise ValueError(
                        f"Input value provided for non-input node {node_name}"
                    )
                elif node_name in self.inverse_edges:
                    # this check might be redundant
                    raise ValueError(
                        f"Input value provided for node {node_name} with input edges"
                    )
            elif node_name not in self.inverse_edges:
                if isinstance(self.nodes[node_name], InputNode):
                    raise ValueError(f"No input value provided for node {node_name}")
                else:
                    raise ValueError(
                        f"{node_name} has no incoming edge and is not an input node"
                    )


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
        return self.dag.execute(input_values)

    def execute_parallel(self, input_values=None):
        self._execute_prep(input_values)
        return self.dag.execute_parallel(input_values)
