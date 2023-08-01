"""Presently, we don't have a convenient way to aggregate a lot of nodes together without
specifying annoying aggregation functions that include many parameters and are unwieldy.
I'd like to add an aggregate node function, but I don't have an implementation yet.

In the mean time, this is one way to accomplish something similar.  We can create a subgraph
and then wrap it in a node.  This is a bit more verbose than I'd like, but it works.
"""

import agentgraph
import functools
import openai


def completion(input):
    messages = [
        {"role": "system", "content": "You assist in translations."},
        {"role": "user", "content": input},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return response["choices"][0]["message"]["content"]


def translate(language, input):
    return completion("Translate to " + language + ": " + input)


# create a node for each language
languages = [
    "Spanish",
    "Russian",
    "French",
    "Italian",
    "German",
    "Swedish",
    "Norwegian",
    "Danish",
    "Finnish",
    "Portugese",
]


def main_with_subgraph():
    # create subgraph
    subgraph = agentgraph.DAG()
    subgraph.add_node(agentgraph.InputNode("input"))
    for language in languages:
        fn = functools.partial(translate, language)
        subgraph.add_node(agentgraph.Node(language, fn))
        subgraph.add_edge("input", language, "input")

    # wrap subgraph in a node
    def subgraph_fn(input):
        # execute subgraph
        results = subgraph.execute_parallel({"input": input})
        # format output
        output = "Original message: + " + input + "\n"
        for language in languages:
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
