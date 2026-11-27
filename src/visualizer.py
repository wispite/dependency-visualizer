
import shutil
import subprocess
import webbrowser
from pathlib import Path


def generate_graphviz(
        graph,
        cycles=None,
        output_name="dependency-graph",
        open_browser=False
):
    if cycles is None:
        cycles = []

    cycle_nodes = set()

    for cycle in cycles:
        for package in cycle:
            cycle_nodes.add(package)

    lines = [
        "digraph DependencyGraph {",
        '    graph [rankdir="LR", nodesep=0.35, ranksep=0.8];',
        '    node [shape=box, style="rounded,filled", '
        'fillcolor=lightblue, fontname="Arial", fontsize=10];',
        '    edge [color=gray50, arrowsize=0.7];',
        ""
    ]

    for package in graph:
        escaped_package = package.replace("\\", "\\\\").replace('"', '\\"')

        if package in cycle_nodes:
            lines.append(
                f'    "{escaped_package}" [fillcolor=lightcoral];'
            )
        else:
            lines.append(f'    "{escaped_package}";')

    lines.append("")

    for package, dependencies in graph.items():
        source = package.replace("\\", "\\\\").replace('"', '\\"')

        for dependency in dependencies:
            target = dependency.replace("\\", "\\\\").replace('"', '\\"')

            lines.append(f'    "{source}" -> "{target}";')

    lines.append("}")

    dot_description = "\n".join(lines)

    project_dir = Path(__file__).resolve().parent.parent
    output_dir = project_dir / "visualizations"
    output_dir.mkdir(exist_ok=True)

    dot_path = output_dir / f"{output_name}.dot"
    svg_path = output_dir / f"{output_name}.svg"


    dot_path.write_text(dot_description, encoding="utf-8")

    print(f"\nDOT file saved: {dot_path}")

    dot_executable = shutil.which("dot")

    if dot_executable is None:
        print("Graphviz is not installed or not found in PATH.")
        return dot_description

    # Генерация SVG
    subprocess.run(
        [
            dot_executable,
            "-Tsvg",
            str(dot_path),
            "-o",
            str(svg_path)
        ],
        check=True
    )

    print(f"SVG visualization saved: {svg_path}")
    if open_browser:
        webbrowser.open(svg_path.resolve().as_uri())
        print("Visualization opened in browser.")

    return dot_description
