
import argparse
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

from nuget import get_direct_dependencies


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Dependency Visualizer - package dependency analyzer"
    )

    parser.add_argument(
        "--package",
        required=True,
        help="Name of the package"
    )

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

    parser.add_argument(
        "--version",
        required=True,
        help="Package version"
    )

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


def print_dependencies(dependencies):
    print("\n=== Direct Dependencies ===\n")

    if not dependencies:
        print("The package has no direct dependencies.")
        return

    for index, dependency in enumerate(dependencies, start=1):
        print(f"{index}. {dependency['id']}")
        print(f"   Version:   {dependency['version']}")
        print(f"   Framework: {dependency['framework']}")


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
            raise ValueError(
                "Test mode dependency retrieval will be implemented "
                "in a later stage."
            )

        print("\nConfiguration loaded successfully!")

        print("\nDownloading package dependencies...")

        dependencies = get_direct_dependencies(
            args.repository,
            args.package,
            args.version
        )

        print_dependencies(dependencies)

        print("\nDependency retrieval completed successfully!")

    except (ValueError, URLError, TimeoutError, OSError,
            ET.ParseError) as error:
        print(f"\nError: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
