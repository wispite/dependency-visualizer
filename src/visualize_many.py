from main import build_remote_graph
from pathlib import Path
import subprocess


REPOSITORY_URL = "https://api.nuget.org/v3/index.json"

PACKAGES = [
    ("Newtonsoft.Json", "13.0.3"),
    ("Serilog", "4.2.0"),
    ("Microsoft.Extensions.Logging", "8.0.1"),
    ("Microsoft.EntityFrameworkCore", "8.0.11"),
    ("Swashbuckle.AspNetCore", "6.6.2"),
    ("AutoMapper", "13.0.1"),
    ("Polly", "8.5.0"),
    ("FluentValidation", "11.11.0"),
    ("Dapper", "2.1.35"),
    ("NLog", "5.3.4"),
]


def escape_label(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def main():
    lines = [
        "digraph AllPackageDependencies {",
        '    graph [rankdir="LR", compound=true, overlap=false, '
        'splines=true, nodesep=0.25, ranksep=0.7];',
        '    node [shape=box, style="rounded,filled", '
        'fillcolor=lightblue, fontname="Arial", fontsize=9];',
        '    edge [color=gray50, arrowsize=0.6];',
        ""
    ]

    successful = 0

    for index, (package, version) in enumerate(PACKAGES):
        print(f"\n[{index + 1}/{len(PACKAGES)}] Загружаем {package} {version}...")

        try:
            graph, cycles, resolved_versions = build_remote_graph(
                REPOSITORY_URL,
                package,
                version
            )

            prefix = f"p{index}_"

            lines.append(f"    subgraph cluster_{index} {{")
            lines.append('        style="rounded";')
            lines.append('        color=gray60;')
            lines.append(
                f'        label="{escape_label(package)} {version}";'
            )

            for node in graph:
                node_id = prefix + node.lower()
                label = escape_label(node)

                if node.lower() == package.lower():
                    lines.append(
                        f'        "{node_id}" [label="{label}", '
                        'fillcolor=gold];'
                    )
                else:
                    lines.append(
                        f'        "{node_id}" [label="{label}"];'
                    )

            for node, dependencies in graph.items():
                source = prefix + node.lower()

                for dependency in dependencies:
                    target = prefix + dependency.lower()
                    lines.append(f'        "{source}" -> "{target}";')

            lines.append("    }")
            lines.append("")

            successful += 1
            print(
                f"Готово: {len(graph)} узлов, "
                f"{sum(len(v) for v in graph.values())} связей"
            )

        except Exception as error:
            print(f"Не удалось обработать {package}: {error}")

    lines.append("}")

    if successful == 0:
        print("\nНе удалось построить ни одного графа.")
        return

    output_dir = Path("visualizations")
    output_dir.mkdir(exist_ok=True)

    dot_path = output_dir / "all-packages.dot"
    svg_path = output_dir / "all-packages.svg"

    dot_path.write_text("\n".join(lines), encoding="utf-8")

    subprocess.run(
        ["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)],
        check=True
    )

    print("\n===================================")
    print(f"Успешно обработано пакетов: {successful}")
    print(f"DOT-файл: {dot_path}")
    print(f"Общий холст: {svg_path}")
    print("===================================")


if __name__ == "__main__":
    main()
