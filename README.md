# AgentGraph

Agent Graph is an experimental execution framework that aims to support the development of
automated agents. It provides a computation graph that supports parallel execution.  It comes with
two APIs: a simpler, more limited option called SimpleGraph, and the full featured DAG API.

## SimpleGraph

High level simple wrapper that makes it as easy as possible to define a graph, but
at the cost of some flexibility.

Define functions, and add them to the graph.  The edges are defined automatically by
matching the names of functions with the names of arguments of other functions.  Whatever
a function returns is automatically routed to the input of any downstream function.

Here's a simple example:

```python
def upper(text):
    return text.upper()

def double(upper):
    return upper + upper

graph = SimpleGraph()
graph.add_functions([upper, double])
output = graph.execute({"text": "Hello"})
print(output["double"]) # outputs "HELLOHELLO"
```

Here's a more involved example that gives an idea of how the library might be used with a chat agent.

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

Functions can also be added to SimpleGraph with a decorator.

```python
graph = SimpleGraph()

@graph.add_function
def some_thing(query):
    ...

output = graph.execute_parallel({"query": "Hello world!"})
```

## DAG
DAG is the core computation graph class. SimpleGraph wraps DAG, and hides much of
the complexity, but if you need more flexibility or control, you can use DAG directly.

Node types are defined in agentgraph.node, and are added to the graph using add_node().
Edges are added to the graph using add_edge().

execute() or execute_parallel() are used to execute the graph.  InputNodes in the
graph are seeded with initial values from the input_values argument to the execute
functions.  The output of the graph is returned from the execute call, and consists
of a dictionary with the output of each node, keyed by node name.

Example:
```python
graph = DAG()
graph.add_node(InputNode("input"))
graph.add_node(Node("output", lambda x: x * 2))
dag.add_edge("input", "output", "x")

output = dag.execute({"input": 2})
assert output["output"] == 4
```

AggregationNodes can be used to join together similar computations and process the
results at one time.  This is mostly useful to simplify the code that needs to be written
when building a graph.  See translate_aggregate.py under examples for usage.