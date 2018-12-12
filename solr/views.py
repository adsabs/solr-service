from flask import current_app, request
from flask.ext.restful import Resource
from flask.ext.discoverer import advertise
import json
from models import Limits
from sqlalchemy import or_
import requests # Do not use current_app.client but requests, to avoid re-using
                # connections from a pool which would make solr ingress nginx
                # not set cookies with the affinity hash sroute

class StatusView(Resource):
    """Returns the status of this app"""
    scopes = []
    rate_limit = [1000, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]

    def get(self):
        return {'app': current_app.name, 'status': 'online'}, 200


class SolrInterface(Resource):
    """Base class that responsible for forwarding a query to Solr"""
    handler = 'SOLR_SERVICE_URL'

    def __init__(self, *args, **kwargs):
        Resource.__init__(self, *args, **kwargs)
        self._host = None

    def get(self):
        query, headers = self.cleanup_solr_request(dict(request.args))

        current_app.logger.info("Dispatching 'POST' request to endpoint '{}'".format(current_app.config[self.handler]))
        r = requests.post(
            current_app.config[self.handler],
            data=query,
            headers=headers,
            cookies=SolrInterface.set_cookies(request),
        )
        current_app.logger.info("Received response from from endpoint '{}' with status code '{}'".format(current_app.config[self.handler], r.status_code))
        return r.text, r.status_code, r.headers

    @staticmethod
    def set_cookies(request):
        """
        Picks out the cookies from the current flask.request context with
        a name in `SOLR_SERVICE_FORWARDED_COOKIES`
        :param request: current flask.request
        :return: the single cookie with the cookie_name or None
        :rtype dict or None
        """
        cookie_names = current_app.config.get('SOLR_SERVICE_FORWARDED_COOKIES', {})
        cookie = {}
        for cookie_name in cookie_names:
            value = request.cookies.get(cookie_name, None)
            if value:
                cookie[cookie_name] = value
        if cookie:
            return cookie
        else:
            return None

    def apply_protective_filters(self, payload, user_id, protected_fields):
        """
        Adds filters to the query that should limit results to conditions
        that are associted with the user_id+protected_field. If a field is
        not found in the db of limits, it will not be returned to the user

        :param payload: raw request payload
        :param user_id: string, user id as known to ADS API
        :param protected_fields: list of strings, fields
        """
        fl = payload.get('fl', 'id')
        fq = payload.get('fq', [])
        if not isinstance(fq, list):
            fq = [fq]
        payload['fq'] = fq

        with current_app.session_scope() as session:
            for f in session.query(Limits).filter(Limits.uid==user_id, or_(Limits.field==x for x in protected_fields)).all():
                if f.filter:
                    fl = u'{0},{1}'.format(fl, f.field)
                    fq.append(unicode(f.filter))
                    payload['fl'] = fl
            session.commit()


    def cleanup_solr_request(self, payload, user_id=None):
        """
        Sanitizes a request before it is passed to solr

        :param payload: dict, raw request payload. Warning: we'll
            modify the dictionary directly
        :kwarg user_id: string, identifying the user

        :return: tuple - (sanitized payload, headers for solr)
        """

        if not user_id:
            user_id = request.headers.get('X-Adsws-Uid', 'default')

        headers = {}
        _h = request.headers.get('Content-Type', 'application/x-www-form-urlencoded')
        if 'big-query' not in _h: # only let big-query headers pass unmolested
            _h = 'application/x-www-form-urlencoded'
        headers['Content-Type'] =  _h

        # trace id and Host header are important for proper routing/logging
        headers['Host'] = self.get_host(current_app.config.get(self.handler))

        if 'X-Amzn-Trace-Id' in request.headers:
            payload['x-amzn-trace-id'] = request.headers['X-Amzn-Trace-Id']
        elif 'x-amzn-trace-id' in request.headers:
            payload['x-amzn-trace-id'] = request.headers['x-amzn-trace-id']

        payload['wt'] = 'json'
        max_rows = current_app.config.get('SOLR_SERVICE_MAX_ROWS', 100)
        max_rows *= float(
            request.headers.get('X-Adsws-Ratelimit-Level', 1.0)
        )
        max_rows = int(max_rows)


        # Ensure there is a single rows value and that it does not bypass the max rows limit
        rows = current_app.config.get('SOLR_SERVICE_DEFAULT_ROWS', 10)
        if 'rows' in payload:
            rows = _safe_int(payload['rows'], default=max_rows)
        rows = min(rows, max_rows)
        payload['rows'] = rows

        # Ensure there is a single start value
        start = 0
        if 'start' in payload:
            start = _safe_int(payload['start'], default=0)
        payload['start'] = start

        # we disallow 'return everything'
        if 'fl' not in payload:
            payload['fl'] = 'id'
        else:
            fields = []
            for y in payload['fl']:
                fields.extend([i.strip().lower() for i in y.split(',')])

            disallowed = current_app.config.get(
                'SOLR_SERVICE_DISALLOWED_FIELDS'
            )

            protected_fields = []
            if disallowed:
                protected_fields = filter(lambda x: x in disallowed, fields)
                fields = filter(lambda x: x not in disallowed, fields)

            if len(fields) == 0:
                fields.append('id')
            if '*' in fields:
                fields = current_app.config.get('SOLR_SERVICE_ALLOWED_FIELDS')
            payload['fl'] = ','.join(fields)

            if len(protected_fields) > 0:
                self.apply_protective_filters(payload, user_id, protected_fields)

        max_hl = current_app.config.get('SOLR_SERVICE_MAX_SNIPPETS', 4)
        max_frag = current_app.config.get('SOLR_SERVICE_MAX_FRAGSIZE', 100)
        for k,v in payload.items():
            if 'hl.' in k:
                if '.snippets' in k:
                    payload[k] = max(0, min(_safe_int(v, default=max_hl), max_hl))
                elif '.fragsize' in k:
                    payload[k] = max(1, min(_safe_int(v, default=max_frag), max_frag)) #0 would return whole field

        return payload, headers

    def get_host(self, url):
        """Just extracts the host from the url."""
        return self._host or self._get_host(url)

    def _get_host(self, url):
        parts = url.split('/')
        if 'http' in parts[0].lower():
            self._host = parts[2]
        else:
            self._host = parts[0]
        return self._host

class Tvrh(SolrInterface):
    """Exposes the solr term-vector histogram endpoint"""
    scopes = []
    rate_limit = [500, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = 'SOLR_SERVICE_TVRH_HANDLER'


class Search(SolrInterface):
    """Exposes the solr select endpoint"""
    scopes = []
    rate_limit = [5000, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = 'SOLR_SERVICE_SEARCH_HANDLER'


class Qtree(SolrInterface):
    """Exposes the qtree endpoint"""
    scopes = []
    rate_limit = [500, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = 'SOLR_SERVICE_QTREE_HANDLER'


class BigQuery(SolrInterface):
    """Exposes the bigquery endpoint"""
    scopes = ['api']
    rate_limit = [100, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = 'SOLR_SERVICE_BIGQUERY_HANDLER'

    def post(self):
        payload = dict(request.form)
        payload.update(request.args)

        query, headers = self.cleanup_solr_request(payload)

        if request.files and \
                sum([len(i) for i in request.files.listvalues()]) > 1:
            message = "You can only pass one content stream."
            current_app.logger.error(message)
            return json.dumps(
                {'error': message}), 400

        if 'fq' not in query:
            query['fq'] = [u'{!bitset}']
        elif len(filter(lambda x: '!bitset' in x, query['fq'])) == 0:
            query['fq'].append(u'{!bitset}')

        if 'big-query' not in headers.get('Content-Type', ''):
            headers['Content-Type'] = 'big-query/csv'

        if request.data:
            current_app.logger.info("Dispatching 'POST' request to endpoint '{}'".format(current_app.config[self.handler]))
            r = requests.post(
                current_app.config[self.handler],
                params=query,
                data=request.data,
                headers=headers,
                cookies=SolrInterface.set_cookies(request),
            )
            current_app.logger.info("Received response from endpoint '{}' with status code '{}'".format(current_app.config[self.handler], r.status_code))
        elif request.files:
            current_app.logger.info("Dispatching 'POST' request to endpoint '{}'".format(current_app.config[self.handler]))
            r = requests.post(
                current_app.config[self.handler],
                params=query,
                headers=headers,
                files=request.files,
                cookies=SolrInterface.set_cookies(request),
            )
            current_app.logger.info("Received response from endpoint '{}' with status code '{}'".format(current_app.config[self.handler], r.status_code))
        else:
            message = "Malformed request"
            current_app.logger.error(message)
            return json.dumps({'error': message}), 400
        return r.text, r.status_code, r.headers


def _safe_int(val, default=0):
    if isinstance(val, (list, tuple)):
        val = val[0]
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
