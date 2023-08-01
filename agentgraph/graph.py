import inspect

# The basic idea here is that we can define a computation graph as a set of nodes
# and edges.  The nodes each process their input and emit their output.  The system
# routes the output to the downstream nodes.
# final nodes in the graph are the outputs of the graph.


class Node:
    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.signature = inspect.signature(func)
        self.input_mapping = dict()

    def map_input(self, arg_name, node):
        if arg_name in self.input_mapping:
            raise ValueError(
                f"Tried to map to {self.name}:{arg_name} from {node} but already mapped from {self.input_mapping[arg_name]}!"
            )
        if arg_name not in self.signature.parameters:
            raise ValueError(
                f"Argument {arg_name} not in function signature for {self.name}!"
            )

        self.input_mapping[arg_name] = node

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
        self.edges = {}
        self.inverse_edges = {}  # lookup from node to parents

    def add_node(self, node):
        if node.name in self.nodes:
            raise ValueError("Node with name {} already exists!".format(node.name))
        self.nodes[node.name] = node
        self.edges[node.name] = []
        self.inverse_edges[node.name] = []

    def add_edge(self, from_node, to_node, arg_name):
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist within the graph!")
        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)
            self.inverse_edges[to_node].append(from_node)
            self.nodes[to_node].map_input(arg_name, from_node)

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
            self.nodes[to_node].input_mapping.pop(arg_name)
            raise ValueError("Adding this edge creates a cycle!")

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
                inputs = {}
                for arg_name, input_node in node.input_mapping.items():
                    inputs[arg_name] = node_outputs[input_node]
                node_outputs[node.name] = node.execute(**inputs)

        return node_outputs
