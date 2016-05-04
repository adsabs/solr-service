from flask.ext.testing import TestCase
import unittest
import app


class TestWebservices(TestCase):

    def create_app(self):
        """Start the wsgi application"""
        return app.create_app()

    def test_ResourcesRoute(self):
        """Tests for the existence of a /resources route, and that it
        returns properly formatted JSON data"""

        r = self.client.get('/resources')
        self.assertStatus(r, 200)
        # Assert each key is a string-type
        [self.assertIsInstance(k, basestring) for k in r.json]

        for expected_field, _type in {
            'scopes': list,
            'methods': list,
            'description': basestring,
            'rate_limit': list,
        }.iteritems():
            # Assert each resource is described has the expected_field
            [self.assertIn(expected_field, v) for v in r.json.values()]

            # Assert every expected_field has the proper type
            [self.assertIsInstance(v[expected_field], _type) for v in r.json.values()]

    def test_headers(self):
        """
        Every route should return some hard-coded headers if the incoming
        request has Content-Type: application/json
        """
        r = self.client.get('/status')
        self.assertEqual(r.headers['Cache-Control'], "public, max-age=600")

if __name__ == '__main__':
    unittest.main()
