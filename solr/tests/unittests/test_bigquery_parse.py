"""
Characterization tests for the bigquery-parsing helpers:
`SolrInterface._extract_docs_values` and the `{!bitset}` fq-injection branches
of `check_for_embedded_bigquery`. Locks behavior before they move to
solr/bigquery.py.
"""
import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask_testing import TestCase
import mock

from solr import app
from solr.views import SolrInterface
from models import Base


def _request(data='', files=None):
    r = mock.MagicMock()
    r.data = data
    r.files = files or {}
    return r


class TestExtractDocsValues(TestCase):

    def create_app(self):
        a = app.create_app(**{'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def test_single(self):
        si = SolrInterface()
        self.assertEqual(si._extract_docs_values('foo docs(abc) bar'), ['abc'])

    def test_multiple(self):
        si = SolrInterface()
        self.assertEqual(
            si._extract_docs_values('docs(abc) AND docs(xyz)'), ['abc', 'xyz'])

    def test_library_prefix_preserved(self):
        si = SolrInterface()
        self.assertEqual(si._extract_docs_values('docs(library/abc)'), ['library/abc'])

    def test_none_present(self):
        si = SolrInterface()
        self.assertEqual(si._extract_docs_values('q=star'), [])


class TestBitsetInjection(TestCase):

    def create_app(self):
        a = app.create_app(**{'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def _check(self, params, request, headers):
        si = SolrInterface()
        return si.check_for_embedded_bigquery(params, request, headers)

    def test_no_fq_injected_when_data_present(self):
        params = {}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self._check(params, _request(data='bibcode\nfoo'), headers)
        self.assertEqual(params['fq'], [u'{!bitset}'])
        # files were produced -> Content-Type removed for multipart
        self.assertNotIn('Content-Type', headers)

    def test_string_fq_gets_bitset_appended(self):
        params = {'fq': 'author:foo'}
        self._check(params, _request(data='bibcode\nfoo'), {'Content-Type': 'x'})
        self.assertEqual(params['fq'], u'author:foo {!bitset}')

    def test_list_fq_gets_bitset_appended(self):
        params = {'fq': ['author:foo']}
        self._check(params, _request(data='bibcode\nfoo'), {'Content-Type': 'x'})
        self.assertEqual(params['fq'], ['author:foo', u'{!bitset}'])

    def test_no_data_no_injection(self):
        params = {}
        headers = {'Content-Type': 'x'}
        files = self._check(params, _request(data=''), headers)
        self.assertNotIn('fq', params)
        self.assertEqual(files, {})
        # no files -> Content-Type preserved
        self.assertIn('Content-Type', headers)


if __name__ == '__main__':
    import unittest
    unittest.main()
