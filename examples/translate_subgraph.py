"""This was created before AggregateNode was implemented as an alternative way to accomplish
something similar.

This uses a subgraph to encapsulate a set of related work.  The subgraph is then wrapped
in a function and used as a node in a higher level graph.
"""

import agentgraph
import functools
import util


def main_with_subgraph():
    # create subgraph
    subgraph = agentgraph.DAG()
    subgraph.add_node(agentgraph.InputNode("input"))
    for language in util.languages:
        fn = functools.partial(util.translate, language)
        subgraph.add_node(agentgraph.Node(language, fn))
        subgraph.add_edge("input", language, "input")

    # wrap subgraph in a node
    def subgraph_fn(input):
        # execute subgraph
        results = subgraph.execute_parallel({"input": input})
        # format output
        output = "Original message: + " + input + "\n"
        for language in util.languages:
            output += language + ": " + results[language] + "\n"
        return output

    subgraph_node = agentgraph.Node("subgraph", subgraph_fn)

    # create graph and top level input node
    dag = agentgraph.DAG()
    dag.add_node(agentgraph.InputNode("input"))
    dag.add_node(subgraph_node)
    dag.add_edge("input", "subgraph", "input")

    # get the user input and execute the top level graph
    user_input = input("Enter a message: ")
    results = dag.execute_parallel({"input": user_input})
    print(results["subgraph"])


if __name__ == "__main__":
    main_with_subgraph()
