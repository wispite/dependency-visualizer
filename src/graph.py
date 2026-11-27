
import json
import re
from pathlib import Path


def load_test_repository(file_path):
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        repository = json.load(file)

    if not isinstance(repository, dict):
        raise ValueError("Test repository must contain a JSON object")

    for package, dependencies in repository.items():
        if not isinstance(package, str) or not re.fullmatch(
            r"[A-Z]+", package
        ):
            raise ValueError(
                f"Invalid package name: {package}. "
                "Use uppercase Latin letters."
            )

        if not isinstance(dependencies, list):
            raise ValueError(
                f"Dependencies of package {package} must be a list"
            )

        for dependency in dependencies:
            if not isinstance(dependency, str) or not re.fullmatch(
                r"[A-Z]+", dependency
            ):
                raise ValueError(
                    f"Invalid dependency name in package {package}"
                )

    for package, dependencies in repository.items():
        for dependency in dependencies:
            if dependency not in repository:
                raise ValueError(
                    f"Package {dependency} is referenced by {package}, "
                    "but is not described in the repository"
                )

    return repository


def build_dependency_graph(root_package, get_dependencies):

    graph = {}
    visited = set()
    active = set()
    cycles = []

    visited.add(root_package)
    active.add(root_package)
    graph[root_package] = []

    stack = [
        (root_package, iter(get_dependencies(root_package)))
    ]

    while stack:
        current_package, dependencies_iterator = stack[-1]

        try:
            dependency = next(dependencies_iterator)

        except StopIteration:
            active.remove(current_package)
            stack.pop()
            continue

        graph[current_package].append(dependency)

        if dependency in active:
            current_path = [
                package for package, _ in stack
            ]

            cycle_start = current_path.index(dependency)
            cycle = current_path[cycle_start:] + [dependency]

            cycles.append(cycle)
            continue

        if dependency not in visited:
            visited.add(dependency)
            active.add(dependency)

            graph[dependency] = []

            stack.append(
                (dependency, iter(get_dependencies(dependency)))
            )

    return graph, cycles


def build_reverse_graph(repository):

    reverse_graph = {
        package: [] for package in repository
    }

    for package, dependencies in repository.items():
        for dependency in dependencies:
            reverse_graph[dependency].append(package)

    return reverse_graph


def find_reverse_dependencies(root_package, reverse_graph):

    graph, cycles = build_dependency_graph(
        root_package,
        lambda package: reverse_graph[package]
    )

    reverse_dependencies = []

    for package in graph:
        if package != root_package:
            reverse_dependencies.append(package)

    return reverse_dependencies, cycles
