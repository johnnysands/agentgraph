# The basic idea here is that we can define a computation graph as a set of nodes
# and edges.  The nodes each process their input and emit their output.  The system
# routes the output to the downstream nodes.
# final nodes in the graph are the outputs of the graph.


class Node:
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def compute(self, *inputs):
        if self.func is not None:
            return self.func(*inputs)


class InputNode(Node):
    """InputNodes are supplied with their value at execution time."""

    def __init__(self, name):
        super().__init__(name, func=None)

    def compute(self):
        # Just return None, actual input values are provided in the execute call.
        return None


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

    def add_edge(self, from_node, to_node):
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist within the graph!")
        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)
            self.inverse_edges[to_node].append(from_node)

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
                inputs = [node_outputs[n] for n in self.inverse_edges[node.name]]
                node_outputs[node.name] = node.compute(*inputs)

        return node_outputs


class LinearGraph(DAG):
    """A linear graph is a DAG where each node has exactly one parent.
    This can provide a simpler API for defining a graph"""

    def __init__(self):
        super().__init__()
        self.last_node = None

    def add_node(self, node):
        super().add_node(node)
        if self.last_node is not None:
            self.add_edge(self.last_node.name, node.name)
        self.last_node = node
