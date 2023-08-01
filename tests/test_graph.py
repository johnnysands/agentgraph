from agentgraph import InputNode, Node, DAG, LinearGraph


def add(x, y):
    return x + y


def mul(x, y):
    return x * y


def test_node_compute():
    node = Node("add_node", add)
    result = node.compute(3, 2)
    assert result == 5


def test_add_node_to_dag():
    node = Node("add_node", add)
    dag = DAG()
    dag.add_node(node)
    assert len(dag.nodes) == 1


def test_add_edge_to_dag():
    node1 = Node("add_node", add)
    node2 = Node("mul_node", mul)
    dag = DAG()
    dag.add_node(node1)
    dag.add_node(node2)
    dag.add_edge("add_node", "mul_node")
    assert len(dag.edges["add_node"]) == 1


def test_dag_execution():
    # create nodes
    input_node1 = Node("input1", lambda: 2)
    input_node2 = Node("input2", lambda: 3)
    add_node = Node("add", add)
    mul_node = Node("mul", mul)

    # create dag
    graph = DAG()
    graph.add_node(input_node1)
    graph.add_node(input_node2)
    graph.add_node(add_node)
    graph.add_node(mul_node)

    graph.add_edge("input1", "add")
    graph.add_edge("input2", "add")
    graph.add_edge("add", "mul")
    graph.add_edge("input2", "mul")

    outputs = graph.execute()

    assert outputs == {"input1": 2, "input2": 3, "add": 5, "mul": 15}


def test_dag_cycle_detection():
    dag = DAG()

    input_node = Node("input", lambda: 2)
    add_node = Node("add", add)
    mul_node = Node("mul", mul)

    dag.add_node(input_node)
    dag.add_node(add_node)
    dag.add_node(mul_node)

    dag.add_edge("input", "add")
    dag.add_edge("add", "mul")
    try:
        dag.add_edge("mul", "add")
    except ValueError:
        pass
    else:
        raise AssertionError("Should have raised a ValueError!")


def test_linear_graph():
    graph = LinearGraph()
    graph.add_node(Node("input1", lambda: 2))
    graph.add_node(Node("square", lambda x: x**2))
    graph.add_node(Node("str", lambda x: str(x)))

    result = graph.execute()
    assert result == {"input1": 2, "square": 4, "str": "4"}


def test_execute_with_input_nodes():
    # Create the graph
    graph = DAG()

    # Create the nodes
    input1 = InputNode("input1")
    input2 = InputNode("input2")
    add_node = Node("add", lambda x, y: x + y)

    # Add the nodes to the graph
    graph.add_node(input1)
    graph.add_node(input2)
    graph.add_node(add_node)

    # Add edges between the nodes
    graph.add_edge("input1", "add")
    graph.add_edge("input2", "add")

    # Execute the graph with input values
    output = graph.execute({"input1": 5, "input2": 3})
    assert output["add"] == 8, f'Expected 8, got {output["add"]}'

    # Execute the graph with different input values
    output = graph.execute({"input1": 7, "input2": 4})
    assert output["add"] == 11, f'Expected 11, got {output["add"]}'


def test_missing_input_values():
    # Create the graph
    graph = DAG()

    # Create the nodes
    input_node = InputNode("input")
    double_node = Node("double", lambda x: x * 2)

    # Add the nodes to the graph
    graph.add_node(input_node)
    graph.add_node(double_node)

    # Add an edge between the nodes
    graph.add_edge("input", "double")

    # Attempt to execute the graph without providing an input value
    try:
        graph.execute({})
    except ValueError as e:
        assert (
            str(e) == "Input value not provided for node input"
        ), f"Unexpected error message: {str(e)}"
    else:
        raise AssertionError("Should have raised a ValueError!")

    # Now provide an input value and ensure it works correctly
    output = graph.execute({"input": 7})
    assert output["double"] == 14, f'Expected 14, got {output["double"]}'
