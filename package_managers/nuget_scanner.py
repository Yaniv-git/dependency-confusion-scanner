from io import StringIO
import requests
import xml.etree.ElementTree as ET


class NugetScanner(object):

    @staticmethod
    def _package_exists(package_id: str) -> bool:
        response = requests.get(f"https://api.nuget.org/v3/registration5-semver1/{package_id.lower()}/index.json", timeout=10)
        if response.status_code == 404:
            return False
        return True

    @staticmethod
    def parse_item_group(item_group: ET.ElementTree) -> dict:
        packages = {}
        for package_reference in item_group.iter("PackageReference"):
            package_id = package_reference.get("Include")
            version = package_reference.get("Version")
            if (package_id is None) or (version is None):
                # Sometimes version is specified though a child node
                for child in package_reference:
                    if child.tag == "Version":
                        version = child.text
                    if child.tag == "Include":
                        package_id = child.text
                if (package_id is None) or (version is None):
                    continue
            packages[package_id] = version
        return packages

    @staticmethod
    def _parse_package(package: ET.ElementTree) -> (str, str):
        package_id = package.get("id")
        version = package.get("version")
        if (package_id is None) or (version is None):
            # Sometimes version is specified though a child node
            for child in package:
                if child.tag == "Version":
                    version = child.tag
                    return package_id, version
            return None
        return package_id, version

    @staticmethod
    def _parse_file(file_name: str, content: bytes) -> dict:
        result = {}
        try:
            root = ET.fromstring(StringIO(content.decode('utf-8')))
        except Exception as e:
            print(f"Error parsing {file_name}")
            return result
        if file_name == "packages.config":
            if root.tag != "packages":
                return result
            for package in root.iter("package"):
                package_id, version = NugetScanner._parse_package(package)
                result[package_id] = version
            return result
        else:
            if root.tag != "Project":
                return result
            for item_group in root.iter("ItemGroup"):
                result = NugetScanner.parse_item_froup(item_group)
            return result

    @staticmethod
    def scan_for_confusion(file_name: str, content: bytes) -> dict:
        results = {}
        dependencies = NugetScanner._parse_file(file_name, content)
        for package_id, version in dependencies.items():
            if not NugetScanner._package_exists(package_id):
                results[package_id] = version
        return results
