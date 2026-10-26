import unittest
from src.guardian import validate
from pathlib import Path
import json
BASE = Path(__file__).resolve().parents[1]
class GuardianTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((BASE/'sample_data/catalog.json').read_text())
    def test_detects_incompatible_products(self):
        r=validate(self.catalog, {'proposed_products':['BASIC_VIDEO','PREMIUM_VIDEO']})
        self.assertIn('INCOMPATIBLE_PRODUCTS',[x['rule_id'] for x in r['findings']])
    def test_detects_missing_required_product(self):
        r=validate(self.catalog, {'proposed_products':['HOME_STARTER']})
        self.assertIn('MISSING_REQUIRED_PRODUCT',[x['rule_id'] for x in r['findings']])
    def test_valid_configuration_passes(self):
        r=validate(self.catalog, {'proposed_products':['HOME_STARTER','BROADBAND_MODEM','VOICE_ADDON']})
        self.assertEqual('PASS',r['status'])
    def test_unknown_product(self):
        r=validate(self.catalog, {'proposed_products':['NOT_REAL']})
        self.assertIn('UNKNOWN_PRODUCT',[x['rule_id'] for x in r['findings']])
    def test_no_writes(self):
        r=validate(self.catalog, {'proposed_products':['VOICE_ADDON']})
        self.assertTrue(r['read_only'])
if __name__=='__main__': unittest.main()
