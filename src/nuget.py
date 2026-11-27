import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
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

    raise ValueError("NuGet repository does not provide PackageBaseAddress")


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
        raise ValueError("Invalid NuGet package manifest: metadata not found")

    dependencies_element = find_child(metadata, "dependencies")

    if dependencies_element is None:
        return []

    dependencies = []

    for element in dependencies_element:
        tag_name = element.tag.split("}")[-1]

        if tag_name == "dependency":
            dependency_id = element.get("id")
            dependency_version = element.get("version", "Not specified")

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
                    "version",
                    "Not specified"
                )

                if dependency_id:
                    dependencies.append({
                        "id": dependency_id,
                        "version": dependency_version,
                        "framework": framework
                    })

    return dependencies
