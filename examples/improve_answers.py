"""A simple example that utilizes template functions to generate a multi-stage response to a user's input."""

import agentgraph as ag
import openai
from rich.console import Console
from rich.markdown import Markdown


def chat_completion_handler(content):
    """Create a chat completion with OpenAI's API."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": content},
    ]
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return completion.choices[0].message.content


def setup_graph():
    graph = ag.SimpleGraph()

    graph.add_template_function_with_handler(
        "response",
        chat_completion_handler,
        "{input}",
    )
    graph.add_template_function_with_handler(
        "critic",
        chat_completion_handler,
        "Here is an answer to the query: {input}\nThe answer: {response}\n\nPlease provide a thoughtful critique of this response.",
    )
    graph.add_template_function_with_handler(
        "final",
        chat_completion_handler,
        "Here is an answer to the query: {input}\nThe answer: {response}\n\nAn analysis of this response follows: {critic}\n\nPlease answer the query, taking into account the previous response and analysis. Query: {input}",
    )
    graph.add_template_function_with_handler(
        "comparison",
        chat_completion_handler,
        "Which of the two responses to the following query are the best, the first or second one?\n\nQuery: {input}\n\nFirst response: {response}\n\nSecond response: {final}",
    )
    return graph


graph = setup_graph()
question = "Write a shell script to split the lines from a large file randomly into two outfiles."
output = graph.execute({"input": question})

console = Console()
console.print(Markdown("# Initial response"))
console.print(Markdown(output["response"]))
console.print(Markdown("# Critique"))
console.print(Markdown(output["critic"]))
console.print(Markdown("# Final response"))
console.print(Markdown(output["final"]))
console.print(Markdown("# Comparison"))
console.print(Markdown(output["comparison"]))
