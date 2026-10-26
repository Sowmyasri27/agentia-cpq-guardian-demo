# Agentia CPQ Guardian — Salesforce-connected reference implementation

A read-only CPQ quality gate for Salesforce telecom product configurations. It validates required products, incompatible combinations, unknown codes, and inactive products, then writes a JSON findings report.

## What works in this repository
- Local deterministic validator with repeatable sample scenarios.
- Optional Salesforce connection through the **Salesforce CLI authenticated org session** (`sf org display --json`) and read-only REST query of `Product2`.
- Optional rule overlay (`requires` and `incompatible_with`) to encode domain rules not universally available on standard Product2 fields.
- Five automated unit tests.
- Agentia plugin scaffold/manifest notes are separate and must be built and verified in the user's Agentia environment before claiming an installed Agentia plugin.

## Requirements
- Python 3.10+
- For Salesforce mode: Salesforce CLI (`sf`) installed and authenticated to a sandbox/Developer Edition org.
- No password, token, or client secret should be pasted into source code or committed to Git.

## 1. Run sample scenarios
```bash
py src/guardian.py --catalog sample_data/catalog.json --change sample_data/change_request_invalid.json --output invalid-report.json
py src/guardian.py --catalog sample_data/catalog.json --change sample_data/change_request_valid.json --output valid-report.json
py -m unittest discover -s tests -v
```
The invalid case is expected to exit with code 1 because findings were detected; the valid case exits 0.

## 2. Authenticate Salesforce CLI
```bash
sf --version
sf org login web --alias cpq-dev --instance-url https://login.salesforce.com
# For a sandbox, use https://test.salesforce.com
sf org list
sf org display --target-org cpq-dev
```
Complete login in the browser. Never paste credentials into the terminal or commit CLI auth files.

## 3. Read Product2 from Salesforce (read-only)
```bash
py src/guardian.py --salesforce --target-org cpq-dev --change sample_data/change_request_invalid.json --rules sample_data/salesforce_rules_overlay.json --snapshot-output product-snapshot.json --output salesforce-report.json
```
The connector uses the authenticated CLI session and queries standard Product2 fields only. Your org must grant API access and read access to Product2. Product codes become validator IDs; ensure the change request uses matching ProductCode values. If ProductCode is blank, the Salesforce record ID is used.

**Important:** standard Product2 does not universally contain dependency or incompatibility rules. Provide those through a reviewed JSON overlay or adapt the connector to the actual Industries CPQ/EPC schema in your org. This repository does not assume one universal Vlocity schema, and it does not write to Salesforce.


## 4. Copado Agentia CLI plugin

This repository includes the source for a custom Agentia CLI plugin in `agentia-plugin/`. The plugin exposes the command `agentia cpq validate` and invokes the CPQ Guardian Python validator.

### Plugin capabilities
- Accepts a change-request JSON file.
- Validates against the local sample catalog or reads Product2 from Salesforce through an authenticated Salesforce CLI session.
- Supports an optional rules overlay for required and incompatible products.
- Prints the validator's JSON findings and returns a non-zero exit status when validation fails.
- Does not create or update Salesforce records.

### Build and link locally

Requirements: Node.js, npm, the Copado Agentia CLI, Python, and Salesforce CLI for Salesforce mode.

From the repository root, build the plugin:

```powershell
cd agentia-plugin
npm ci
npm.cmd run build
agentia plugins link .
cd ..
```

If `agentia` is not on your PATH in PowerShell, use the full path to your installed `agentia.cmd` executable.

### Example commands

Run these commands from the repository root after linking the plugin:

```powershell
agentia cpq validate --change sample_data/change_request_live_valid.json --salesforce --target-org GuardianDev
```

Validate a request containing an unknown product:

```powershell
agentia cpq validate --change sample_data/change_request_live_invalid.json --salesforce --target-org GuardianDev
```

Test a product incompatibility using the rules overlay:

```powershell
agentia cpq validate --change sample_data/change_request_live_conflict.json --salesforce --target-org GuardianDev --rules sample_data/salesforce_rules_overlay.json
```

The valid request should pass if the referenced products exist and are active in the connected org. Invalid requests are expected to return a non-zero exit status when findings are detected.

### Integration boundaries

The local plugin command has been built and exercised in a development environment. It invokes Python and Salesforce CLI on the local machine; it is not evidence that Copado-hosted Headless authentication, a hosted Agentia pipeline, or a production deployment has been configured. Users must build and link the plugin in their own supported Agentia environment.

The Salesforce connector queries standard `Product2` fields and is read-only. Product dependencies and incompatibilities are supplied through a rules overlay unless explicitly mapped to the target org's Industries CPQ/EPC schema. See `docs/AGENTIA_INTEGRATION.md`.
