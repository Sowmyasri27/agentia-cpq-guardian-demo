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

## 4. Copado Agentia
The `agentia-plugin/` folder is an integration starter, not a claim that a plugin is already installed or verified. Install the current Agentia CLI using Copado's official instructions, scaffold a plugin with the official generator, and port the validator command into that generated plugin. Verify the CLI command in your authenticated Agentia environment before describing it as a working Agentia integration. See `docs/AGENTIA_INTEGRATION.md`.

## Security / limitations
- Salesforce integration is read-only; no records or metadata are modified.
- Only standard Product2 fields are queried by default.
- This does not directly read Industries CPQ/EPC catalog relationships until mapped to the actual org schema.
- No credentials, customer records, or org snapshots should be committed to a public repository.
