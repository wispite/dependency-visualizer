
def generate_graphviz(graph, cycles=None):

    if cycles is None:
        cycles = []

    cycle_nodes = set()

    for cycle in cycles:
        for package in cycle:
            cycle_nodes.add(package)

    lines = [
        "digraph DependencyGraph {",
        '    rankdir="LR";',
        '    node [shape=box, style=filled, fillcolor=lightblue];',
        ""
    ]

    for package in graph:
        if package in cycle_nodes:
            lines.append(
                f'    "{package}" '
                '[fillcolor=lightcoral];'
            )
        else:
            lines.append(f'    "{package}";')

    lines.append("")

    for package, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(
                f'    "{package}" -> "{dependency}";'
            )

    lines.append("}")

    return "\n".join(lines)
