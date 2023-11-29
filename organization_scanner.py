import base64
import requests
from package_managers.npm_scanner import NpmScanner
from package_managers.pypi_scanner import PypiScanner
from package_managers.packagist_scanner import PackagistScanner
from package_managers.maven_scanner import MavenScanner
from package_managers.nuget_scanner import NugetScanner

class OrganizationScanner(object):
    MANIFEST_FILES = {"*.csproj": NugetScanner,
                      "packages.config": NugetScanner,
                      "build.gradle": MavenScanner,
                      "build.gradle.kts": MavenScanner,
                      "*pom.xml": MavenScanner,
                      "composer.lock": PackagistScanner,
                      "composer.json": PackagistScanner,
                      "requirements.txt": PypiScanner,
                      "package-lock.json": NpmScanner,
                      "package.json": NpmScanner}

    def __init__(self, organization_name="", exclude_repos=[]) -> None:
        self.exclude_repos = exclude_repos
        self.organization_name = organization_name
        self.access_token = open('./github_access_token', 'r').read()
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        self.file_trees = {}
        self.scanners = [NpmScanner]

    def scan_all_repos(self) -> None:
        for repository in self._get_organization_repositories():
            self.scan_repo(repository['full_name'])

    def scan_repo(self, repository_name: str) -> None:
        print(f"scanning {repository_name}")
        for manifest_file_name in self.MANIFEST_FILES.keys():
            for manifest_file_path in self._get_file_paths(repository_name, manifest_file_name):
                print(f"    scanning {manifest_file_name}")
                results = self.MANIFEST_FILES[manifest_file_name].scan_for_confusion(manifest_file_name,
                                                                                     self._get_file_content(
                                                                                         repository_name,
                                                                                         manifest_file_path))
                if results:
                    print(f"""
                    ***************************************************************
                    packages that are being used in {repository_name} (file path: {manifest_file_path}) but doesn't 
                    exist in the relevant package manager: {results}
                    ***************************************************************
                    """)

    def _get_organization_repositories(self) -> dict:
        page = 1
        while True:
            url = f"https://api.github.com/orgs/{self.organization_name}/repos?per_page=100&page={page}&type=private"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                repositories = response.json()
                if not repositories:
                    break
                for repository in repositories:
                    if repository['full_name'] not in self.exclude_repos:
                        yield repository
            else:
                raise Exception(
                    f"Failed to fetch repositories. Status code: {response.status_code}, Response: {response.text}")
            page += 1

    def _get_default_repo_branch(self, repository_name: str) -> str:
        url = f"https://api.github.com/repos/{repository_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response_json = response.json()
            return response_json['default_branch']
        else:
            raise Exception(
                f"Failed to fetch repository details. Status code: {response.status_code}, Response: {response.text}")

    def _get_repository_file_tree(self, repository_name: str) -> None:
        default_branch = self._get_default_repo_branch(repository_name)
        url = f"https://api.github.com/repos/{repository_name}/git/trees/{default_branch}?recursive=1"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            tree = response.json()
            self.file_trees[repository_name] = tree['tree']
        else:
            raise Exception(
                f"Failed to fetch repositories. Status code: {response.status_code}, Response: {response.text}")

    def _get_file_paths(self, repository_name: str, file_name: str) -> str:
        if not self.file_trees.get(repository_name, False):
            self._get_repository_file_tree(repository_name)
        if file_name[0] != "*":
            file_name = "/" + file_name
        for file in self.file_trees[repository_name]:
            if file['path'].endswith(file_name) or file['path'] == file_name:
                yield file['path']

    def _get_file_content(self, repository_name: str, file_path: str) -> bytes:
        url = f"https://api.github.com/repos/{repository_name}/contents/{file_path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            res_json = response.json()
            return base64.b64decode(res_json['content'])
        else:
            raise Exception(
                f"Failed to fetch repositories. Status code: {response.status_code}, Response: {response.text}")
