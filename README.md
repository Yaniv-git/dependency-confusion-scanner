# Dependency confusion scanner
This small repo is meant to scan Github's repositories for potential [Dependency confusion](https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610) vulnerabilities. 

It scans for packages in:
* [Nuget](https://www.nuget.org/)
  * *.csproj
  * packages.config
* [Maven](https://mvnrepository.com/)
  * *pom.xml
  * build.gradle
* [Packagist](https://packagist.org/)
  * composer.lock
  * composer.json
* [Pypi](https://pypi.org/)
  * requirements.txt
* [NPM](https://www.npmjs.com/)
  * package-lock.json
  * package.json

## How it works

Simply fetches the relevant files for each package manager, parse it, and check if the package exists publicly. 
Additionally, it will warn if a detected public package includes `999` or `9.9.9` in the package version (for already exploited dependency confusion)

### setup
Create a `github_access_token` file and add you Github's api token to it (this way it could also have access to private repos).
### run
In order to run the script simply state an organization and scan all the repos in it (with option to `exclude_repos`)
```python
    scanner = OrganizationScanner("SonarSource")
    scanner.scan_all_repos()
```
Or scan a specific repo
```python
    scanner = OrganizationScanner()
    scanner.scan_repo("ndleah/python-mini-project")
```