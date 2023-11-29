import json
import requests


class NpmScanner(object):

    @staticmethod
    def _package_exists(package_name: str) -> bool:
        try:
            response = requests.get(f"https://registry.npmjs.org/{package_name}/latest", timeout=10)
        except Exception as e:
            raise Exception(f"npm request timeout to https://registry.npmjs.org/{package_name}/latest")
        if response.status_code == 404:
            if "version not found" in response.text:
                pass
            elif "Not Found" in response.text:
                return False
            else:
                print(response.text, f" for https://registry.npmjs.org/{package_name}/latest")
        elif response.status_code == 200:
            response_json = response.json()
            if "999" in response_json['version'] or "9.9.9" in response_json['version']:
                print(f"*** Potential exploited confusion in ---> {package_name} ***")
        return True
        '''elif req.status_code == 200:
            # Package found
            depStr = req.text
            if noTransitive:
                continue
            parsedDependencies = getPckgDependencies(depStr)
            for dep in parsedDependencies:
                # Do not put already processed packages back in queue
                if dep not in lstVisitedDep:
                    # print(f"Adding {dep}")
                    queueDep.append(dep)
                    lstVisitedDep[dep] = True
                    resultObj["recursiveDependencies"].append(dep)'''

    @staticmethod
    def _parse_file(file_name: str, content: bytes) -> dict:
        results = {}
        try:
            content = content.decode("utf-8")
            file_json = json.loads(content)
        except Exception as e:
            print("Error parsing package.json - ", e)
            return results

        if "dependencies" in file_json.keys() and "lock" not in file_name:  # package.json
            results["dependencies"] = file_json["dependencies"]
        if "devDependencies" in file_json:
            results["dev_dependencies"] = file_json["devDependencies"]
        if "dependencies" in file_json and "lock" in file_name:  # package-lock.json
            dependencies = file_json["dependencies"]
            for dependency_name, dependency_data in dependencies.items():
                if "requires" in dependency_data.keys():
                    results["package-lock_requires"] = dependency_data["requires"]
        return results

    @staticmethod
    def scan_for_confusion(file_name: str, content: bytes) -> dict:
        results = {}
        dependencies = NpmScanner._parse_file(file_name, content)
        for dependencies_types, dependencies_list in dependencies.items():
            for dependency_name, dependency_version in dependencies_list.items():
                if not NpmScanner._package_exists(dependency_name):
                    results[dependency_name] = dependency_version
        return results
