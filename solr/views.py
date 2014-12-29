from flask import current_app, Blueprint, request
from flask.ext.restful import Resource
import inspect
import sys
from urllib import urlencode
import urlparse
from client import Client

client = Client(None,send_oauth2_token=False)

blueprint = Blueprint(
    'solr',
    __name__,
    static_folder=None,
)

class StatusView(Resource):
  '''Returns the status of this app'''
  scopes = []
  rate_limit = [1000,60*60*24]
  def get(self):
    return {'app':current_app.name,'status': 'online'}, 200

class Resources(Resource):
  '''Overview of available resources'''
  scopes = []
  rate_limit = [1000,60*60*24]
  def get(self):
    func_list = {}
    clsmembers = [i[1] for i in inspect.getmembers(sys.modules[__name__], inspect.isclass)]
    for rule in current_app.url_map.iter_rules():
      f = current_app.view_functions[rule.endpoint]
      #If we load this webservice as a module, we can't guarantee that current_app only has these views
      if not hasattr(f,'view_class') or f.view_class not in clsmembers:
        continue
      print rule.rule
      methods = f.view_class.methods
      scopes = f.view_class.scopes
      rate_limit = f.view_class.rate_limit
      description = f.view_class.__doc__
      func_list[rule.rule] = {'methods':methods,'scopes': scopes,'description': description,'rate_limit':rate_limit}
    print func_list
    return func_list, 200

class SolrInterface(Resource):
  '''Base class that responsible for forwarding a query to Solr'''

  def get(self):
    query = SolrInterface.cleanup_solr_request(dict(request.args))
    r = client.session.get(current_app.config[self.handler],
      params=urlencode(query, doseq=True))
    return r.json()

  def post(self):
    query = SolrInterface.cleanup_solr_request(urlparse.parse_qs(request.data))
    r = client.session.post(current_app.config[self.handler], 
      data=urlencode(query, doseq=True))
    return r.json()

  @staticmethod
  def cleanup_solr_request(payload,disallowed=['body','full']):
    payload['wt'] = 'json'
    # we disallow 'return everything'
    if 'fl' not in payload:
        payload['fl'] = 'id'
    else:
        fields = payload['fl'][0].split(',')
        if disallowed:
            fields = filter(lambda x: x not in disallowed, fields)
        if len(fields) == 0:
            fields.append('id')
        payload['fl'][0] = ','.join(fields)
    return payload
 

class Tvrh(SolrInterface):
  '''Exposes the solr term-vector histogram endpoint'''
  scopes = ['ads:default']
  rate_limit = [100,60*60*24]
  handler = 'SOLR_TVRH_HANDLER'

class Search(SolrInterface):
  '''Exposes the solr select endpoint'''
  scopes = ['ads:default']
  rate_limit = [100,60*60*24]
  handler = 'SOLR_SEARCH_HANDLER'

class Qtree(SolrInterface):
  '''Exposes the qtree endpoint'''
  scopes = ['ads:default']
  rate_limit = [100,60*60*24]
  handler = 'SOLR_QTREE_HANDLER'
