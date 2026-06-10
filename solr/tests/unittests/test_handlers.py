"""
Characterization tests for handler-class routing (`Search.get_handler_class`)
and host parsing (`SolrInterface._get_host`). Locks behavior before the routing
logic is deduped into solr/handlers.py and host parsing into solr/transport.py.
"""
import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask_testing import TestCase

from solr import app
from solr.views import Search, SolrInterface
from models import Base


class TestClassifyRequest(TestCase):

    def create_app(self):
        a = app.create_app(**{
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'TESTING': True,
            'BOT_TOKENS': ['GoogleBot'],
        })
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def _classify(self, headers):
        with self.app.test_request_context(headers=headers):
            return Search().get_handler_class()

    def test_default_for_normal_user(self):
        self.assertEqual(self._classify({'Authorization': 'Bearer NormalUser'}), 'default')

    def test_bot_token_via_authorization(self):
        # token is header[7:], so "Bearer GoogleBot" -> "GoogleBot"
        self.assertEqual(self._classify({'Authorization': 'Bearer GoogleBot'}), 'bot')

    def test_bot_token_via_forwarded_authorization_precedence(self):
        headers = {
            'X-Forwarded-Authorization': 'Bearer GoogleBot',
            'Authorization': 'Bearer NormalUser',
        }
        self.assertEqual(self._classify(headers), 'bot')

    def test_anonymous_uid(self):
        self.assertEqual(
            self._classify({'Authorization': 'Bearer x', 'X-api-uid': '1'}), 'anonymous')

    def test_no_auth_header_is_default(self):
        # missing Authorization -> [][7:] == [] -> not a bot -> default
        self.assertEqual(self._classify({}), 'default')


class TestGetHost(TestCase):

    def create_app(self):
        a = app.create_app(**{'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def test_full_url(self):
        self.assertEqual(SolrInterface()._get_host('http://host:8983/solr/select'), 'host:8983')

    def test_bare_hostport(self):
        self.assertEqual(SolrInterface()._get_host('host:8983/solr/select'), 'host:8983')

    def test_uppercase_scheme(self):
        self.assertEqual(SolrInterface()._get_host('HTTP://host:8983/solr'), 'host:8983')


if __name__ == '__main__':
    import unittest
    unittest.main()
