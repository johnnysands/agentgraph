"""
This example is just demonstrating the functionality of the execute_parallel method.

Since the graph is a DAG, we can often execute nodes in parallel that do not depend
on each other.  This is a simple example of how to do that that simply parallelizes
the execution of a bunch of similar translation calls.
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


def main():
    # create graph and top level input node
    dag = agentgraph.DAG()
    dag.add_node(agentgraph.InputNode("input"))

    for language in languages:
        fn = functools.partial(translate, language)
        dag.add_node(agentgraph.Node(language, fn))
        dag.add_edge("input", language, "input")

    # get the user input and execute the graph
    user_input = input("Enter a message: ")

    results = dag.execute_parallel({"input": user_input})
    for language in languages:
        print(language + ": " + results[language])


if __name__ == "__main__":
    main()
