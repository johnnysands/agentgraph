# This is a demonstration of the ability to have multiple computations
# executing on the graph simultaneously, in addition to the ability
# for each execution to be internally parallelized.

import agentgraph
import concurrent
from concurrent.futures import ThreadPoolExecutor, wait

import time

# now we can execute the graph multiple times in parallel using concurrent futures
# and an executor


def execute_graph(execute_fn):
    # create an executor
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        # create a list of futures
        futures = []
        for i in range(10):
            # submit the graph to the executor, this will return a future
            future = executor.submit(execute_fn, {"input": f"HeLlO {i}"})
            futures.append(future)

        print("submitted all tasks")
        # wait for all the futures to complete
        wait(futures)
        print("all tasks completed")

        # get the results
        for future in futures:
            print(future.result()["final"])
    print(f"total time: {time.time() - start_time}")


def main():
    def upper(input):
        time.sleep(2)
        return input.upper()

    def lower(input):
        time.sleep(2)
        return input.lower()

    def final(upper, lower):
        return upper + " " + lower

    graph = agentgraph.SimpleGraph()
    graph.add_functions([upper, lower, final])

    # though we have multiple executions simultaneously, each execution is still
    # single threaded, so upper and lower will execute sequentially even though they
    # don't depend on each other
    print("executing with execute()")
    execute_graph(graph.execute)

    # when we execute the graph with execute_parallel instead, upper and lower will
    # execute in parallel
    print("executing with execute_parallel()")
    execute_graph(graph.execute_parallel)


if __name__ == "__main__":
    main()
