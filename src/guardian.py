#!/usr/bin/env python3
"""Agentia CPQ Guardian: deterministic telecom CPQ configuration validator."""
import argparse, json, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path


def load_json(path):
    with open(path, encoding='utf-8') as f: return json.load(f)


def salesforce_products(target_org, limit=2000):
    """Read Product2 from an org authenticated with Salesforce CLI; read-only."""
    cmd = ['sf', 'org', 'display', '--json', '--target-org', target_org]
    try:
        auth = json.loads(subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE))
    except FileNotFoundError as e:
        raise RuntimeError('Salesforce CLI (sf) was not found. Install it and run sf org login web first.') from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError('Could not read Salesforce CLI auth. Run `sf org login web --alias YOUR_ALIAS` and retry.') from e
    result = auth.get('result', {})
    token, instance = result.get('accessToken'), result.get('instanceUrl')
    if not token or not instance:
        raise RuntimeError('Salesforce CLI did not return an access token and instance URL. Re-authenticate the org.')
    soql = f"SELECT Id, Name, ProductCode, Family, IsActive, Description FROM Product2 ORDER BY Name LIMIT {int(limit)}"
    endpoint = instance.rstrip('/') + '/services/data/v60.0/query/?q=' + urllib.parse.quote(soql)
    req = urllib.request.Request(endpoint, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response: data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        raise RuntimeError(f'Salesforce Product2 query failed: {e}') from e
    products = []
    for rec in data.get('records', []):
        code = rec.get('ProductCode') or rec.get('Id')
        products.append({'id': code, 'salesforce_id': rec.get('Id'), 'name': rec.get('Name'),
                         'product_code': rec.get('ProductCode'), 'family': rec.get('Family'),
                         'active': rec.get('IsActive'), 'description': rec.get('Description'),
                         'requires': [], 'incompatible_with': []})
    return {'source': 'salesforce', 'target_org': target_org, 'products': products,
            'note': 'Read-only Product2 snapshot. Add dependency/incompatibility rules in the rules overlay.'}


def merge_rules(catalog, rules_path):
    if not rules_path: return catalog
    rules = load_json(rules_path)
    by_id = {p['id']: p for p in catalog.get('products', [])}
    for pid, values in rules.get('rules', {}).items():
        if pid in by_id:
            by_id[pid]['requires'] = values.get('requires', [])
            by_id[pid]['incompatible_with'] = values.get('incompatible_with', [])
    return catalog


def validate(catalog, change):
    products = {p['id']: p for p in catalog.get('products', [])}
    proposed = list(dict.fromkeys(change.get('proposed_products', [])))
    target = change.get('target_product')
    findings = []
    def add(code, severity, message, affected, evidence, next_step):
        findings.append({'rule_id': code, 'severity': severity, 'message': message,
                         'affected_products': affected, 'evidence': evidence, 'suggested_next_step': next_step})
    if target and target not in products:
        add('UNKNOWN_TARGET_PRODUCT', 'critical', f'Target product {target} does not exist in the catalog.', [target],
            {'target_product': target}, 'Refresh the catalog and confirm the product code before proceeding.')
    for pid in proposed:
        if pid not in products:
            add('UNKNOWN_PRODUCT', 'high', f'Product {pid} is not present in the catalog.', [pid], {'product_id': pid},
                'Correct the product code or refresh the catalog snapshot.')
    known = [pid for pid in proposed if pid in products]
    chosen = set(known)
    for pid in known:
        p = products[pid]
        if p.get('active') is False:
            add('INACTIVE_PRODUCT', 'high', f'{pid} is inactive in the catalog.', [pid], {'product_id': pid},
                'Use an active product or confirm the intended lifecycle status.')
        for req in p.get('requires', []):
            if req not in chosen:
                add('MISSING_REQUIRED_PRODUCT', 'high', f'{pid} requires {req}, but it is not in the proposed configuration.',
                    [pid, req], {'product_id': pid, 'required_product': req}, 'Add the required product or revise the bundle rules.')
        for other in p.get('incompatible_with', []):
            if other in chosen and pid < other:
                add('INCOMPATIBLE_PRODUCTS', 'high', f'{pid} is incompatible with {other}.', [pid, other],
                    {'product_a': pid, 'product_b': other}, 'Remove one product or review the compatibility rule with the catalog owner.')
    return {'project': 'Agentia CPQ Guardian', 'status': 'FAIL' if findings else 'PASS', 'finding_count': len(findings),
            'source': catalog.get('source', 'json'), 'target_org': catalog.get('target_org'),
            'proposed_products': proposed, 'findings': findings,
            'read_only': True, 'note': 'No Salesforce records are created or modified.'}


def main():
    ap = argparse.ArgumentParser(description='Validate telecom CPQ configurations against a catalog snapshot.')
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument('--catalog', help='Local normalized catalog JSON')
    source.add_argument('--salesforce', action='store_true', help='Read Product2 from an authenticated Salesforce org')
    ap.add_argument('--target-org', help='Salesforce CLI org alias (required with --salesforce)')
    ap.add_argument('--change', required=True, help='Proposed change JSON')
    ap.add_argument('--rules', help='Optional JSON overlay for requires/incompatible_with rules')
    ap.add_argument('--output', default='report.json', help='Output report path')
    ap.add_argument('--snapshot-output', help='Optional path to save Salesforce catalog snapshot')
    ap.add_argument('--limit', type=int, default=2000, help='Maximum Product2 records to fetch')
    args = ap.parse_args()
    try:
        if args.salesforce:
            if not args.target_org: ap.error('--target-org is required with --salesforce')
            catalog = salesforce_products(args.target_org, args.limit)
            if args.snapshot_output: Path(args.snapshot_output).write_text(json.dumps(catalog, indent=2), encoding='utf-8')
        else: catalog = load_json(args.catalog)
        catalog = merge_rules(catalog, args.rules)
        report = validate(catalog, load_json(args.change))
        Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
        return 1 if report['status'] == 'FAIL' else 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as e:
        print(f'ERROR: {e}', file=sys.stderr); return 2

if __name__ == '__main__': raise SystemExit(main())
