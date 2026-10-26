# Demo walkthrough (2–3 minutes)

1. Introduce Guardian as a read-only Salesforce CPQ validation quality gate.
2. Run the invalid local sample and show incompatible products plus missing required modem.
3. Run the five unit tests.
4. Run the valid sample and show PASS / zero findings.
5. Explain Salesforce path: authenticate Salesforce CLI, query standard Product2 fields, map ProductCode values, and apply a reviewed overlay for dependency/incompatibility rules.
6. If live Salesforce auth is available, run the documented `--salesforce` command in the user's org and record the real output. Do not use sample output as evidence of live org connectivity.
7. Clearly distinguish Salesforce CLI read-only integration from the separate Agentia plugin, which must be generated, linked, and verified in the target Agentia environment.
