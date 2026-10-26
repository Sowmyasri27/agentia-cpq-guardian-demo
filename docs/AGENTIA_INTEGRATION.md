# Copado Agentia integration plan

The Salesforce adapter is independent of Agentia. To expose it as a native Agentia command, generate a plugin using the currently supported Copado Agentia plugin generator and port the validator into its command action.

```bash
npm install -g @copado/agentia-cli
agentia setup
npm init @copado/agentia-plugin agentia-cpq-guardian
cd agentia-cpq-guardian
npm install
npm run build
agentia plugins link .
```

Review the current Copado docs before running commands; plugin generator templates and extension contracts may change. The generated plugin API should be the source of truth. Do not import private Agentia CLI internals, call undocumented Copado endpoints, or claim a plugin is live until `agentia --help` shows the command and it succeeds in the intended environment.

Suggested command workflow:
1. Select an authenticated Salesforce org alias.
2. Read Product2 via Salesforce CLI session.
3. Map ProductCode to IDs and apply a reviewed CPQ rules overlay mapped to the org's actual catalog schema.
4. Run deterministic rules.
5. Display findings and write a JSON report.
6. Require a human review; do not perform automated production writes.
