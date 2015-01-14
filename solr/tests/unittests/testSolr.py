import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__),'../../'))
sys.path.append(PROJECT_HOME)
from flask.ext.testing import TestCase
from flask import url_for, request
import unittest
import json
import httpretty
import app

class TestWebservices(TestCase):
  '''Tests that each route is an http response'''
  
  def tearDown(self):
    httpretty.disable()
    httpretty.reset()

  def setUp(self):
    def request_callback(request, uri, headers):
      headers.update({"content-type":"application/json"})
      if request.method=='GET':
        fl = request.querystring['fl']
      elif request.method=='POST':
        fl = request.parsed_body['fl']
      if 'body' in fl:
        return (400, headers, "{'The query was not sanitized properly'}")
      else:
        return (200, headers, '''{
          "responseHeader(search)":{
          "status":0, "QTime":0,
          "params":{ "fl":"title,bibcode", "indent":"true", "wt":"json", "q":"*:*"}},
          "response":{"numFound":10456930,"start":0,"docs":[
            { "bibcode":"2005JGRC..110.4002G" },
            { "bibcode":"2005JGRC..110.4003N" },
            { "bibcode":"2005JGRC..110.4004Y" }]}}''')

    httpretty.enable()
    for method in [httpretty.GET,httpretty.POST]:
      httpretty.register_uri(
        method, 
        self.app.config.get('SOLR_SEARCH_HANDLER'),
        body=request_callback
      )
      httpretty.register_uri(
        method, 
        self.app.config.get('SOLR_QTREE_HANDLER'),
        content_type='application/json',
        status=200,
        body="""{"foo": "bar"}"""
      )
      httpretty.register_uri(
        method, 
        self.app.config.get('SOLR_TVRH_HANDLER'),
        content_type='application/json',
        status=200,
        body="""{"responseHeader(tvrh)":{"status":0,"QTime":179},"response":{"numFound":0,"start":0,"docs":[]}}"""
      )

  def create_app(self):
    '''Start the wsgi application'''
    _app = app.create_app()
    return _app

  def test_sanitization(self):
    r = self.client.get(
      url_for('solr.search'),
      data={'q': 'star', 'fl': 'body,title'}
    )
    self.assertStatus(r, 200)
    self.assertIn('responseHeader(search)',json.loads(r.data))
      
  def test_search(self):
    r = self.client.get(url_for('solr.search'))
    self.assertStatus(r, 200)
    self.assertIn('responseHeader(search)',json.loads(r.data))

    r = self.client.post(url_for('solr.search'))
    self.assertStatus(r, 200)
    self.assertIn('responseHeader(search)',json.loads(r.data))

  def test_qtree(self):
    r = self.client.get(url_for('solr.qtree'))
    self.assertStatus(r, 200)
    self.assertIn('foo',json.loads(r.data))

    r = self.client.post(url_for('solr.qtree'))
    self.assertStatus(r, 200)
    self.assertIn('foo',json.loads(r.data))
      
  def test_tvrh(self):
    r = self.client.get(url_for('solr.tvrh'))
    self.assertStatus(r, 200)
    self.assertIn('responseHeader(tvrh)',json.loads(r.data))

    r = self.client.post(url_for('solr.tvrh'))
    self.assertStatus(r, 200)
    self.assertIn('responseHeader(tvrh)',json.loads(r.data))

if __name__ == '__main__':
  unittest.main()
