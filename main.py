from organization_scanner import OrganizationScanner

if __name__ == "__main__":
    scanner = OrganizationScanner()
    #scanner.scan_repo("ndleah/python-mini-project")
    scanner.scan_all_repos()