import argparse
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import URLError
import xml.etree.ElementTree as ET

from nuget import (
    get_direct_dependencies,
    get_package_base_address,
    resolve_dependency_version
)
from graph import (
    load_test_repository,
    build_dependency_graph,
    build_reverse_graph,
    find_reverse_dependencies
)
from visualizer import generate_graphviz


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Dependency Visualizer - package dependency analyzer"
    )

    parser.add_argument("--package", required=True, help="Name of the package")
    parser.add_argument(
        "--repository",
        required=True,
        help="Repository URL or path to test repository file"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["remote", "test"],
        help="Working mode: remote or test"
    )
    parser.add_argument("--version", required=True, help="Package version")

    return parser.parse_args()


def validate_arguments(args):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.package):
        raise ValueError("Invalid package name")

    if not re.fullmatch(
            r"\d+(?:\.\d+)*(?:-[A-Za-z0-9.-]+)?(?:\+[A-Za-z0-9.-]+)?",
            args.version
    ):
        raise ValueError("Invalid package version")

    if args.mode == "remote":
        parsed_url = urlparse(args.repository)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            raise ValueError("Invalid repository URL")

    elif args.mode == "test":
        repository_path = Path(args.repository)

        if not repository_path.exists():
            raise ValueError("Test repository file does not exist")

        if not repository_path.is_file():
            raise ValueError("Test repository path must point to a file")

        if not re.fullmatch(r"[A-Z]+", args.package):
            raise ValueError(
                "Test mode package name must contain uppercase Latin letters"
            )


def print_dependencies(dependencies):
    print("\n=== Direct Dependencies ===\n")

    if not dependencies:
        print("The package has no direct dependencies.")
        return

    for index, dependency in enumerate(dependencies, start=1):
        print(f"{index}. {dependency['id']}")
        print(f"   Version:   {dependency['version']}")
        print(f"   Framework: {dependency['framework']}")


def print_graph(graph):
    print("\n=== Dependency Graph ===\n")

    for package, dependencies in graph.items():
        if dependencies:
            print(f"{package} -> {', '.join(dependencies)}")
        else:
            print(f"{package} -> (no dependencies)")


def print_cycles(cycles):
    print("\n=== Cycle Detection ===\n")

    if not cycles:
        print("No cycles detected.")
        return

    for index, cycle in enumerate(cycles, start=1):
        print(f"{index}. {' -> '.join(cycle)}")

def print_graphviz(graph, cycles):
    print("\n=== Graphviz DOT Description ===\n")

    dot_description = generate_graphviz(graph, cycles)

    print(dot_description)

def build_remote_graph(repository_url, root_package, root_version):
    base_address = get_package_base_address(repository_url)

    resolved_versions = {
        root_package.lower(): root_version
    }

    def get_dependencies(package):
        package_key = package.lower()
        package_version = resolved_versions[package_key]

        dependencies = get_direct_dependencies(
            repository_url,
            package,
            package_version
        )

        unique_dependencies = {}

        for dependency in dependencies:
            dependency_id = dependency["id"]
            dependency_key = dependency_id.lower()
            version_range = dependency["version"]

            if dependency_key not in resolved_versions:
                resolved_versions[dependency_key] = (
                    resolve_dependency_version(
                        base_address,
                        dependency_id,
                        version_range
                    )
                )

            if dependency_key not in unique_dependencies:
                unique_dependencies[dependency_key] = dependency_id

        return list(unique_dependencies.values())

    graph, cycles = build_dependency_graph(
        root_package,
        get_dependencies
    )

    return graph, cycles, resolved_versions


def main():
    try:
        args = parse_arguments()
        validate_arguments(args)

        print("\n=== Dependency Visualizer ===\n")
        print(f"Package:     {args.package}")
        print(f"Repository:  {args.repository}")
        print(f"Mode:        {args.mode}")
        print(f"Version:     {args.version}")

        if args.mode == "test":
            repository = load_test_repository(args.repository)

            if args.package not in repository:
                raise ValueError(
                    f"Package {args.package} not found in test repository"
                )

            print("\nBuilding dependency graph...")

            graph, cycles = build_dependency_graph(
                args.package,
                lambda package: repository[package]
            )

        else:
            print("\nDownloading dependencies and building graph...")
            print("This may take some time...\n")

            graph, cycles, resolved_versions = build_remote_graph(
                args.repository,
                args.package,
                args.version
            )

            print("=== Resolved Package Versions ===")

            for package, version in resolved_versions.items():
                print(f"{package}: {version}")

        print_graph(graph)
        print_cycles(cycles)
        print_graphviz(graph, cycles)

        if args.mode == "test":
            reverse_graph = build_reverse_graph(repository)

            reverse_dependencies, reverse_cycles = (
                find_reverse_dependencies(
                    args.package,
                    reverse_graph
                )
            )

            print("\n=== Reverse Dependencies ===\n")

            if reverse_dependencies:
                for index, package in enumerate(
                        reverse_dependencies, start=1
                ):
                    print(f"{index}. {package}")
            else:
                print("No reverse dependencies found.")

            if reverse_cycles:
                print("\nCycles in reverse graph:")

                for index, cycle in enumerate(
                        reverse_cycles, start=1
                ):
                    print(f"{index}. {' -> '.join(cycle)}")

        print("\nOperation completed successfully!")

    except (
            ValueError,
            URLError,
            TimeoutError,
            OSError,
            ET.ParseError
    ) as error:
        print(f"\nError: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
