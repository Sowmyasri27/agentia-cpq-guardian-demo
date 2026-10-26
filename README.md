# Agentia CPQ Guardian --- Salesforce-connected reference implementation

A read-only CPQ quality gate for Salesforce telecom product
configurations. It validates required products, incompatible
combinations, unknown product codes, and inactive products, then emits a
JSON findings report.

## What works in this repository

-   Local deterministic validator with repeatable sample scenarios.
-   Optional Salesforce connection through an authenticated Salesforce
    CLI session and read-only REST queries of `Product2`.
-   Optional rules overlay (`requires` and `incompatible_with`) for
    domain rules that are not universally available on standard
    `Product2` fields.
-   Five automated unit tests.
-   Custom Agentia CLI plugin source included in `agentia-plugin/`. It
    has been built and tested locally from a fresh GitHub clone.

## Requirements

-   Python 3.10 or newer.
-   Node.js 22.12 or newer and npm for the Agentia plugin.
-   Copado Agentia CLI for linking and running the plugin.
-   For Salesforce mode: Salesforce CLI (`sf`) installed and
    authenticated to a sandbox or Developer Edition org.
-   Never paste passwords, access tokens, or client secrets into source
    code or commit them to Git.

## 1. Run sample scenarios

From the repository root:

``` bash
py src/guardian.py --catalog sample_data/catalog.json --change sample_data/change_request_invalid.json --output invalid-report.json
py src/guardian.py --catalog sample_data/catalog.json --change sample_data/change_request_valid.json --output valid-report.json
py -m unittest discover -s tests -v
```

The invalid case is expected to exit with code `1` because findings were
detected. The valid case should exit with code `0`.

## 2. Authenticate Salesforce CLI

``` bash
sf --version
sf org login web --alias cpq-dev --instance-url https://login.salesforce.com
# For a sandbox, use https://test.salesforce.com
sf org list
sf org display --target-org cpq-dev
```

Complete login in the browser. Never paste credentials into the terminal
or commit CLI authentication files.

## 3. Read Product2 from Salesforce (read-only)

``` bash
py src/guardian.py --salesforce --target-org cpq-dev --change sample_data/change_request_invalid.json --rules sample_data/salesforce_rules_overlay.json --snapshot-output product-snapshot.json --output salesforce-report.json
```

The connector queries standard `Product2` fields only. Your org must
grant API access and read access to `Product2`. Product codes become
validator IDs, so change requests must use matching `ProductCode`
values. If `ProductCode` is blank, the Salesforce record ID is used.

**Important:** Standard `Product2` does not universally contain
dependency or incompatibility rules. Provide those through a reviewed
JSON overlay or adapt the connector to your org's actual Industries
CPQ/EPC schema. This repository does not assume a universal Vlocity
schema and does not write to Salesforce.

## 4. Copado Agentia CLI plugin

This repository includes the custom Agentia CLI plugin source in
`agentia-plugin/`. The plugin exposes `agentia cpq validate` and invokes
the CPQ Guardian Python validator.

### Plugin capabilities

-   Accepts a change-request JSON file.
-   Validates against the local sample catalog or reads `Product2` from
    Salesforce through an authenticated Salesforce CLI session.
-   Supports an optional rules overlay for required and incompatible
    products.
-   Prints the validator's JSON findings and returns a non-zero exit
    status when validation fails.
-   Does not create or update Salesforce records.

### Build and link locally

Requirements: Node.js, npm, the Copado Agentia CLI, and Python.
Salesforce CLI authentication is also required for Salesforce mode.

From the repository root, run:

``` powershell
Set-Location .\agentia-plugin
npm.cmd ci
npm.cmd run build
& "$env:APPDATA\npm\agentia.cmd" plugins link .
Set-Location ..
```

If Agentia CLI is installed in a different location, use the path to
your installed `agentia.cmd` executable.

### Example commands

Run these commands from the **repository root** after building and
linking the plugin.

**1. Validate a valid sample configuration** --- expected to pass with
zero findings:

``` powershell
& "$env:APPDATA\npm\agentia.cmd" cpq validate --change sample_data/change_request_valid.json
```

**2. Validate an invalid sample configuration** --- expected to report
findings and return a non-zero exit code:

``` powershell
& "$env:APPDATA\npm\agentia.cmd" cpq validate --change sample_data/change_request_invalid.json
```

These sample scenarios use the local catalog and do not require
Salesforce authentication. For Salesforce mode, use a change-request
JSON file whose product codes exist in your connected org and
authenticate Salesforce CLI first.

### Integration boundaries

The local plugin command has been built and exercised in a development
environment, including a fresh clone of this public repository. It
invokes Python and Salesforce CLI on the local machine. This does
**not** mean Copado-hosted Headless authentication, a hosted Agentia
pipeline, or a production deployment has been configured. Users must
build and link the plugin in their own supported Agentia environment.

The Salesforce connector queries standard `Product2` fields and is
read-only. Product dependencies and incompatibilities are supplied
through a rules overlay unless explicitly mapped to the target org's
Industries CPQ/EPC schema. See `docs/AGENTIA_INTEGRATION.md`.

## Security and limitations

-   Salesforce integration is read-only; no Salesforce records or
    metadata are modified.
-   Only standard `Product2` fields are queried by default.
-   Industries CPQ/EPC relationships are not read directly until they
    are mapped to the target org's actual schema.
-   Do not commit credentials, customer records, authentication files,
    product snapshots, or generated reports to a public repository.
