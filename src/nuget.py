import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from functools import cmp_to_key
from urllib.parse import quote


def download_text(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "DependencyVisualizer/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def get_package_base_address(repository_url):
    service_index = json.loads(download_text(repository_url))

    for resource in service_index.get("resources", []):
        resource_type = resource.get("@type", "")

        if resource_type.startswith("PackageBaseAddress/3.0.0"):
            return resource["@id"]

    raise ValueError(
        "NuGet repository does not provide PackageBaseAddress"
    )


def get_package_versions(base_address, package_id):
    package_name = quote(package_id.lower(), safe=".-")

    url = (
        f"{base_address.rstrip('/')}/"
        f"{package_name}/index.json"
    )

    data = json.loads(download_text(url))
    return data.get("versions", [])


def parse_version(version):
    version = version.split("+", 1)[0].lower()

    match = re.fullmatch(
        r"(\d+(?:\.\d+){0,3})(?:-([0-9a-z.-]+))?",
        version
    )

    if not match:
        raise ValueError(f"Unsupported NuGet version: {version}")

    numbers = tuple(
        int(part) for part in match.group(1).split(".")
    )

    numbers = numbers + (0,) * (4 - len(numbers))

    prerelease = match.group(2)

    if prerelease is not None:
        prerelease = prerelease.split(".")

    return numbers, prerelease


def compare_versions(first, second):
    first_numbers, first_pre = parse_version(first)
    second_numbers, second_pre = parse_version(second)

    if first_numbers != second_numbers:
        return (first_numbers > second_numbers) - (
            first_numbers < second_numbers
        )

    if first_pre is None and second_pre is None:
        return 0

    if first_pre is None:
        return 1

    if second_pre is None:
        return -1

    for first_part, second_part in zip(first_pre, second_pre):
        if first_part == second_part:
            continue

        first_numeric = first_part.isdigit()
        second_numeric = second_part.isdigit()

        if first_numeric and second_numeric:
            return (int(first_part) > int(second_part)) - (
                int(first_part) < int(second_part)
            )

        if first_numeric:
            return -1

        if second_numeric:
            return 1

        return (first_part > second_part) - (
            first_part < second_part
        )

    return (len(first_pre) > len(second_pre)) - (
        len(first_pre) < len(second_pre)
    )


def version_satisfies(version, version_range):
    version_range = version_range.strip()

    if not version_range or version_range == "Not specified":
        return True

    if version_range.startswith(("[", "(")):
        if not version_range.endswith(("]", ")")):
            raise ValueError(
                f"Invalid NuGet version range: {version_range}"
            )

        content = version_range[1:-1]

        if "," not in content:
            if version_range[0] != "[" or version_range[-1] != "]":
                return False

            return compare_versions(version, content.strip()) == 0

        lower, upper = content.split(",", 1)

        if lower.strip():
            result = compare_versions(version, lower.strip())

            if result < 0 or (
                result == 0 and version_range[0] == "("
            ):
                return False

        if upper.strip():
            result = compare_versions(version, upper.strip())

            if result > 0 or (
                result == 0 and version_range[-1] == ")"
            ):
                return False

        return True

    return compare_versions(version, version_range) >= 0


def resolve_dependency_version(
    base_address,
    package_id,
    version_range
):
    versions = get_package_versions(base_address, package_id)

    if not versions:
        raise ValueError(
            f"No published versions found for package {package_id}"
        )

    allow_prerelease = (
        "-" in version_range
        and version_range != "Not specified"
    )

    candidates = []

    for version in versions:
        try:
            if not allow_prerelease and "-" in version:
                continue

            if version_satisfies(version, version_range):
                candidates.append(version)

        except ValueError:
            continue

    if not candidates:
        raise ValueError(
            f"No version of {package_id} satisfies "
            f"the range {version_range}"
        )

    candidates.sort(key=cmp_to_key(compare_versions))

    return candidates[0]


def get_direct_dependencies(repository_url, package_id, version):
    base_address = get_package_base_address(repository_url)

    package_name = quote(package_id.lower(), safe=".-")
    package_version = quote(
        version.split("+", 1)[0].lower(),
        safe=".-"
    )

    nuspec_url = (
        f"{base_address.rstrip('/')}/"
        f"{package_name}/{package_version}/"
        f"{package_name}.nuspec"
    )

    nuspec_content = download_text(nuspec_url)
    root = ET.fromstring(nuspec_content)

    def find_child(element, name):
        for child in element:
            if child.tag.split("}")[-1] == name:
                return child
        return None

    metadata = find_child(root, "metadata")

    if metadata is None:
        raise ValueError(
            "Invalid NuGet package manifest: metadata not found"
        )

    dependencies_element = find_child(metadata, "dependencies")

    if dependencies_element is None:
        return []

    dependencies = []

    for element in dependencies_element:
        tag_name = element.tag.split("}")[-1]

        if tag_name == "dependency":
            dependency_id = element.get("id")
            dependency_version = element.get(
                "version", "Not specified"
            )

            if dependency_id:
                dependencies.append({
                    "id": dependency_id,
                    "version": dependency_version,
                    "framework": "All"
                })

        elif tag_name == "group":
            framework = element.get("targetFramework", "All")

            for dependency in element:
                if dependency.tag.split("}")[-1] != "dependency":
                    continue

                dependency_id = dependency.get("id")
                dependency_version = dependency.get(
                    "version", "Not specified"
                )

                if dependency_id:
                    dependencies.append({
                        "id": dependency_id,
                        "version": dependency_version,
                        "framework": framework
                    })

    return dependencies
