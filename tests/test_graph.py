from agentgraph import InputNode, Node, DAG, AggregateNode, SimpleGraph


def add(x, y):
    return x + y


def mul(x, y):
    return x * y


def test_node_execute():
    node = Node("add_node", add)
    result = node.execute(3, 2)
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
    dag.add_edge("add_node", "mul_node", "x")
    assert len(dag.edges["add_node"]) == 1


def test_add_edge_detect_duplicate():
    input_node1 = InputNode("input1")
    input_node2 = InputNode("input2")
    some_node = Node("some_node", lambda x: x)

    dag = DAG()
    dag.add_node(input_node1)
    dag.add_node(input_node2)
    dag.add_node(some_node)

    dag.add_edge("input1", "some_node", "x")
    try:
        dag.add_edge("input2", "some_node", "x")
    except ValueError:
        pass
    else:
        raise AssertionError("Should have raised a ValueError!")


def test_add_edge_detect_duplicate():
    input_node1 = InputNode("input1")
    input_node2 = InputNode("input2")
    some_node = Node("some_node", lambda x: x)

    dag = DAG()
    dag.add_node(input_node1)
    dag.add_node(input_node2)
    dag.add_node(some_node)

    dag.add_edge("input1", "some_node", "x")
    try:
        dag.add_edge("input1", "some_node", "x")
    except ValueError:
        pass
    else:
        raise AssertionError("Should have raised a ValueError!")


def test_add_edge_invalid_input():
    input_node1 = InputNode("input1")
    some_node = Node("some_node", lambda x: x)

    dag = DAG()
    dag.add_node(input_node1)
    dag.add_node(some_node)

    try:
        dag.add_edge("input1", "some_node", "z")
    except ValueError:
        pass
    else:
        raise AssertionError("Should have raised a ValueError!")


def test_dag_input_node():
    input_node = InputNode("input")
    dag = DAG()
    dag.add_node(input_node)
    assert len(dag.nodes) == 1
    result = dag.execute({"input": 2})
    assert result["input"] == 2


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

    graph.add_edge("input1", "add", "x")
    graph.add_edge("input2", "add", "y")
    graph.add_edge("add", "mul", "x")
    graph.add_edge("input2", "mul", "y")

    outputs = graph.execute()

    assert outputs == {"input1": 2, "input2": 3, "add": 5, "mul": 15}


def test_missing_inputs():
    input_node1 = Node("input1", lambda: 2)
    input_node2 = Node("input2", lambda: 3)
    add_node = Node("add", add)

    graph = DAG()
    graph.add_node(input_node1)
    graph.add_node(input_node2)
    graph.add_node(add_node)

    graph.add_edge("input1", "add", "x")
    # forget the second edge

    try:
        graph.execute()
    except TypeError:
        pass
    else:
        raise AssertionError("Should have raised a TypeError!")


def test_extra_inputs():
    input_node1 = Node("input1", lambda: 2)
    input_node2 = Node("input2", lambda: 3)
    input_node3 = Node("input3", lambda: 4)
    add_node = Node("add", add)

    graph = DAG()
    graph.add_node(input_node1)
    graph.add_node(input_node2)
    graph.add_node(input_node3)
    graph.add_node(add_node)

    graph.add_edge("input1", "add", "x")
    graph.add_edge("input2", "add", "y")
    try:
        graph.add_edge("input3", "add", "z")
    except ValueError:
        pass
    else:
        raise AssertionError("Should have raised a ValueError!")


def test_dag_cycle_detection():
    dag = DAG()

    input_node = Node("input", lambda: 2)
    add_node = Node("add", add)
    mul_node = Node("mul", mul)

    dag.add_node(input_node)
    dag.add_node(add_node)
    dag.add_node(mul_node)

    dag.add_edge("input", "add", "x")
    dag.add_edge("add", "mul", "x")
    try:
        dag.add_edge("mul", "add", "y")
    except ValueError:
        pass
    else:
        raise AssertionError("Should have raised a ValueError!")


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
    graph.add_edge("input1", "add", "x")
    graph.add_edge("input2", "add", "y")

    # Execute the graph with input values
    output = graph.execute({"input1": 5, "input2": 3})
    assert output["add"] == 8, f'Expected 8, got {output["add"]}'

    # Execute the graph with different input values
    output = graph.execute({"input1": 7, "input2": 4})
    assert output["add"] == 11, f'Expected 11, got {output["add"]}'

    output = graph.execute_parallel({"input1": 7, "input2": 4})
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
    graph.add_edge("input", "double", "x")

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


def test_dag_execute_parallel():
    import time

    def slow_job(x):
        time.sleep(1)
        return x

    input_node = InputNode("input")
    slow_node1 = Node("slow1", slow_job)
    slow_node2 = Node("slow2", slow_job)
    slow_node3 = Node("slow3", slow_job)
    slow_node4 = Node("slow4", slow_job)
    slow_node5 = Node("slow5", slow_job)
    slow_node6 = Node("slow6", slow_job)
    slow_node7 = Node("slow7", slow_job)
    slow_node8 = Node("slow8", slow_job)

    def big_sum(a, b, c, d, e, f, g, h):
        return a + b + c + d + e + f + g + h

    big_sum_node = Node("sum", big_sum)

    graph = DAG()
    graph.add_node(input_node)
    graph.add_node(slow_node1)
    graph.add_node(slow_node2)
    graph.add_node(slow_node3)
    graph.add_node(slow_node4)
    graph.add_node(slow_node5)
    graph.add_node(slow_node6)
    graph.add_node(slow_node7)
    graph.add_node(slow_node8)
    graph.add_node(big_sum_node)

    graph.add_edge("input", "slow1", "x")
    graph.add_edge("input", "slow2", "x")
    graph.add_edge("input", "slow3", "x")
    graph.add_edge("input", "slow4", "x")
    graph.add_edge("input", "slow5", "x")
    graph.add_edge("input", "slow6", "x")
    graph.add_edge("input", "slow7", "x")
    graph.add_edge("input", "slow8", "x")

    graph.add_edge("slow1", "sum", "a")
    graph.add_edge("slow2", "sum", "b")
    graph.add_edge("slow3", "sum", "c")
    graph.add_edge("slow4", "sum", "d")
    graph.add_edge("slow5", "sum", "e")
    graph.add_edge("slow6", "sum", "f")
    graph.add_edge("slow7", "sum", "g")
    graph.add_edge("slow8", "sum", "h")

    start = time.time()
    output = graph.execute_parallel({"input": 1})
    finish = time.time()
    assert finish - start < 2, f"Parallel execution took {finish - start} seconds!"

    assert output["sum"] == 8, f'Expected 8, got {output["sum"]}'


def test_aggregate_node():
    # Create the graph
    graph = DAG()

    # Create the nodes
    input_node = InputNode("input")
    work1_node = Node("work1", lambda x: x + 1)
    work2_node = Node("work2", lambda x: x + 2)
    work3_node = Node("work3", lambda x: x + 3)
    aggregate_node = AggregateNode("aggregate", lambda x: x, lambda x: sum(x.values()))

    # Add the nodes to the graph
    graph.add_node(input_node)
    graph.add_node(work1_node)
    graph.add_node(work2_node)
    graph.add_node(work3_node)
    graph.add_node(aggregate_node)

    # Add edges between the nodes
    graph.add_edge("input", "work1", "x")
    graph.add_edge("input", "work2", "x")
    graph.add_edge("input", "work3", "x")
    graph.add_edge("work1", "aggregate", "x")
    graph.add_edge("work2", "aggregate", "x")
    graph.add_edge("work3", "aggregate", "x")

    # Execute the graph with input values
    output = graph.execute({"input": 0})
    assert output["aggregate"] == 6

    output = graph.execute_parallel({"input": 0})
    assert output["aggregate"] == 6


def test_simple_graph():
    def upper(input):
        return input.upper()

    def doubler(upper):
        return upper + upper

    def tripler(input):
        return input + input + input

    def joiner(doubler, tripler):
        return doubler + tripler

    graph = SimpleGraph()
    graph.add_functions([upper, doubler, tripler, joiner])

    output = graph.execute({"input": "hello"})
    assert output["joiner"] == "HELLOHELLOhellohellohello"

    output = graph.execute_parallel({"input": "hello"})
    assert output["joiner"] == "HELLOHELLOhellohellohello"
