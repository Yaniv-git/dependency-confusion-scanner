import json
import requests


class PackagistScanner(object):

    @staticmethod
    def _package_exists(package_name: str) -> bool:
        try:
            response = requests.get(f"https://repo.packagist.org/p2/{package_name}.json", timeout=10)
        except Exception as e:
            raise Exception(f"npm request timeout to https://registry.npmjs.org/{package_name}/latest")
        if response.status_code == 200:
            response_json = response.json()
            if "999" in response_json['packages'][package_name][0]['version'] or "9.9.9" in \
                    response_json['packages'][package_name][0]['version']:
                print(f"*** Potential exploited confusion in ---> {package_name} ***")
        return response.status_code == 200

    @staticmethod
    def _parse_file(file_name: str, content: bytes) -> dict:  # exclude ext-* and php dep?
        results = {}
        try:
            content = content.decode("utf-8")
            file_json = json.loads(content)
        except Exception as e:
            raise Exception("Error parsing package.json - ", e)

        if "require" in file_json.keys() and "lock" not in file_name:  # package.json
            results["dependencies"] = file_json["require"]
        if "require-dev" in file_json:
            results["dev_dependencies"] = file_json["require-dev"]
        if "packages" in file_json and "lock" in file_name:  # package-lock.json
            dependencies = file_json["packages"]
            if "require" in dependencies:  # package.json
                results["composer-lock_requires"] = dependencies["require"]
        return results

    @staticmethod
    def scan_for_confusion(file_name: str, content: bytes) -> dict:
        results = {}
        dependencies = PackagistScanner._parse_file(file_name, content)
        for dependencies_types, dependencies_list in dependencies.items():
            for dependency_name, dependency_version in dependencies_list.items():
                if dependency_name != "php" and not dependency_name.startswith("ext-") and not PackagistScanner._package_exists(dependency_name):
                    results[dependency_name] = dependency_version
        return results
