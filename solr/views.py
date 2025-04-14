from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import str
from past.builtins import basestring
from flask import current_app, request
from flask_restful import Resource
from flask_discoverer import advertise
try:
    from flask_login import current_user
except:
    # If solr service is not shipped with adsws, this will fail and it is ok
    pass
import json
from .models import Limits
from sqlalchemy import or_
from werkzeug.datastructures import MultiDict
from io import StringIO
from io import BytesIO
from urllib.parse import parse_qs

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
    handler = {'default': 'SOLR_SERVICE_URL', 'default_embedded_bigquery': 'SOLR_SERVICE_BIGQUERY_HANDLER'}

    def __init__(self, *args, **kwargs):
        Resource.__init__(self, *args, **kwargs)
        self._host = None
        self.internal_logging_params = {
            'X-Amzn-Trace-Id': 'Root=-',
        } # Pass to solr only for logging purposes, note that this will be returned back to the user by solr

    def get_handler_class(self):
        return "default"

    def get(self):
        query, headers = self.cleanup_solr_request(request.args.to_dict(flat=False))
        if current_app.config.get("SOLR_INJECT_QUERY_PARAMS", {}):
            injected_params = current_app.config.get("SOLR_INJECT_QUERY_PARAMS", {})
            query.update(injected_params)

        # trickery, we can accept docs() operator if it is part of form data
        # I tried to search whether it is a valid move to send multipart
        # data with GET request, but I didn't see anything suggesting it is
        # not possible; web clients/servers are probably dropping it
        # here is an example with curl; the first one will not contain the file

        # curl 'http://httpbin.org/get?foo=bar' --form file=@/tmp/foo --trace-ascii /dev/stdout -X GET
        # curl 'http://httpbin.org/post?foo=bar' --form file=@/tmp/foo --trace-ascii /dev/stdout -X POST

        # so I *think* this should be safe...

        handler_class = self.get_handler_class()
        files = self.check_for_embedded_bigquery(query, request, headers, handler_class=handler_class)
        if files and len(files): # must be directed to /bigquery
            handler_class += '_embedded_bigquery'
        handler = self.handler.get(handler_class, self.handler.get("default"))

        should_postprocess_response = False

        unhighlightable_publishers = current_app.config.get('SOLR_SERVICE_DISALLOWED_HIGHLIGHTS_PUBLISHERS', [])
        default_fields = current_app.config.get('SOLR_SERVICE_DEFAULT_FIELDS', [])

        if default_fields and handler == 'SOLR_SERVICE_SEARCH_HANDLER':
            if 'fl' not in query:
                query['fl'] = ",".join(default_fields)

            if unhighlightable_publishers and 'hl' in query:
                if 'publisher' not in query['fl']:
                    query['fl'] = query['fl'] + ',publisher'
                should_postprocess_response = True

        try:
            current_user_id = current_user.get_id()
        except:
            # If solr service is not shipped with adsws, this will fail and it is ok
            current_user_id = None


        if current_user_id:
            current_app.logger.info("Dispatching 'POST' request to endpoint '{}' for user '{}'".format(current_app.config[handler], current_user_id))
        else:
            current_app.logger.info("Dispatching 'POST' request to endpoint '{}'".format(current_app.config[handler]))
        if files and len(files): # must be directed to /bigquery
            r = requests.post(
                current_app.config[handler],
                params=query,
                headers=headers,
                files=files,
                cookies=SolrInterface.set_cookies(request),
            )
        else:
            r = requests.post(
                current_app.config[handler],
                data=query,
                headers=headers,
                cookies=SolrInterface.set_cookies(request),
            )
        current_app.logger.info("Received response from from endpoint '{}' with status code '{}'".format(current_app.config[handler], r.status_code))

        if should_postprocess_response and r.ok:
            try:
                response_data = r.json()
                unhighlightable_docs = []

                for doc in response_data['response']['docs']:
                    if 'publisher' not in doc:
                        continue

                    if type(doc['publisher']) is list:
                        for publisher in doc['publisher']:
                            if publisher.lower() in unhighlightable_publishers:
                                unhighlightable_docs.append(doc['id'])
                                break
                    else:
                        if doc['publisher'].lower() in unhighlightable_publishers:
                            unhighlightable_docs.append(doc['id'])

                for remove_doc in unhighlightable_docs:
                    if remove_doc in response_data['highlighting']:
                        doc_highlights = response_data['highlighting'][remove_doc]

                        for remove_key in ['body', 'ack']:
                            if remove_key in doc_highlights:
                                del doc_highlights[remove_key]

                response_data['filtered'] = 'true'

                return json.dumps(response_data), r.status_code, r.headers
            except Exception as e:
                current_app.logger.error(e.with_traceback())

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

    def apply_protective_filters(self, payload, user_id, protected_fields, key):
        """
        Adds filters to the query that should limit results to conditions
        that are associted with the user_id+protected_field. If a field is
        not found in the db of limits, it will not be returned to the user

        :param payload: raw request payload
        :param user_id: string, user id as known to ADS API
        :param protected_fields: list of strings, fields
        :param key: string, name of the field we are currently processing
            (typically 'fl', but could be 'anything.fl' when dealing
            with subrequests)
        """
        fl = payload.get(key, 'id')
        if key == 'fl':
            fq = payload.get('fq', [])
            fq_key = 'fq'
        else:
            prefix = key.rsplit('.', 1)[0]
            fq_key = '%s.fq' % (prefix)
            fq = payload.get(fq_key, [])


        if not isinstance(fq, list):
            fq = [fq]

        payload[fq_key] = fq

        with current_app.session_scope() as session:
            for f in session.query(Limits).filter(Limits.uid==user_id, or_(Limits.field==x for x in protected_fields)).all():
                if f.filter:
                    fl = u'{0},{1}'.format(fl, f.field)
                    fq.append(str(f.filter))
                    payload['fl'] = fl
            session.commit()

    def cleanup_solr_request(self, payload, user_id=None, handler_class="default"):
        """
        Sanitizes a request before it is passed to solr

        :param payload: dict, raw request payload. Warning: we'll
            modify the dictionary directly
        :kwarg user_id: string, identifying the user

        :return: tuple - (sanitized payload, headers for solr)
        """

        if not user_id:
            user_id = request.headers.get('X-api-uid', 'default')

        headers = {}
        _h = request.headers.get('Content-Type', 'application/x-www-form-urlencoded')
        if 'big-query' not in _h: # only let big-query headers pass unmolested
            _h = 'application/x-www-form-urlencoded'
        headers['Content-Type'] =  _h

        # trace id, Host, token header are important for proper routing/logging
        handler = self.handler.get(handler_class, self.handler.get("default", "-"))
        headers['Host'] = self.get_host(current_app.config.get(handler))
        internal_logging = []
        for internal_param, default in self.internal_logging_params.items():
            if internal_param in request.headers:
                internal_logging.append("{}={}".format(internal_param, request.headers[internal_param]))
                headers[internal_param] = request.headers[internal_param]
            else:
                # Make sure solr always reports the parameter to facilitate regex logging parsing
                internal_logging.append("{}={}".format(internal_param, default))

        payload['internal_logging_params'] = ";".join(internal_logging)
        payload['wt'] = 'json'


        # Ensure there is a single rows
        if 'rows' not in payload:
            payload['rows'] = current_app.config.get('SOLR_SERVICE_DEFAULT_ROWS', 10)

        # Ensure there is a single start value
        start = 0
        if 'start' in payload:
            start = _safe_int(payload['start'], default=0)
        payload['start'] = start

        # Ensure there is one fl value
        if 'fl' not in payload:
            payload['fl'] = 'id'

        # Amount of time, in milliseconds, allowed for a search to complete (incompatible with cursorMark)
        # - This value is only checked at the time of: Query Expansion, and Document collection
        if 'cursorMark' not in payload:
            time_allowed = current_app.config.get('SOLR_SERVICE_TIME_ALLOWED_MS')
            if time_allowed:
                payload['timeAllowed'] = time_allowed

        max_hl = current_app.config.get('SOLR_SERVICE_MAX_SNIPPETS', 4)
        max_frag = current_app.config.get('SOLR_SERVICE_MAX_FRAGSIZE', 200)

        # Highlight queries need to be limited per publisher agreements,
        # so inject the limit terms if they don't exist.
        if 'hl' in payload:
            if 'hl.maxHighlightCharacters' not in payload:
                payload['hl.maxHighlightCharacters'] = max_frag

        for k,v in list(payload.items()):
            if 'hl.' in k:
                if '.snippets' in k:
                    payload[k] = max(0, min(_safe_int(v, default=max_hl), max_hl))
                elif '.fragsize' in k:
                    payload[k] = max(1, min(_safe_int(v, default=max_frag), max_frag)) #0 would return whole field
                    payload['hl.maxHighlightCharacters'] = payload[k]
            if k == 'hl.fl':
                self._cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_HIGHLIGHTS_FIELDS'))
            if k == 'fl' or ('.fl' in k and k != 'hl.fl'):
                self._cleanup_fl(payload, user_id, k)
            if k == 'rows' or '.rows' in k:
                self._cleanup_rows(payload, user_id, k)
            if k == 'facet.field':
                self._cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_FACET_FIELDS'))
            if k == 'facet.pivot':
                self._cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_FACET_PIVOT'))
            if k == 'stats.field':
                self._cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_STATS_FIELDS'))
            if k == 'sort':
                self._cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_SORT_FIELDS'))

        return payload, headers

    def _cleanup_fields(self, payload, key, allowed_fields):
        """ Only allow certain fields """
        values = payload[key]
        if not isinstance(values, list):
            values = [values]

        fields = []
        for y in values:
            fields.extend([i.strip().lower() for i in y.split(',')])

        if allowed_fields:
            fields = [x for x in fields if x in allowed_fields]

        payload[key] = ','.join(fields)


    def _cleanup_rows(self, payload, user_id, key):
        """Ensure rows does not bypass the max rows limit"""
        value = payload[key]
        default_rows = current_app.config.get('SOLR_SERVICE_DEFAULT_ROWS', 10)
        max_rows = int(current_app.config.get('SOLR_SERVICE_MAX_ROWS', 100))
        payload[key] = min(_safe_int(value, default=default_rows), max_rows)

    def _cleanup_fl(self, payload, user_id, key):

        values = payload[key]

        if not isinstance(values, list):
            values = [values]

        fields = []
        for y in values:
            fields.extend([i.strip().lower() for i in y.split(',')])

        disallowed = current_app.config.get(
            'SOLR_SERVICE_DISALLOWED_FIELDS'
        )

        protected_fields = []
        if disallowed:
            protected_fields = [x for x in fields if x in disallowed]
            fields = [x for x in fields if x not in disallowed]

        if len(fields) == 0:
            fields.append('id')

        while '*' in fields:
            fields.pop(fields.index('*'))

        if len(fields) == 0:
            fields = current_app.config.get('SOLR_SERVICE_ALLOWED_FIELDS')

        payload[key] = ','.join(fields)

        if len(protected_fields) > 0:
            self.apply_protective_filters(payload, user_id, protected_fields, key)


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

    def _extract_docs_values(self, input):
        out = []
        i = 0
        while input.find('docs(', i) > -1:
            i = input.index('docs(', i) + 5
            j = i
            while input[j] != ')' and j < len(input):
                j += 1
            out.append(input[i:j])
            i = j + 1
        return out

    def check_for_embedded_bigquery(self, params, request, headers, handler_class="default"):
        """Checks for the presence of docs() query any where inside
        the query parameters; if present - we'll verify/update
        the query with data.

        This function can also be used to process bigquery request
        (i.e. no docs() operator is present)
        """
        streams = set()
        for k,v in params.items():
            if 'q' in k: # well, i was lying - we'll only check params that *could* be a query
                if isinstance(v, basestring):
                    if 'docs(' in v:
                        streams.update(self._extract_docs_values(v))
                else:
                    for x in v:
                        if 'docs(' in x:
                            streams.update(self._extract_docs_values(x))

        # old-hack, bigquery can be passed without specifying 'fq' parameter
        # we need to detect that situation and fill in the missing detail
        # this is only accepted if the data was passed in request.data
        # if user tried to send the data with anonymous request.fiel stream
        # they must set the appropriate headers
        if request.data and isinstance(request.data, basestring) and len(request.data) > 0:
            if 'fq' not in params:
                params['fq'] = [u'{!bitset}']
            elif isinstance(params['fq'], str) and '{!bitset}' not in params['fq']:
                params['fq'] += u' {!bitset}'
            elif isinstance(params['fq'], list) and len([x for x in params['fq'] if '!bitset' in x]) == 0:
                params['fq'].append(u'{!bitset}')

            # we'll package request.data into files
            streams.add('old-bad-behaviour')
            params['old-bad-behaviour'] = request.data


        # what is left is missing and we need to fill in the gaps
        files = self._get_stream_data(params, list(streams), request, handler_class=handler_class)

        # let requests library pick the appropriate ctype
        if len(files):
            del headers['Content-Type']

        return files

    def _get_stream_data(self, params, streams, request, handler_class="default"):
        # TODO: it seems natural that this functionality could live inside
        # myads; there we'd be not forced to query a remote service; however
        # I fear that is not really what people are asking for - they just
        # want any/all queries to work when we say foo AND docs(barxxxx)

        out = {}

        # must verify the input is not supplied and should be loaded
        for sn in streams:
            if sn in params: # it can be in the parameters, which is OK...
                x = params[sn]
                if isinstance(x, list) and len(x) > 0:
                    x = x[0]
                out[sn] = (sn, x, 'big-query/csv')
                streams.remove(sn)
                del params[sn]
            elif request.data and not isinstance(request.data, basestring) and sn in request.data: # if data is a dict...
                x = request.data[sn]
                if isinstance(x, list) and len(x) > 0:
                    x = x[0]
                out[sn] = (sn, x, 'big-query/csv')
                streams.remove(sn)
            elif request.files and sn in request.files:
                f = request.files[sn]
                out[sn] = (f.name, f.stream, f.mimetype)
                streams.remove(sn)


        for s in streams:
            if '/' in s:
                prefix, value = s.split('/', 1)
            else:
                prefix = ''
                value = s

            new_headers = {'Authorization': request.headers['Authorization']}
            if 'X-Forwarded-Authorization' in request.headers:
                new_headers['X-Forwarded-Authorization'] = request.headers['X-Forwarded-Authorization']
            # trace id, Host, token header are important for proper routing/logging
            handler = self.handler.get(handler_class, self.handler.get("default", "-"))
            new_headers['Host'] = self.get_host(current_app.config.get(handler))
            for internal_param in self.internal_logging_params.keys():
                if internal_param in request.headers:
                    new_headers[internal_param] = request.headers[internal_param]

            docs = None

            if prefix == 'library':
                q = self._harvest_library(value, new_headers)
                docs = 'bibcode\n' + '\n'.join(q['documents'])

            else:
                r = current_app.client.get(current_app.config['VAULT_ENDPOINT'] + '/' + value,
                                           headers=new_headers)
                r.raise_for_status()

                # json serialized dictionary with two keys, 'query' and 'bigquery'
                # their values are strings (for query urlencoded parameters)
                q = json.loads(r.json()['query'])
                try:
                    params = parse_qs(q['query'])
                except:
                    params = {}

                if value in params: # it is encoded in parameters
                    docs = params[value]
                    if isinstance(docs, list): # urlparsing can do that
                        docs = docs[0]
                elif 'bigquery' in q and q['bigquery']: # this query has a bigquery, so it must be that
                    docs = q['bigquery']
                else:
                    raise Exception('Query relies on {} however such queryid is not available via API'.format(s))

            out[s] = (s, docs, "big-query/csv")

        # copy over remaining files
        for k,v in request.files.items():
            if k not in out:
                out[k] = (v.name, v.stream, v.mimetype)
        return out

    def _harvest_library(self, library_id, headers):
        """I looked inside the impl of the biblib/libraries
        and unfortunately it is quite expensive; not only does
        it make (automatic) bigquery to verify bibcodes with
        every request; it also loads *every time* set of all
        bibcodes, even if it only returns section of it -
        we would really do better if there existed an endpoint
        that just returns all bibcodes saved in the library"""


        maxr = current_app.config.get('BIBLIB_MAX_ROWS', 2000)
        params = {'rows': maxr, 'start': 0}
        out = {'documents': set(), 'library': library_id}
        while True:
            r = current_app.client.get(current_app.config['LIBRARY_ENDPOINT'] + '/' + library_id,
                                       params=params,
                                       headers=headers)
            r.raise_for_status()

            q = r.json()
            oldcount = len(out['documents'])
            out['documents'].update(q['documents'])
            out['metadata'] = q['metadata']

            # all of these conditions because biblib doesn't guarantee stable sort order, sigh...
            if 'num_documents' in out['metadata'] and out['metadata']['num_documents'] <= len(out['documents']) or \
                len(q['documents']) < maxr or \
                oldcount == len(out['documents']) or \
                len(q['documents']) == 0:
                break

            params['start'] = params['start'] + maxr

        return out


class Tvrh(SolrInterface):
    """Exposes the solr term-vector histogram endpoint"""
    scopes = []
    rate_limit = [500, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = {'default': 'SOLR_SERVICE_TVRH_HANDLER'}

class Search(SolrInterface):
    """Exposes the solr select endpoint"""
    scopes = []
    rate_limit = [5000, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = {'default': 'SOLR_SERVICE_SEARCH_HANDLER',
               'default_embedded_bigquery': 'SOLR_SERVICE_BIGQUERY_HANDLER',
               'bot': 'BOT_SOLR_SERVICE_SEARCH_HANDLER',
               'bot_embedded_bigquery': 'BOT_SOLR_SERVICE_BIGQUERY_HANDLER'}

    def get_handler_class(self):
        """Identify bot requests based on their authentication token"""
        forwarded_authorization = request.headers.get('X-Forwarded-Authorization', [])
        if forwarded_authorization and len(forwarded_authorization) > 7:
            request_token = forwarded_authorization[7:]
        else:
            request_token = request.headers.get('Authorization', [])[7:]
        if request_token in current_app.config.get('BOT_TOKENS', []):
            return "bot"
        else:
            return "default"

class Qtree(SolrInterface):
    """Exposes the qtree endpoint"""
    scopes = []
    rate_limit = [500, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = {'default': 'SOLR_SERVICE_QTREE_HANDLER'}


class BigQuery(SolrInterface):
    """Exposes the bigquery endpoint"""
    scopes = ['api']
    rate_limit = [100, 60*60*24]
    decorators = [advertise('scopes', 'rate_limit')]
    handler = {'default': 'SOLR_SERVICE_BIGQUERY_HANDLER',
               'default_embedded_bigquery': 'SOLR_SERVICE_BIGQUERY_HANDLER',
               'bot': 'BOT_SOLR_SERVICE_BIGQUERY_HANDLER',
               'bot_embedded_bigquery': 'BOT_SOLR_SERVICE_BIGQUERY_HANDLER'}

    def get_handler_class(self):
        """Identify bot requests based on their authentication token"""
        forwarded_authorization = request.headers.get('X-Forwarded-Authorization', [])
        if forwarded_authorization and len(forwarded_authorization) > 7:
            request_token = forwarded_authorization[7:]
        else:
            request_token = request.headers.get('Authorization', [])[7:]
        if request_token in current_app.config.get('BOT_TOKENS', []):
            return "bot"
        else:
            return "default"

    def post(self):
        handler_class = self.get_handler_class()
        payload = request.form.to_dict(flat=False)
        payload.update(request.args.to_dict(flat=False))
        if request.is_json:
            payload.update(request.json)

        query, headers = self.cleanup_solr_request(payload)
        files = self.check_for_embedded_bigquery(query, request, headers, handler_class=handler_class)

        if files and len(files) > 0:
            try:
                current_user_id = current_user.get_id()
            except:
                # If solr service is not shipped with adsws, this will fail and it is ok
                current_user_id = None
            if current_user_id:
                current_app.logger.info("Dispatching 'POST' request to endpoint '{}' for user '{}'".format(current_app.config[self.handler[handler_class]], current_user_id))
            else:
                current_app.logger.info("Dispatching 'POST' request to endpoint '{}'".format(current_app.config[self.handler[handler_class]]))
            r = requests.post(
                current_app.config[self.handler[handler_class]],
                params=query,
                headers=headers,
                files=files,
                cookies=SolrInterface.set_cookies(request),
            )
            current_app.logger.info("Received response from endpoint '{}' with status code '{}'".format(current_app.config[self.handler[handler_class]], r.status_code))
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


class ClosingTuple(tuple):
    """The sole raison d'etre of this class is to accommodate
    Flask which wants to call close() on anything inside
    request.files; and to allow requests to use files
    as (name, fileobj, mimetype)"""
    def close(self):
        for x in self:
            if hasattr(x, 'close'):
                x.close()

