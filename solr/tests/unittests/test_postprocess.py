"""
Characterization tests for `SolrInterface.postprocess_response`: publisher-based
highlight removal, highlight windowing, empty-highlight pruning, and the
`filtered` marker. Locks behavior before postprocess logic moves to
solr/postprocess.py.
"""
import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
import json
from flask_testing import TestCase

from solr import app
from solr.views import SolrInterface
from solr.tests.stubdata.solr import highlighting_solr_response
from models import Base


class _FakeResponse(object):
    """Minimal stand-in for requests.Response (postprocess only calls .json())."""
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return json.loads(self._payload)


class TestPostprocessResponse(TestCase):

    def create_app(self):
        a = app.create_app(**{
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'TESTING': True,
            'PROPAGATE_EXCEPTIONS': True,
            'SOLR_SERVICE_DISALLOWED_HIGHLIGHTS_PUBLISHERS': ['ieee'],
            'SOLR_SERVICE_MAX_FRAGSIZE': 200,
        })
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def _run(self):
        si = SolrInterface()
        return si.postprocess_response(_FakeResponse(highlighting_solr_response))

    def test_non_disallowed_publisher_keeps_highlights(self):
        # doc 1 (Elsevier) is untouched except windowing.
        result = self._run()
        self.assertEqual(result['highlighting']['1']['abstract'], ['a <em>star</em> here'])

    def test_ieee_in_list_removes_body_only(self):
        # doc 2 publisher is a list containing IEEE -> body removed, abstract kept.
        result = self._run()
        self.assertNotIn('body', result['highlighting']['2'])
        self.assertIn('abstract', result['highlighting']['2'])

    def test_ieee_string_removes_body_and_ack(self):
        # doc 3 publisher == "IEEE" -> body and ack removed, title kept.
        result = self._run()
        self.assertNotIn('body', result['highlighting']['3'])
        self.assertNotIn('ack', result['highlighting']['3'])
        self.assertIn('title', result['highlighting']['3'])

    def test_field_without_em_tags_windows_to_empty_list(self):
        # windowing a snippet with no <em> tags yields [], which then survives
        # the empty-pruning step as an empty list.
        result = self._run()
        self.assertEqual(result['highlighting']['3']['nomatch'], [])

    def test_filtered_flag_set(self):
        self.assertEqual(self._run()['filtered'], 'true')


if __name__ == '__main__':
    import unittest
    unittest.main()
