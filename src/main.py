import argparse
import re
from pathlib import Path
from urllib.parse import urlparse


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

    # Check package version
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


def main():
    try:
        args = parse_arguments()
        validate_arguments(args)

        print("\n=== Dependency Visualizer ===\n")
        print(f"Package:     {args.package}")
        print(f"Repository:  {args.repository}")
        print(f"Mode:        {args.mode}")
        print(f"Version:     {args.version}")
        print("\nConfiguration loaded successfully!")

    except ValueError as error:
        print(f"\nError: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
