import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask.ext.testing import TestCase
from flask import url_for
import unittest
import httpretty
import json
import app
from werkzeug.security import gen_salt
from StringIO import StringIO

class TestWebservices(TestCase):

    def create_app(self):
        """Start the wsgi application"""
        a = app.create_app()
        return a

    @httpretty.activate
    def test_cookie_forwarding(self):
        """
        Test that cookies get properly passed by the SolrInterface
        """

        def request_callback(request, uri, headers):
            return 200, headers, request.headers.get('cookie')

        httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_SERVICE_SEARCH_HANDLER'),
            body=request_callback,
        )
        with self.client as c:
            cookie_value = gen_salt(200)

            # This cookie should be forwarded
            c.set_cookie(
                'localhost',
                self.app.config.get("SOLR_SERVICE_FORWARD_COOKIE_NAME"),
                cookie_value
            )

            # This cookie should not be forwarded
            c.set_cookie(
                'localhost',
                'cookie_name',
                'cookie_value'
            )

            r = c.get(url_for('search'), query_string={'q': 'star'})

            # One and only one cookie
            self.assertEqual(len(r.data.split('=')), 2)

            # This forwarded cookie should match the one we gave originally
            rcookie_value = r.data.split('=')[1]
            self.assertEqual(rcookie_value, cookie_value)


    @httpretty.activate
    def test_sanitization(self):
        """
        Tests that fields are properly removed from the query params before
        being forwarded to solr
        """

        def request_callback(request, uri, headers):
            if 'fl' not in request.parsed_body:
                return 503, headers, "{'The query parameters were not passed properly'}"
            if 'title' not in request.parsed_body['fl']:
                return 503, headers, "{'The query parameters were not passed properly'}"
            if 'body' in request.parsed_body['fl']:
                return 503, headers, "{'The query was not sanitized properly'}"
            return 200, \
                   headers, \
                   "The {0} response from {1}".format(
                       request.method, uri
                   )

        httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_SERVICE_SEARCH_HANDLER'),
            body=request_callback)

        resp = self.client.get(
                url_for('search'),
                query_string={'q': 'star', 'fl': 'body,title'},
        )
        self.assertEqual(resp.status_code, 200)

    @httpretty.activate
    def test_search(self):
        """
        Test the search endpoint
        """
        httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_SERVICE_SEARCH_HANDLER'),
            content_type='application/json',
            status=200,
            body="""{
            "responseHeader":{
            "status":0, "QTime":0,
            "params":{ "fl":"title,bibcode", "indent":"true", "wt":"json", "q":"*:*"}},
            "response":{"numFound":10456930,"start":0,"docs":[
              { "bibcode":"2005JGRC..110.4002G" },
              { "bibcode":"2005JGRC..110.4003N" },
              { "bibcode":"2005JGRC..110.4004Y" }]}}""")

        r = self.client.get(url_for('search'))
        self.assertStatus(r, 200)
        self.assertIn('responseHeader', r.json)

    @httpretty.activate
    def test_qtree(self):
        """
        Test the qtree endpoint
        """
        httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_SERVICE_QTREE_HANDLER'),
            content_type='application/json',
            status=200,
            body=r'''{
             "qtree": "\n{\"name\":\"OPERATOR\", \"label\":\"DEFOP\", \"children\": [\n    {\"name\":\"MODIFIER\", \"label\":\"MODIFIER\", \"children\": [\n        {\"name\":\"TMODIFIER\", \"label\":\"TMODIFIER\", \"children\": [\n            {\"name\":\"FIELD\", \"label\":\"FIELD\", \"children\": [\n                {\"name\":\"QNORMAL\", \"label\":\"QNORMAL\", \"children\": [\n                    {\"name\":\"TERM_NORMAL\", \"input\":\"star\", \"start\":0, \"end\":3}]\n                }]\n            }]\n        }]\n    }]\n}",
             "responseHeader": {
              "status": 0,
              "QTime": 6,
              "params": {
               "q": "star",
               "wt": "json",
               "fl": "id"
              }
             }
            }'''
        )

        r = self.client.get(url_for('qtree'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('qtree', r.json)
        self.assertIn('name', json.loads(r.json['qtree']))

        r = self.client.post(url_for('tvrh'))
        self.assertStatus(r, 405)


    @httpretty.activate
    def test_tvrh(self):
        """
        Test the tvrh endpoint
        """
        httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_SERVICE_TVRH_HANDLER'),
            content_type='application/json',
            status=200,
            body="""
                {
        "responseHeader":{
        "status":0,
        "QTime":1,
        "params":{
          "fl":"title",
          "indent":"on",
          "start":"0",
          "q":"*:*",
          "tv":"true",
          "tv.all":"true",
          "tv.fl":"abstract",
          "wt":"json",
          "qt":"tvrh",
          "rows":"1"}},
        "response":{"numFound":10715572,"start":0,"docs":[
          {
            "title":["The Structure of Convection in the Planetary Boundary -"]}]
        },
        "termVectors":[
        "uniqueKeyFieldName","id",
        "374878",[
          "uniqueKey","374878"]]}
                """
        )

        resp = self.client.get(url_for('tvrh'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('termVectors', resp.json)

    @httpretty.activate
    def test_bigquery(self):
        """
        Test the bigquery endpoint
        """
        def request_callback(request, uri, headers):
            if 'q' not in request.querystring:
                return 500, headers, "{'The query parameters were not passed properly'}"
            return 200, \
                   headers, \
                   "The {0} response from {1}".format(
                       request.method, uri
                   )

        httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_SERVICE_BIGQUERY_HANDLER'),
            body=request_callback)

        bibcodes = 'bibcode\n1907AN....174...59.\n1908PA.....16..445.\n1989LNP...334..242S'
        resp = self.client.post(
                url_for('bigquery'),
                content_type='multipart/form-data',
                data={
                    'q': '*:*',
                    'fl': 'bibcode',
                    'fq': '{!bitset}',
                    'file_field': (StringIO(bibcodes), 'big-query/csv')
                }
        )

        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
                url_for('bigquery'),
                content_type='multipart/form-data',
                data={
                    'q': '*:*',
                    'fl': 'bibcode',
                    'file_field': (StringIO(bibcodes), 'big-query/csv'),
                    }
        )

        self.assertEqual(resp.status_code, 400)

if __name__ == '__main__':
    unittest.main()
