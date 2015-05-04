from flask import current_app, request
from flask.ext.restful import Resource
import inspect
import sys
import json
import requests


class StatusView(Resource):
    """Returns the status of this app"""
    scopes = []
    rate_limit = [1000,60*60*24]

    def get(self):
        return {'app': current_app.name, 'status': 'online'}, 200


class Resources(Resource):
    """Overview of available resources"""
    scopes = []
    rate_limit = [100, 60*60*24]

    def get(self):
        func_list = {}
        clsmembers = [i[1] for i in inspect.getmembers(sys.modules[__name__], inspect.isclass)]
        for rule in current_app.url_map.iter_rules():
            f = current_app.view_functions[rule.endpoint]
            # If we load this webservice as a module, we can't guarantee that
            # current_app only has these views
            if not hasattr(f, 'view_class') or f.view_class not in clsmembers:
                continue
            methods = f.view_class.methods
            scopes = f.view_class.scopes
            rate_limit = f.view_class.rate_limit
            description = f.view_class.__doc__
            func_list[rule.rule] = {'methods': methods,
                                    'scopes': scopes,
                                    'description': description,
                                    'rate_limit': rate_limit
                                    }
        return func_list, 200


class SolrInterface(Resource):
    """Base class that responsible for forwarding a query to Solr"""

    def get(self):
        query = SolrInterface.cleanup_solr_request(dict(request.args))
        headers = dict()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        r = requests.post(
            current_app.config[self.handler],
            data=query,
            headers=headers,
            cookies=SolrInterface.set_cookies(request),
        )
        return r.text, r.status_code, r.headers

    @staticmethod
    def set_cookies(request):
        """
        Picks out a single cookie from the current flask.request context with
        the name `SOLR_SERVICE_FORWARD_COOKIE_NAME`
        :param request: current flask.request
        :return: the single cookie with the cookie_name or None
        :rtype dict or None
        """
        cookie_name = current_app.config.get('SOLR_SERVICE_FORWARD_COOKIE_NAME')
        cookie = {cookie_name: request.cookies.get(cookie_name, 'session')}
        return cookie if cookie[cookie_name] else None

    @staticmethod
    def cleanup_solr_request(payload, disallowed=['body', 'full']):
        """
        Sanitizes a request before it is passed to solr
        :param payload: raw request payload
        :param disallowed: disallowed fields
        :return: sanitized payload
        """
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
    """Exposes the solr term-vector histogram endpoint"""
    scopes = []
    rate_limit = [500, 60*60*24]
    handler = 'SOLR_SERVICE_TVRH_HANDLER'


class Search(SolrInterface):
    """Exposes the solr select endpoint"""
    scopes = []
    rate_limit = [5000, 60*60*24]
    handler = 'SOLR_SERVICE_SEARCH_HANDLER'


class Qtree(SolrInterface):
    """Exposes the qtree endpoint"""
    scopes = []
    rate_limit = [500, 60*60*24]
    handler = 'SOLR_SERVICE_QTREE_HANDLER'


class BigQuery(Resource):
    """Exposes the bigquery endpoint"""
    scopes = ['api']
    rate_limit = [100, 60*60*24]
    handler = 'SOLR_SERVICE_BIGQUERY_HANDLER'
    
    def post(self):
        payload = dict(request.form)
        payload.update(request.args)
        headers = dict(request.headers)
        
        query = SolrInterface.cleanup_solr_request(payload)
        if 'fq' not in query or \
                len(filter(lambda x: '!bitset' in x, query['fq'])) == 0:
            return json.dumps({'error': "Missing fq={!bitset}"}), 400

        if 'big-query' not in headers.get('Content-Type', ''):
            headers['Content-Type'] = 'big-query/csv'
                        
        if request.data:
            r = requests.post(
                current_app.config[self.handler],
                params=query,
                data=request.data,
                headers=headers,
                cookies=SolrInterface.set_cookies(request),
            )
        elif request.files:
            r = requests.post(
                current_app.config[self.handler],
                params=query,
                headers=headers,
                files=request.files,
                cookies=SolrInterface.set_cookies(request),
            )
        else:
            return json.dumps({'error': "malformed request"}), 400
        return r.text, r.status_code, r.headers
