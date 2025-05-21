import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask_testing import TestCase
from flask import url_for
import unittest
import httpretty
import json
from solr import app
from werkzeug.security import gen_salt
from werkzeug.datastructures import MultiDict
from io import BytesIO
from solr.tests.mocks import MockSolrResponse
from solr.views import SolrInterface
from solr.models import Limits, Base
import mock

class TestSolrInterface(TestCase):

    def create_app(self):
        """Start the wsgi application"""
        a = app.create_app(**{
               'SQLALCHEMY_DATABASE_URI': 'sqlite://',
               'SQLALCHEMY_ECHO': False,
               'TESTING': True,
               'PROPAGATE_EXCEPTIONS': True,
               'TRAP_BAD_REQUEST_ERRORS': True,
               'SOLR_SERVICE_DEFAULT_ROWS': 10,
               'SOLR_SERVICE_MAX_ROWS': 100,
               'SOLR_SERVICE_DISALLOWED_FIELDS': ['full', 'bar']
            })
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def test_cleanup_solr_request(self):
        """
        Simple test of the cleanup classmethod
        """
        si = SolrInterface()
        payload = {}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['rows'], self.app.config.get('SOLR_SERVICE_DEFAULT_ROWS', 10))
        self.assertEqual(cleaned['fl'], 'id')

        payload = {'rows': '1000000'}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['rows'], self.app.config.get('SOLR_SERVICE_MAX_ROWS', 100))

        payload = {'rows': 1000000}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['rows'], self.app.config.get('SOLR_SERVICE_MAX_ROWS', 100))

        payload = {'rows': '5'}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['rows'], 5)

        payload = {'rows': ['5', '1000000']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['rows'], 5)

        payload = {'rows': ['1', '0']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['rows'], 1)

        payload = {'hl.snippets': 1000000, 'hl.fragsize': 1000000}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['hl.snippets'], self.app.config.get('SOLR_SERVICE_MAX_SNIPPETS', 4))
        self.assertEqual(cleaned['hl.fragsize'], self.app.config.get('SOLR_SERVICE_MAX_FRAGSIZE', 100))

        payload = {'hl.snippets': [2, 1000000], 'hl.fragsize': [3, 1000000]}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['hl.snippets'], self.app.config.get('SOLR_SERVICE_MAX_SNIPPETS', 2))
        self.assertEqual(cleaned['hl.fragsize'], self.app.config.get('SOLR_SERVICE_MAX_FRAGSIZE', 3))

        payload = {'fl': ['id,bibcode,title,volume']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['fl'], 'id,bibcode,title,volume')

        payload = {'fl': ['id ', ' bibcode ', 'title ', ' volume']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['fl'], 'id,bibcode,title,volume')
        self.assertEqual(cleaned['rows'], self.app.config.get('SOLR_SERVICE_DEFAULT_ROWS', 100))

        payload = {'fl': ['id', 'bibcode', '*']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertNotIn('*', cleaned['fl'])

        payload = {'fl': ['id,bibcode,*']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertNotIn('*', cleaned['fl'])

        payload = {'stats.field': ['body']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['stats.field'], '')

        payload = {'hl.fl': ['body']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['hl.fl'], '')

        payload = {'sort': ['body asc']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['sort'], '')

        payload = {'sort': ['bibcode desc']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['sort'], 'bibcode desc')

        payload = {'sort': ['body asc, bibcode desc']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['sort'], 'bibcode desc')

        payload = {'facet.pivot': ['body']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['facet.pivot'], '')

        payload = {'facet.field': ['body']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['facet.field'], '')

        payload = {'facet.field': ['author_facet_hier']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['facet.field'], 'author_facet_hier')

        payload = {'fq': ['pos(1,author:foo)']}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['fq'], ['pos(1,author:foo)'])

        self.assertEqual(headers,
                         {'Host': u'localhost:8983', 'Content-Type': 'application/x-www-form-urlencoded'})

        # cites.fl=bibcode,pubdate,body&cites.q=citations(bibcode:2011MNRAS.413..971D)&fl=bibcode,cites:[subquery]&indent=on&q=author:Liske&wt=json
        payload = {'cites.fl': 'bibcode,full', 'cites.q': 'bibcode:2011MNRAS.413..971D', 'fl': 'bibcode,cites:[subquery]', 'q': 'author:name'}
        cleaned, headers = si.cleanup_solr_request(payload)
        self.assertEqual(cleaned['cites.fl'], 'bibcode')

    def test_limits(self):
        """
        Prevent users from getting certain data
        """
        si = SolrInterface()
        with self.app.session_scope() as session:
            session.add(Limits(uid='9', field='full', filter='bibstem:apj'))
            session.commit()
            self.assertTrue(len(session.query(Limits).filter_by(uid='9').all()) == 1)

        payload = {'fl': ['id,bibcode,title,full,bar'], 'q': '*:*'}
        cleaned, headers = si.cleanup_solr_request(payload, user_id='9')
        self.assertEqual(cleaned['fl'], u'id,bibcode,title,full')
        self.assertEqual(cleaned['fq'], [u'bibstem:apj'])

        cleaned, headers = si.cleanup_solr_request(
            {'fl': ['id,bibcode,full'], 'fq': ['*:*']},
            user_id='9')
        self.assertEqual(cleaned['fl'], u'id,bibcode,full')
        self.assertEqual(cleaned['fq'], ['*:*', u'bibstem:apj'])

        # multiple entries for the user
        with self.app.session_scope() as session:
            session.add(Limits(uid='9', field='bar', filter='bibstem:apr'))
            session.commit()

        cleaned, headers = si.cleanup_solr_request(
            {'fl': ['id,bibcode,fuLL,BAR'], 'fq': ['*:*']},
            user_id='9')
        self.assertEqual(cleaned['fl'], u'id,bibcode,full,bar')
        self.assertEqual(cleaned['fq'], ['*:*', u'bibstem:apj', u'bibstem:apr'])
    def test_rewrite_citations(self):
        """
        Simple tests of the rewrite citations query method
        """
        si = SolrInterface()
        payload1 = {'fl': 'bibcode', 'q': ['citations(bibcode:2011MNRAS.413..971D=1)', 'and another thing']}
        payload2 = {'fl': 'bibcode', 'q': 'references(bibcode:2011MNRAS.413..971D=2)'}
        payload3 = {'fl': 'bibcode', 'q': 'citations(identifier:2011MNRAS.413..971D=3)'}
        payload4 = {'fl': 'bibcode', 'q': ['references(identifier:2011MNRAS.413..971D=4)']}
        payload5 = {'fl': ['id,bibcode,title,full,bar'], 'q': '*:*'}
        cleaned1, rewrote = si.rewrite_citations(payload1['q'])
        self.assertEqual(rewrote, None)
        self.assertEqual(cleaned1, ['citations(bibcode:2011MNRAS.413..971D=1)', 'and another thing'])
        cleaned2, rewrote = si.rewrite_citations(payload2['q'])
        self.assertEqual(rewrote, 'bibcode:2011MNRAS.413..971D=2')
        self.assertEqual(cleaned2, 'citation:2011MNRAS.413..971D=2')
        cleaned3, rewrote = si.rewrite_citations(payload3['q'])
        self.assertEqual(rewrote, 'identifier:2011MNRAS.413..971D=3')
        self.assertEqual(cleaned3, 'reference:2011MNRAS.413..971D=3')
        cleaned4, rewrote = si.rewrite_citations(payload4['q'])
        self.assertEqual(rewrote, 'identifier:2011MNRAS.413..971D=4')
        self.assertEqual(cleaned4, ['citation:2011MNRAS.413..971D=4'])
        cleaned5, rewrote = si.rewrite_citations(payload5['q'])
        self.assertFalse(rewrote)
        self.assertEqual(cleaned5, '*:*')

    def test_is_second_order(self):
        """
        Simple test of the cleanup classmethod
        """
        si = SolrInterface()
        query = "darmok and jalad at tanagra"
        is_so = si.is_second_order(query)
        self.assertFalse(is_so)
        query = "darmok and similar(jalad at tanagra)"
        is_so = si.is_second_order(query)
        self.assertTrue(is_so)
        query = "darmok and topn(similar(jalad at tanagra))"
        is_so = si.is_second_order(query)
        self.assertTrue(is_so)
        query = "darmok and reviews(identifier:2011MNRAS.413..971D=3) AND more"
        is_so = si.is_second_order(query)
        self.assertTrue(is_so)
        query = "useful(references(identifier:2011MNRAS.413..971D=3)) darmok and "
        is_so = si.is_second_order(query)
        self.assertTrue(is_so)
        query = "useful(citations(darmok and jalad)) darmok and "
        is_so = si.is_second_order(query)
        self.assertTrue(is_so)
        query = "trending(identifier:2011MNRAS.413..971D=3) darmok and more fielded:query)"
        is_so = si.is_second_order(query)
        self.assertTrue(is_so)
    def test_sub_bibcode(self):
        si = SolrInterface()
        query = "reference:abcde"
        bibcode = "12345"
        new_q = si.sub_bibcode(query, bibcode)
        self.assertEqual(new_q, "reference:12345")

class TestWebservices(TestCase):

    def create_app(self):
        """Start the wsgi application"""
        a = app.create_app(**{
               'SQLALCHEMY_DATABASE_URI': 'sqlite://',
               'SQLALCHEMY_ECHO': True,
               'TESTING': True,
               'PROPAGATE_EXCEPTIONS': True,
               'TRAP_BAD_REQUEST_ERRORS': True,
               'SOLR_SERVICE_DISALLOWED_FIELDS': ['full', 'bar'],
               'SOLR_SERVICE_SEARCH_HANDLER': 'http://localhost:8983/solr/select',
               'BOT_SOLR_SERVICE_SEARCH_HANDLER': 'http://bot-localhost:8983/solr/select',
               'BOT_TOKENS': ['GoogleBot'],
            })
        Base.query = a.db.session.query_property()
        return a

    def setUp(self):
        Base.metadata.create_all(bind=self.app.db.engine)

    def tearDown(self):
        self.app.db.session.remove()
        self.app.db.drop_all()

    def test_bot_request(self):
        """
        Test that bot requests are sent to the right endpoint
        """
        with MockSolrResponse(self.app.config['BOT_SOLR_SERVICE_SEARCH_HANDLER']):
            r = self.client.get(url_for('search'), query_string={'q': 'star'}, headers={'Authorization': 'Bearer:GoogleBot'})
            # At this point, an exception would have happened if the request was
            # sent to SOLR_SERVICE_SEARCH_HANDLER instead of BOT_SOLR_SERVICE_SEARCH_HANDLER

        with MockSolrResponse(self.app.config['SOLR_SERVICE_SEARCH_HANDLER']):
            r = self.client.get(url_for('search'), query_string={'q': 'star'}, headers={'Authorization': 'Bearer:NormalUser'})
            # At this point, an exception would have happened if the request was
            # sent to BOT_SOLR_SERVICE_SEARCH_HANDLER instead of SOLR_SERVICE_SEARCH_HANDLER

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

            for cookie_name in self.app.config.get("SOLR_SERVICE_FORWARDED_COOKIES"):
                # This cookie should be forwarded
                c.set_cookie(
                    'localhost',
                    cookie_name,
                    cookie_value
                )

            # This cookie should not be forwarded
            c.set_cookie(
                'localhost',
                'cookie_name',
                'cookie_value'
            )

            r = c.get(url_for('search'), query_string={'q': 'star'})

            # Two cookies (session and sroute)
            self.assertEqual(len(r.data.decode('utf-8').split(';')), len(self.app.config.get("SOLR_SERVICE_FORWARDED_COOKIES")))

            # This forwarded cookie should match the one we gave originally
            n_found_cookies_with_good_value = 0
            for cookie in r.data.decode('utf-8').split(';'):
                key, value = cookie.split('=')
                if key in self.app.config.get("SOLR_SERVICE_FORWARDED_COOKIES"):
                    self.assertEqual(value.strip(), cookie_value)
                    n_found_cookies_with_good_value += 1
            self.assertEqual(n_found_cookies_with_good_value, len(self.app.config.get("SOLR_SERVICE_FORWARDED_COOKIES")))


    def test_disallowed_fields(self):
        """
        disallowed fields should be absent from the solr response
        """

        with MockSolrResponse(self.app.config.get('SOLR_SERVICE_SEARCH_HANDLER')):
            fl = 'title,id,abstract,{}'.format(
                ','.join(self.app.config['SOLR_SERVICE_DISALLOWED_FIELDS'])
            )
            r = self.client.get(
                url_for('search'),
                query_string={'q': 'star', 'fl': fl},
            )
            for doc in r.json['response']['docs']:
                self.assertIn('title', doc)
                self.assertIn('id', doc)
                self.assertIn('abstract', doc)
                for field in self.app.config['SOLR_SERVICE_DISALLOWED_FIELDS']:
                    self.assertNotIn(field, doc)


    def test_cleanup_params(self):
        """
        Certain parameters have limits
        """

        with MockSolrResponse(self.app.config.get('SOLR_SERVICE_SEARCH_HANDLER')):
            r = self.client.get(
                url_for('search'),
                query_string={'q': 'star', 'hl.snippets': 10},
            )
            self.assertEqual(r.json['responseHeader']['params']['hl.snippets'], ['4'])

            r = self.client.get(
                url_for('search'),
                query_string={'q': 'star', 'hl.snippets': 14, 'hl.full.snippets': 10},
            )
            self.assertEqual(r.json['responseHeader']['params']['hl.snippets'], ['4'])
            self.assertEqual(r.json['responseHeader']['params']['hl.full.snippets'], ['4'])

            r = self.client.get(
                url_for('search'),
                query_string={'q': 'star', 'hl.fragsize': '0'},
            )
            self.assertEqual(r.json['responseHeader']['params']['hl.fragsize'], ['1'])

            r = self.client.get(
                url_for('search'),
                query_string={'q': 'star', 'hl.fragsize': '50'},
            )
            self.assertEqual(r.json['responseHeader']['params']['hl.fragsize'], ['50'])


    def test_set_max_rows(self):
        """
        solr should only return up to a default number of documents
        """
        with MockSolrResponse(self.app.config.get('SOLR_SERVICE_SEARCH_HANDLER')):

            r = self.client.get(
                url_for('search'),
                query_string={'q': '*', 'rows': 10}
            )
            self.assertEqual(len(r.json['response']['docs']), 7)

            self.app.config['SOLR_SERVICE_MAX_ROWS'] = 2
            r = self.client.get(
                url_for('search'),
                query_string={'q': '*', 'rows': 10}
            )
            self.assertEqual(len(r.json['response']['docs']), 2)

            r = self.client.get(
                url_for('search'),
                query_string={'q': '*', 'rows': 10},
                headers={'X-Adsws-Ratelimit-Level': '10'}
            )
            self.assertEqual(len(r.json['response']['docs']), 2)


    def test_docs_subquery(self):
        """
        test various situation in which we pass docs(uuid) query
        """
        data = {
            "documents": [
                "1975CMaPh..43..199H",
                "1973PhRvD...7.2333B"
            ],
            "metadata": {},
            "solr": {},
            "updates": {}
        }
        din = mock.MagicMock()
        din.raise_for_status = lambda: True
        din.json = lambda: data

        out = mock.MagicMock()
        out.text = ''
        out.status_code = 200
        out.headers = {}

        with mock.patch(self.app.client, 'get', return_value=din) as get, \
            mock.patch('solr.views.requests.post', return_value=out) as post:
            r = self.client.post(url_for('bigquery'),
                                 query_string={'q': 'docs(library/hHGU1Ef-TpacAhicI3J8kQ)'},
                                 headers={'Authorization': 'Bearer foo'})
            # it made a request to retrieve library
            get.assert_called()
            assert '/biblib/libraries/hHGU1Ef-TpacAhicI3J8kQ' in get.call_args[0][0]
            assert '/solr/bigquery' in post.call_args[0]
            x = post.call_args[1]['files']['library/hHGU1Ef-TpacAhicI3J8kQ']
            assert x[2] == 'big-query/csv'

        data = {
            'query': json.dumps({'query': 'q=foo&hHGU1Ef-TpacAhicI3J8kQ=foo+bar',
                               'bigquery': 'something'})
        }
        with mock.patch(self.app.client, 'get', return_value=din) as get, \
            mock.patch('solr.views.requests.post', return_value=out) as post:
            r = self.client.post(url_for('bigquery'),
                                 query_string={'q': 'docs(hHGU1Ef-TpacAhicI3J8kQ)'},
                                 headers={'Authorization': 'Bearer foo'})
            # it made a request to retrieve library
            get.assert_called()
            assert '/vault/query/hHGU1Ef-TpacAhicI3J8kQ' in get.call_args[0][0]
            assert '/solr/bigquery' in post.call_args[0]
            x = post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ']
            assert x[2] == 'big-query/csv'


        data = {
            'query': json.dumps({'query': 'q=foo&hHGU1Ef-TpacAhicI3J8kQ=foo+bar',
                                 'bigquery': 'something'})
        }
        with mock.patch(self.app.client, 'get', return_value=din) as get, \
            mock.patch('solr.views.requests.post', return_value=out) as post:
            r = self.client.post(url_for('bigquery'),
                                 query_string={'q': 'docs(hHGU1Ef-TpacAhicI3J8kQ)'},
                                 headers={'Authorization': 'Bearer foo'})
            # it made a request to retrieve library
            get.assert_called()
            assert '/vault/query/hHGU1Ef-TpacAhicI3J8kQ' in get.call_args[0][0]
            assert '/solr/bigquery' in post.call_args[0]

            x = post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ']
            assert x[2] == 'big-query/csv'


        # we are sending another bigquery in data
        with mock.patch(self.app.client, 'get', return_value=din) as get, \
            mock.patch('solr.views.requests.post', return_value=out) as post:
            r = self.client.post(url_for('bigquery'),
                                 content_type='multipart/form-data',
                                 data={
                                     'q': '*:*',
                                     'fq': 'docs(hHGU1Ef-TpacAhicI3J8kQ)',
                                     'big': (BytesIO('foo\nbar'.encode('utf-8')), 'bigname', 'big-query/csv')
                                     },
                                 headers={'Authorization': 'Bearer foo'})
            # it made a request to retrieve library
            get.assert_called()
            assert '/vault/query/hHGU1Ef-TpacAhicI3J8kQ' in get.call_args[0][0]
            assert '/solr/bigquery' in post.call_args[0]

            assert post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ'][1] == 'foo bar'
            assert post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ'][2] == 'big-query/csv'

            assert post.call_args[1]['files']['big'][1].closed == True
            assert post.call_args[1]['files']['big'][2] == 'big-query/csv'


        # and also allowed for GET requests
        with mock.patch(self.app.client, 'get', return_value=din) as get, \
            mock.patch('solr.views.requests.post', return_value=out) as post:
            r = self.client.get(url_for('search'),
                                 query_string={'q': 'docs(hHGU1Ef-TpacAhicI3J8kQ)'},
                                 headers={'Authorization': 'Bearer foo'})
            # it made a request to retrieve library
            get.assert_called()
            assert '/vault/query/hHGU1Ef-TpacAhicI3J8kQ' in get.call_args[0][0]
            assert '/solr/bigquery' in post.call_args[0]

            assert post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ'][1] == 'foo bar'
            assert post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ'][2] == 'big-query/csv'

        # GET request with data in params
        with mock.patch(self.app.client, 'get', return_value=din) as get, \
            mock.patch('solr.views.requests.post', return_value=out) as post:
            r = self.client.get(url_for('search'),
                                 query_string={'q': 'docs(hHGU1Ef-TpacAhicI3J8kQ)',
                                               'hHGU1Ef-TpacAhicI3J8kQ': 'hey joe'},
                                 headers={'Authorization': 'Bearer foo'})
            # it made no request to retrieve library
            assert get.called == False
            assert post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ'][1] == 'hey joe'
            assert post.call_args[1]['files']['hHGU1Ef-TpacAhicI3J8kQ'][2] == 'big-query/csv'
            assert '/solr/bigquery' in post.call_args[0][0]



    def test_search(self):
        """
        Test the search endpoint
        """
        with MockSolrResponse(self.app.config['SOLR_SERVICE_SEARCH_HANDLER']):
            r = self.client.get(url_for('search'))
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
                   "The {0} response from {1}:\n\n{2}".format(
                       request.method, uri, request.body
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
                    'file_field': (BytesIO(bibcodes.encode('utf-8')), 'file', 'big-query/csv')
                }
        )

        self.assertEqual(resp.status_code, 200)

        # Missing 'fq' parameter is not filled
        resp = self.client.post(
                url_for('bigquery'),
                content_type='multipart/form-data',
                data={
                    'q': '*:*',
                    'fl': 'bibcode',
                    'file_field': (BytesIO(bibcodes.encode('utf-8')), 'filename', 'big-query/csv'),
                    }
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTrue('bitset' not in resp.data.decode('utf-8'))
        self.assertTrue("Content-Disposition: form-data; name=\"file_field\"; filename=\"file_field\"\\r\\nContent-Type: big-query/csv" in resp.data.decode('utf-8'))


        # Missing 'fq' parameter is filled in - but only when data (request.post(data=...)
        # is used (flask testing client is absolutely asinine api)
        resp = self.client.post(
                url_for('bigquery'),
                data=bibcodes,
                query_string='q=*:*&fl=bibcode'
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTrue('fq=%7B%21bitset%7D' in resp.data.decode('utf-8'))
        self.assertTrue("Content-Disposition: form-data; name=\"old-bad-behaviour\"; filename=\"old-bad-behaviour\"\\r\\nContent-Type: big-query/csv" in resp.data.decode('utf-8'))



        # 'fq' with additional params specified
        resp = self.client.post(
                url_for('bigquery'),
                content_type='multipart/form-data',
                data={
                    'q': '*:*',
                    'fl': 'bibcode',
                    'fq': '{!bitset compression = true}',
                    'file_field': (BytesIO(bibcodes.encode('utf-8')), 'filename', 'big-query/csv'),
                    }
        )

        self.assertEqual(resp.status_code, 200)
        self.assertTrue('fq=%7B%21bitset+compression+%3D+true%7D' in resp.data.decode('utf-8'))

        # We now allow more content streams to be sent
        data = MultiDict([
            ('q', '*:*'),
            ('fl', 'bibcode'),
            ('fq', '{!bitset}'),
            ('file_field', (BytesIO(bibcodes.encode('utf-8')), 'filename', 'big-query/csv')),
            ('file_field', (BytesIO(bibcodes.encode('utf-8')), 'filename', 'big-query/csv')),
        ])

        resp = self.client.post(
                url_for('bigquery'),
                content_type='multipart/form-data',
                data=data
        )

        self.assertEqual(resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()
