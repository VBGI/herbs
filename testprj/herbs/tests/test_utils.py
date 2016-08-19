from ..utils import get_authors, evaluate_taxons
from unittest import TestCase


class TaxonEvaluationTestCase(TestCase):
    
    def setUp(self):
        self.simple = 'SOMEFAMILY (Maxim.) L.'
        self.bad = 'SOMEFAMILY (Maxim. L.)'
    def test_extract_simple(self):
        res = evaluate_taxons([self.simple])
        res = res[0]
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1], ('', [(0, 'Maxim.'), (1, 'L.')]))
    
    def test_extract_bad_aux(self):
        res = evaluate_taxons([self.bad])
        res = res[0]
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1], ('Auxiliary authors without primary authors are given', [(0, '(Maxim. L.)')]))
        
        
