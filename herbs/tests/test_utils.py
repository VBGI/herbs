# coding: utf-8

from ..utils import get_authors, evaluate_taxons, evaluate_dates
from unittest import TestCase
from datetime import date

# TODO: Structure of utils changed, tests should be updated

class TaxonEvaluationTestCase(TestCase):
    
    def setUp(self):
        self.simple = 'SOMEFAMILY (Maxim.) L.'
        self.bad = 'SOMEFAMILY (Maxim. L.)'
        self.invalid_author = 'SOMEFAMILY jfkld>?'
        self.unbalanced = 'SOMEFAMILY (Maxim. '
        
    def test_extract_simple(self):
        res = evaluate_taxons([self.simple]).pop()
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1], ('', [(0, 'Maxim.'), (1, 'L.')]))
    
    def test_extract_bad_aux(self):
        res = evaluate_taxons([self.bad]).pop()
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1], ('Auxiliary authors without primary authors are given', [(0, '(Maxim. L.)')]))
        
    def test_invalid_author_string(self):
        res = evaluate_taxons([self.invalid_author]).pop()
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1][0], 'Invalid author string')
    
    def test_unbalanced_auth_str(self):
        res = evaluate_taxons([self.unbalanced]).pop()
        self.assertEqual(res[0], 'somefamily')
        self.assertEqual(res[1][0], 'Unbalanced parenthesis')


class DateEvaluationTestCase(TestCase):
    
    def setUp(self):
        self.wrong_day = '67 января 1900 г.'
        self.all_ok = '01 января 1981 г.'
        self.wrong_month = '34 гоп 1999 г.'
        self.wrong_year = '12 марта 2087'
        self.no_year = '12 марта 09 г.'
        self.no_day = 'авгст, 1999'
    
    def test_wrong_day(self):
        res = evaluate_dates([self.wrong_day]).pop()
        self.assertEqual(res[0], 'Day not in range')
    
    def test_all_ok(self):
        res = evaluate_dates([self.all_ok]).pop()
        self.assertEqual(res[0], '')
        self.assertEqual(res[1], date(year=1981, day=1, month=1))
    
    def test_wrong_month(self):
        res = evaluate_dates([self.wrong_month]).pop()
        self.assertEqual(res[0], 'Month not found')
    
    def test_wrong_year(self):
        res = evaluate_dates([self.wrong_year]).pop()
        self.assertEqual(res[0], 'Strange year')
        
    def test_no_year(self):
        res = evaluate_dates([self.no_year]).pop()
        self.assertEqual(res[0], 'Year not found')

    def test_no_day(self):
        res = evaluate_dates([self.no_day]).pop()
        self.assertEqual(res[0], 'Day not found')
