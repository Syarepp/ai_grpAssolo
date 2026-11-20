from __future__ import annotations
from pathlib import Path

import math
import sys

from core.graph import Graph, Node
from core.search import SearchProblem
from core.load_test import PathFinderData, load_test_file
from route_finding.uniform_cost_search import UniformCostSearch
from route_finding.hill_climbing_search import HillClimbingSearch
from route_finding.depth_first_search import DepthFirstSearch
from route_finding.best_first_search import GreedyBestFirstSearch
from route_finding.breadth_first_search import BreadthFirstSearch
from route_finding.a_star_search import AStarSearch


ALGORITHM_OPTIONS = {
    "A* Search": AStarSearch,
    "Greedy-Best-First Search": GreedyBestFirstSearch,
    "Breadth-First Search": BreadthFirstSearch,
    "Depth-First Search": DepthFirstSearch,
    "Hill Climbing Search": HillClimbingSearch,
    "Uniform Cost Search": UniformCostSearch,
}


def find_test_cases(directory: Path) -> list[Path]:
    return [
        path
        for number in range(1, 17)
        if (path := directory / f"PathFinder-test-{number}.txt").is_file()
    ]


class RouteFinder:
    def __init__(self, data: PathFinderData, file_path: str, algorithm: str):
        self.data = data
        self.file_path = file_path
        self.searcher = ALGORITHM_OPTIONS[algorithm]()
        
        # Get test cases available
        directory = Path(file_path).parent
        self.test_cases = find_test_cases(directory)

        self.nodes = {
            node_id: Node(x, y, str(node_id))
            for node_id, (x, y) in data.coords.items()
        }

        # Create exactly one graph, so the radio button remains attached.
        self.graph = Graph.fit(
            self.nodes.values(),
            f"{type(self.searcher).__name__} ({file_path})"
        )

        self.graph.add_radio_button(
            self.graph.algorithm_axes,
            "Search Algorithm",
            list(ALGORITHM_OPTIONS.keys()),
            self.on_select_algorithm
        )
        
        test_case_names = [path.name for path in self.test_cases]

        self.graph.add_radio_button(
            self.graph.test_case_axes,
            "Test Case",
            test_case_names,
            self.on_select_test_case,
            active=test_case_names.index(Path(self.file_path).name)
        )        

        self.draw_graph()


    def on_select_algorithm(self, option):
        # Create a new instance of the selected algorithm.
        self.searcher = ALGORITHM_OPTIONS[option]()

        # Rerun the search and update the visualization.
        self.draw_graph()
        

    def on_select_test_case(self, option):
        path = next(
            path for path in self.test_cases
            if path.name == option
        )

        self.data = load_test_file(str(path))
        self.file_path = str(path)

        self.nodes = {
            node_id: Node(x, y, str(node_id))
            for node_id, (x, y) in self.data.coords.items()
        }

        self.draw_graph()        


    def draw_graph(self):
        graph = self.graph
        data = self.data
        nodes = self.nodes

        # Remove the previous drawing before rendering the new result.
        graph.axes.clear()

        result = self.searcher.search(RouteProblem(data))

        graph.axes.set_title(
            f"{type(self.searcher).__name__} ({self.file_path})"
        )
        graph.axes.set_xlabel("X")
        graph.axes.set_ylabel("Y")
        graph.axes.set_xlim(0, max(node.x for node in nodes.values()) + 2)
        graph.axes.set_ylim(0, max(node.y for node in nodes.values()) + 2)
        graph.axes.set_xticks(range(0, int(max(n.x for n in nodes.values())) + 3))
        graph.axes.set_yticks(range(0, int(max(n.y for n in nodes.values())) + 3))
        graph.axes.spines["left"].set_position("zero")
        graph.axes.spines["bottom"].set_position("zero")
        graph.axes.spines["top"].set_visible(False)
        graph.axes.spines["right"].set_visible(False)
        graph.axes.grid(True)
        graph.axes.set_aspect("equal", adjustable="box")

        # Draw nodes.
        for node_id, node in nodes.items():
            graph.draw_node(node, color=node_colour(node_id, data))

        # Draw directed edges and their costs.
        for first, second, cost in data.edges:
            graph.draw_arrow(
                nodes[first],
                nodes[second],
                label=f"{cost:g}",
                color="lightgrey"
            )

        # Draw the solution path.
        if result.found:
            graph.draw_path([nodes[node_id] for node_id in result.path])

        # Draw the search result information.
        info = [
            f"Origin: {data.origin}",
            f"Destinations: {', '.join(map(str, data.destinations))}",
            ""
        ]

        if result.found:
            info += [
                "Status: path found",
                f"Reached: {result.path[-1]}",
                f"Path: {' -> '.join(map(str, result.path))}",
                f"Cost: {result.cost:g}",
                f"Steps: {result.steps}"
            ]
        else:
            info += ["Status: no path found"]

        info += [
            "",
            f"Expanded: {result.expanded_nodes}",
            f"Generated: {result.generated_nodes}"
        ]

        graph.draw_info(info)

        legend = [
            ("Origin", "green"),
            ("Destination", "red"),
            ("Other node", "black")
        ]

        if result.found:
            legend.append(("Solution path", "crimson"))

        graph.draw_legend(legend)

        # Refresh the existing figure.
        graph.figure.canvas.draw_idle()

        print(f"\nAlgorithm: {type(self.searcher).__name__}")

        if result.found:
            print("Path:", " -> ".join(map(str, result.path)))
            print(
                f"Reached destination {result.path[-1]} | "
                f"cost {result.cost:g} | "
                f"expanded {result.expanded_nodes} | "
                f"generated {result.generated_nodes}"
            )
        else:
            print("No path found")
            

class RouteProblem(SearchProblem[int]):
    """Directed graph of node ids; reaching ANY destination counts as the goal."""

    def __init__(self, data: PathFinderData):
        self.adjacency = data.adjacency()
        self.coords = data.coords
        self.origin = data.origin
        self.destinations = set(data.destinations)

    def initial_state(self): return self.origin
    def is_goal(self, state): return state in self.destinations
    def successors(self, state): return self.adjacency.get(state, [])

    def heuristic(self, state):
        """Straight-line distance to the nearest destination."""
        x, y = self.coords[state]
        return min(
            math.hypot(x - self.coords[goal][0], y - self.coords[goal][1])
            for goal in self.destinations
        )


def node_colour(node_id, data: PathFinderData) -> str:
    if node_id == data.origin:
        return "green"
    if node_id in data.destinations:
        return "red"
    return "black"

def on_select_algorithm(self, option):
    match option:
        case "A* Search":
            self.searcher = AStarSearch()
            
        case "Greedy-Best-First Search":
            self.searcher = GreedyBestFirstSearch()

        case "Breadth-First Search":
            self.searcher = BreadthFirstSearch()

        case "Depth-First Search":
            self.searcher = DepthFirstSearch()

        case "Hill Climbing Search":
            self.searcher = HillClimbingSearch()

        case "Uniform Cost Search":
            self.searcher = UniformCostSearch()

        case _:
            raise ValueError(f"Unknown search algorithm: {option}")


def main():
    file_path = (
        sys.argv[1] if len(sys.argv) > 1
        else "PathFinder-test-2.txt"
    )

    algorithm_key = sys.argv[2] if len(sys.argv) > 2 else "hill"

    # Resolve the command-line key to its display label.
    algorithm_labels = {
        "ucs": "Uniform Cost Search",
        "hill": "Hill Climbing Search",
        "dfs": "Depth-First Search",
        "gbfs": "Greedy-Best-First Search",
        "bfs": "Breadth-First Search",
        "as": "A* Search"
    }

    if algorithm_key not in algorithm_labels:
        sys.exit(
            f"Unknown algorithm '{algorithm_key}'. "
            f"Choose from: {', '.join(algorithm_labels)}"
        )

    data = load_test_file(file_path)

    app = RouteFinder(data, file_path, algorithm_labels[algorithm_key])
    app.graph.render()


if __name__ == "__main__":
    main()