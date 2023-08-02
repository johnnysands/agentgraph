# AgentGraph

Agent Graph is a generic execution framework to execute a DAG of dependent computations.  It supports
parallel execution and has both a full featured and simplified API.

## SimpleGraph

A wrapper for DAG that makes it easier to define a graph.

Functions are added to the graph, and the edges are defined automatically by
looking at the name of the functions and the name of the inputs to the functions.


Example:
```python
def embedding(query):
    ...

def similar_documents(embedding):
    ...

def completion(query, similar_documents):
    ...

def safety_check(query, completion, similar_documents):
    ...

def final(query, completion, safety_check):
    ...

def log(final):
    ...

graph = SimpleGraph()
graph.add_functions([embedding, similar_documents, completion, safety_check, log])

output = graph.execute_parallel({"query": "Hello world!"})
print(output["final"])
```

There is also a decorator form for adding functions to SimpleGraph.

```python
graph = SimpleGraph()

@graph.add_function
def some_thing(query):
    ...

output = graph.execute_parallel({"query": "Hello world!"})
```

## DAG
DAG is the core computation graph class.

Nodes are added to the graph using add_node().  Edges are added using add_edge().

execute() or execute_parallel() are called to execute the graph.  InputNodes in the
graph are seeded with initial values from input_values.  The output of the graph is
returned from the execute call, and consists of a dictionary with the output of
each node, keyed by node name.

Example:
```python
graph = DAG()
graph.add_node(InputNode("input"))
graph.add_node(Node("output", lambda x: x * 2))
dag.add_edge("input", "output", "x")

output = dag.execute({"input": 2})
assert output["output"] == 4
```

There are also AggregationNodes which can be used to join together similar computations
and process the results at one time.  See translate_aggregate.py under examples for usage.
