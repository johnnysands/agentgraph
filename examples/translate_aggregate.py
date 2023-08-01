"""
This example demonstrates the use of an AggregateNode to aggregate the results of a
set of similar nodes.
"""
import agentgraph
import functools
import util


def main():
    # create graph and top level input node
    dag = agentgraph.DAG()
    dag.add_node(agentgraph.InputNode("input"))

    # add the aggregate node, this will be the final node in the graph.
    def aggregate_fn(x):
        output = ""
        for k, v in x.items():
            output += k + ": " + v + "\n"
        return output

    dag.add_node(agentgraph.AggregateNode("aggregate", lambda x: x, aggregate_fn))

    # create a node for each language and connect them to input and aggregate
    for language in util.languages:
        fn = functools.partial(util.translate, language)
        dag.add_node(agentgraph.Node(language, fn))

        dag.add_edge("input", language, "input")
        dag.add_edge(language, "aggregate", "x")

    # get the user input and execute the graph
    user_input = input("Enter a message: ")
    results = dag.execute_parallel({"input": user_input})
    print(results["aggregate"])


if __name__ == "__main__":
    main()
