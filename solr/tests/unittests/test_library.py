"""
Characterization tests for `SolrInterface._harvest_library` pagination and its
several break conditions. Locks behavior before the function moves to
solr/bigquery.py. `current_app.client.get` is mocked.
"""
import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask_testing import TestCase
import mock

from solr import app
from solr.views import SolrInterface
from models import Base


def _page(docs, num_documents=None):
    """Build a fake biblib response object with .json() and .raise_for_status()."""
    meta = {} if num_documents is None else {'num_documents': num_documents}
    r = mock.MagicMock()
    r.raise_for_status = lambda: True
    r.json = lambda: {'documents': list(docs), 'metadata': meta}
    return r


class TestHarvestLibrary(TestCase):

    def create_app(self):
        a = app.create_app(**{
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'TESTING': True,
            'PROPAGATE_EXCEPTIONS': True,
            'BIBLIB_MAX_ROWS': 2,
            'LIBRARY_ENDPOINT': 'http://adsws/biblib/libraries',
        })
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def _harvest(self, pages):
        si = SolrInterface()
        with mock.patch.object(self.app.client, 'get', side_effect=pages) as get:
            out = si._harvest_library('libid', {})
        return out, get

    def test_single_short_page_breaks(self):
        # one page shorter than maxr (2) -> stop after first request.
        out, get = self._harvest([_page(['a'])])
        self.assertEqual(out['documents'], {'a'})
        self.assertEqual(get.call_count, 1)

    def test_num_documents_satisfied_breaks(self):
        # full page (== maxr) but metadata says only 2 docs exist -> stop.
        out, get = self._harvest([_page(['a', 'b'], num_documents=2)])
        self.assertEqual(out['documents'], {'a', 'b'})
        self.assertEqual(get.call_count, 1)

    def test_multi_page_accumulation(self):
        # full pages accumulate until a short page arrives; start advances by maxr.
        pages = [_page(['a', 'b']), _page(['c', 'd']), _page(['e'])]
        out, get = self._harvest(pages)
        self.assertEqual(out['documents'], {'a', 'b', 'c', 'd', 'e'})
        self.assertEqual(get.call_count, 3)
        # third call advanced start to 2*maxr == 4
        self.assertEqual(get.call_args_list[2][1]['params']['start'], 4)

    def test_no_growth_breaks(self):
        # full page that adds nothing new (oldcount == len) -> stop after 2nd page.
        pages = [_page(['a', 'b']), _page(['a', 'b'])]
        out, get = self._harvest(pages)
        self.assertEqual(out['documents'], {'a', 'b'})
        self.assertEqual(get.call_count, 2)

    def test_empty_page_breaks(self):
        out, get = self._harvest([_page([])])
        self.assertEqual(out['documents'], set())
        self.assertEqual(get.call_count, 1)


if __name__ == '__main__':
    import unittest
    unittest.main()
