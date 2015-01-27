import sys, os
from urllib import urlencode
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
from flask.ext.testing import TestCase
from flask import url_for, request
import unittest
import json
import httpretty
import app
import cgi
from StringIO import StringIO

class TestWebservices(TestCase):
  '''Tests that each route is an http response'''
  

  def create_app(self):
    '''Start the wsgi application'''
    _app = app.create_app()
    return _app

  @httpretty.activate
  def test_sanitization(self):
    def request_callback(request, uri, headers):
        if 'fl' not in request.parsed_body:
            return (500, headers, "{'The query parameters were not passed properly'}")
            if 'title' not in request.parsed_body['fl']:
                return (500, headers, "{'The query parameters were not passed properly'}")
        if 'body' in request.parsed_body['fl']:
            return (500, headers, "{'The query was not sanitized properly'}")
        return (200, headers, "{\"msg\": \"The %s response from %s\"}" % (request.method, uri))

    httpretty.register_uri(
        httpretty.POST, self.app.config.get('SOLR_SEARCH_HANDLER'),
        body=request_callback)
    
    resp = self.client.get(url_for('solr.search'),
                data={'q': 'star', 'fl': 'body,title'})
    self.assertEqual(resp.status_code, 200)


  @httpretty.activate
  def test_search(self):
    httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_SEARCH_HANDLER'),
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

    r = self.client.get(url_for('solr.search'))
    self.assertStatus(r, 200)
    self.assertIn('responseHeader', r.json)
        
    
  @httpretty.activate
  def test_qtree(self):
    httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_QTREE_HANDLER'),
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

    r = self.client.get(url_for('solr.qtree'))
    self.assertEqual(r.status_code, 200)
    self.assertIn('qtree', r.json)
    self.assertIn('name', json.loads(r.json['qtree']))
    
    r = self.client.post(url_for('solr.tvrh'))
    self.assertStatus(r, 405)

      
  @httpretty.activate
  def test_tvrh(self):
    httpretty.register_uri(
            httpretty.POST, self.app.config.get('SOLR_TVRH_HANDLER'),
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
            """)

    resp = self.client.get(url_for('solr.tvrh'))
    self.assertEqual(resp.status_code, 200)
    self.assertIn('termVectors', resp.json)
    
  @httpretty.activate
  def test_bigquery(self):
    def request_callback(request, uri, headers):
        #form = cgi.FieldStorage(fp=request.rfile, headers=request.headers, environ=request.environ)
        if 'q' not in request.querystring:
            return (500, headers, "{'The query parameters were not passed properly'}")
        return (200, headers, "{\"msg\": \"The %s response from %s\"}" % (request.method, uri))

    httpretty.register_uri(
        httpretty.POST, self.app.config.get('SOLR_BIGQUERY_HANDLER'),
        body=request_callback)

    # this will work in real-life solr
    # r = requests.post('http://54.173.87.140:8983/solr/bigquery', params={'q':'*:*', 'wt':'json', 'fl':'bibcode', 'fq': '{!bitset}'}, headers={'content-type': 'big-query/csv'}, data=bibcodes); print r.text

    #requests.post('http://localhost:8983/solr/bigquery', params={'q':'*:*', 'wt':'json', 'fl':'bibcode'}, headers={'content-type': 'big-query/csv'}, data=bibcodes)
    bibcodes = 'bibcode\n1907AN....174...59.\n1908PA.....16..445.\n1989LNP...334..242S'
    resp = self.client.post(
            url_for('solr.bigquery'), 
            content_type='multipart/form-data', 
            data={'q' : '*:*',
                 'fl' : 'bibcode',
                 'fq' : '{!bitset}',
                 'file_field' : (StringIO(bibcodes), 'big-query/csv')})
    
    self.assertEqual(resp.status_code, 200)   
    
    resp = self.client.post(
            url_for('solr.bigquery'), 
            content_type='multipart/form-data', 
            data={'q' : '*:*',
                 'fl' : 'bibcode',
                 'file_field' : (StringIO(bibcodes), 'big-query/csv')})
    
    self.assertEqual(resp.status_code, 403)

if __name__ == '__main__':
  unittest.main()
