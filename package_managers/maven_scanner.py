import re
from io import StringIO
import requests
import xml.etree.ElementTree as ET


class MavenScanner(object):

    # Remove xml namespace from tree
    # (only causes problems for this purpose)+
    @staticmethod
    def remove_namespace(doc: str) -> ET.ElementTree:
        it = ET.iterparse(StringIO(doc))
        for _, el in it:
            prefix, has_namespace, postfix = el.tag.partition('}')
            if has_namespace:
                el.tag = postfix  # strip all namespaces
        root = it.root
        return root

    @staticmethod
    def _package_exists(group_id: str, artifact_id: str, version=None) -> bool:
        if version:
            response = requests.get(f"https://repo1.maven.org/maven2/{group_id}/{artifact_id}/{version}/{artifact_id}-{version}.pom", timeout=10)
        else:
            response = requests.get(f"https://repo1.maven.org/maven2/{group_id}/{artifact_id}", timeout=10)
        if response.status_code == 404:
            return False
        return True


    @staticmethod
    def isNumericVersion(string: str) -> bool:
        search=re.compile(r'[^0-9.]').search
        return not bool(search(string))

    @staticmethod
    def _parse_gradle_file(content: str) -> list:
        result = []
        # Regular expression to match dependencies
        pattern = r"dependencies\s*{\s*([\s\S]*?)\s*}"
        # Find the dependencies block
        match = re.search(pattern, content)
        if match:
            # Extract the content inside the dependencies block
            dependencies_content = match.group(1)
            # Regular expression to match dependencies
            dependency_pattern = "[\'\"]([\w\-.]+:[\w\-.]+:[\w\-.\$]+)"
            # Find all dependencies in the content
            dependencies = re.findall(dependency_pattern, dependencies_content)
            for dependency in dependencies:
                version = dependency.split(":")[-1] if "$" not in dependency.split(":")[-1] else None
                result.append([dependency.split(":")[0].replace(".", "/"), dependency.split(":")[1], version])
            no_version_dependency_pattern = "[\'\"]([\w\-.]+:[\w\-.]+)"
            # Find all dependencies in the content
            no_version_dependencies = re.findall(no_version_dependency_pattern, dependencies_content)
            for dependency in no_version_dependencies:
                result.append(
                    [dependency.split(":")[0].replace(".", "/"), dependency.split(":")[1], None])
            return result
        else:
            print("No dependencies block found in the Gradle file.")
            return result

    @staticmethod
    def _parse_file(content: str) -> list:
        result = []
        properties_dict = {}
        root = MavenScanner.remove_namespace(content)
        if root.find("dependencyManagement") is not None:
            root = root.find("dependencyManagement")
        for property in root.iter("properties"):
            properties_dict[property.tag] = property.text
        for dependencies in root.iter("dependencies"):
            for dependency in dependencies.iter("dependency"):
                group_id = None
                artifact_id = None
                version = None
                for dependency_node in dependency:
                    if dependency_node.tag == "groupId":
                        if "$" in dependency_node.text or "{" in dependency_node.text:
                            property_key = re.findall(r'\$\{(.*?)\}', dependency_node.text)
                            if property_key and property_key[0] in properties_dict.keys():
                                group_id = properties_dict[property_key[0]]
                            else:
                                continue
                        else:
                            group_id = dependency_node.text
                    if dependency_node.tag == "artifactId":
                        if "$" in dependency_node.text or "{" in dependency_node.text:
                            property_key = re.findall(r'\$\{(.*?)\}', dependency_node.text)
                            if property_key and property_key[0] in properties_dict.keys():
                                artifact_id = properties_dict[property_key[0]]
                            else:
                                continue
                        else:
                            artifact_id = dependency_node.text
                    if dependency_node.tag == "version":
                        if "$" in dependency_node.text or "{" in dependency_node.text:
                            property_key = re.findall(r'\$\{(.*?)\}', dependency_node.text)
                            if property_key and property_key[0] in properties_dict.keys():
                                if MavenScanner.isNumericVersion(properties_dict[property_key[0]]):
                                    version = properties_dict[property_key[0]]
                            else:
                                continue
                        elif MavenScanner.isNumericVersion(dependency_node.text):
                            version = dependency_node.text

                if (group_id is None) or (artifact_id is None):
                    continue
                else:
                    # Replace . with / in groupId for
                    # Ex: com.google.android => com/google/android
                    if "." in group_id:
                        group_id = group_id.replace(".", "/")
                    result.append([group_id, artifact_id, version])
        return result

    @staticmethod
    def scan_for_confusion(file_name: str, content: bytes) -> dict:
        results = {}
        if "build.gradle" in file_name:
            dependencies = MavenScanner._parse_gradle_file(content.decode('utf-8'))
        else:
            dependencies = MavenScanner._parse_file(content.decode('utf-8'))
        for group_id, artifact_id, version in dependencies:
            if not MavenScanner._package_exists(group_id, artifact_id, version):
                results[group_id + "/" + artifact_id] = version
        return results

