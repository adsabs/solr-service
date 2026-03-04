import unittest

from solr.query_rewrite import rewrite_unfielded_ads_query


class TestQueryRewrite(unittest.TestCase):

    def test_lastname_year(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Kurtz 2000'),
            '(first_author:"kurtz" OR author:"kurtz") year:2000'
        )

    def test_lastname_year_suffix(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Kurtz 2000a'),
            '(first_author:"kurtz" OR author:"kurtz") year:2000'
        )

    def test_lastname_amp_lastname_year(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Kurtz & Mink 2000b'),
            'first_author:"kurtz" author:"mink" year:2000'
        )

    def test_three_authors_with_amp(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Kurtz, Zhu & Henson 2000'),
            '((first_author:"kurtz" author:("zhu" "henson")) OR (first_author:"kurtz zhu" author:"henson")) year:2000'
        )

    def test_et_al(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Kurtz et al 2000'),
            'first_author:"kurtz" author_count:[2 TO 10000] year:2000'
        )

    def test_et_al_with_period(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Kurtz et al. 2000'),
            'first_author:"kurtz" author_count:[2 TO 10000] year:2000'
        )

    def test_double_lastname_et_al(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Blanco Cuaresma et al 2020'),
            '((first_author:"blanco cuaresma" author_count:[2 TO 10000]) OR (first_author:"blanco" author:"cuaresma" author_count:[3 TO 10000])) year:2020'
        )

    def test_double_lastname_with_amp(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Blanco Cuaresma & Lockhart 2020'),
            '((first_author:"blanco" author:("cuaresma" "lockhart")) OR (first_author:"blanco cuaresma" author:"lockhart")) year:2020'
        )

    def test_firstname_lastname_year(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('stephanie jarmak 2020'),
            '(author:"stephanie jarmak" OR author("stephanie" "jarmak")) year:2020'
        )

    def test_lastname_lastname_year(self):
        self.assertEqual(
            rewrite_unfielded_ads_query('Accomazzi Kurtz 2020'),
            '(author:"accomazzi kurtz" OR author("accomazzi" "kurtz")) year:2020'
        )

    def test_explicit_field_is_not_rewritten(self):
        self.assertIsNone(rewrite_unfielded_ads_query('author:kurtz year:2000'))

    def test_no_year_is_not_rewritten(self):
        self.assertIsNone(rewrite_unfielded_ads_query('Kurtz Mink'))
