from ..utils import get_authors, evaluate_taxons
from unittest import TestCase


class TaxonEvaluationTestCase(TestCase):
    
    def setUp(self):
        self.simple = 'SOMEFAMILY (Maxim.) L.'
        self.bad = 'SOMEFAMILY (Maxim. L.)'
        self.invalid_author = 'SOMEFAMILY jfkld>?'
        self.unbalanced = 'SOMEFAMILY (Maxim. '
        
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
        
    def test_invalid_author_string(self):
        res = evaluate_taxons([self.invalid_author])
        res = res[0]
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1][0], 'Invalid author string')
    
    def test_unbalanced_auth_str(self):
        res = evaluate_taxons([self.unbalanced])
        res = res[0]
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1][0], 'Unbalanced parenthesis')
        
class DateEvaluationTestCase(TestCase):
    
    def setUp(self):
        self.simple = '67 января'
        