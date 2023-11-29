from organization_scanner import OrganizationScanner

if __name__ == "__main__":
    scanner = OrganizationScanner("SonarSource", exclude_repos=["SonarSource/security-expected-issues","SonarSource/gh-security-experiment-1","SonarSource/gh-security-experiment-2","SonarSource/gh-security-experiment-3","SonarSource/gh-security-experiment-4","SonarSource/gh-security-experiment-5"])
    #scanner.scan_repo("ndleah/python-mini-project")
    scanner.scan_all_repos()