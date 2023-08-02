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

from .graph import DAG, SimpleGraph
from .node import Node, InputNode, AggregateNode
