import json
import requests
from file_parser.pip_parser import parse, filetypes


class PypiScanner(object):

    @staticmethod
    def _package_exists(package_name: str) -> bool:
        try:
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
        except Exception as e:
            raise Exception(f"npm request timeout to https://registry.npmjs.org/{package_name}/latest")
        if response.status_code == 200:
            response_json = response.json()
            if "999" in response_json['info']['version'] or "9.9.9" in response_json['info']['version']:
                print(f"*** Potential exploited confusion in ---> {package_name} ***")
        return response.status_code == 200

    @staticmethod
    def _parse_file(content: bytes) -> list:
        dependencies = []
        content = content.decode("utf-8")
        parsed_content = parse(content, file_type=filetypes.requirements_txt)
        for dependency in parsed_content.dependencies:
            dependencies.append(dependency.name)
        return dependencies

    @staticmethod
    def scan_for_confusion(file_name: str, content: bytes) -> list:
        results = []
        dependencies = PypiScanner._parse_file(content)
        for dependency_name in dependencies:
            if not PypiScanner._package_exists(dependency_name):
                results.append(dependency_name)
        return results
