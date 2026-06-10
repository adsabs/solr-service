from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import str
from flask import current_app, request
from flask_restful import Resource
from flask_discoverer import advertise
try:
    from flask_login import current_user
except ImportError:
    # If solr service is not shipped with adsws, this will fail and it is ok
    pass
import json
from . import sanitize
from . import middleware
from . import bigquery
from . import transport
from . import handlers
from . import postprocess as _postprocess
from .postprocess import apply_highlight_window as _apply_highlight_window
from .transport import parse_host as _parse_host
from .bigquery import extract_docs_values as _extract_docs_values
from typing import List

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

    @staticmethod
    def _current_user_id():
        """Best-effort user id for logging: flask_login when shipped with adsws,
        otherwise the X-api-uid header."""
        try:
            return current_user.get_id()
        except:
            # If solr service is not shipped with adsws, this will fail and it is ok
            return request.headers.get("X-api-uid", None)

    def get(self):
        query, headers = self.cleanup_solr_request(request.args.to_dict(flat=False))

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
        handler = handlers.resolve_handler_key(self.handler, handler_class)

        ctx = middleware.Context(
            query, headers, request, current_app.config,
            handler_class=handler_class, handler_key=handler, files=files,
        )
        middleware.run_preprocess(ctx)

        current_user_id = self._current_user_id()
        current_app.logger.info("Dispatching 'POST' request to endpoint '{}' for user '{}'".format(current_app.config[self.handler[handler_class]], current_user_id or "anonymous"))

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

        ctx.response = r
        return middleware.run_postprocess(ctx)

    def postprocess_response(self, r: requests.Response) -> dict:
        return _postprocess.postprocess_response(r.json(), current_app.config)

    def apply_highlight_window(self, highlight_text: str, max_len: int) -> List[str]:
        return _apply_highlight_window(highlight_text, max_len)

    @staticmethod
    def set_cookies(request):
        """
        Picks out the cookies from the current flask.request context with
        a name in `SOLR_SERVICE_FORWARDED_COOKIES`
        :param request: current flask.request
        :return: the single cookie with the cookie_name or None
        :rtype dict or None
        """
        return transport.select_cookies(request, current_app.config)

    def cleanup_solr_request(self, payload, user_id=None, handler_class="default"):
        """
        Sanitizes a request before it is passed to solr. Thin wrapper that binds
        this resource's handler map / logging params to the policy in
        :mod:`solr.sanitize`.

        :param payload: dict, raw request payload (modified in place)
        :kwarg user_id: string, identifying the user

        :return: tuple - (sanitized payload, headers for solr)
        """
        return sanitize.cleanup_solr_request(
            payload, request, self.handler,
            handler_class=handler_class,
            internal_logging_params=self.internal_logging_params,
            user_id=user_id,
        )


    def _get_host(self, url):
        self._host = _parse_host(url)
        return self._host

    def _extract_docs_values(self, input):
        return _extract_docs_values(input)

    def check_for_embedded_bigquery(self, params, request, headers, handler_class="default"):
        """Resolve any embedded bigquery (docs() operators or raw bigquery data)
        into multipart files. Thin wrapper binding this resource's handler map /
        logging params to the logic in :mod:`solr.bigquery`."""
        return bigquery.check_for_embedded_bigquery(
            params, request, headers, self.handler,
            handler_class=handler_class,
            internal_logging_params=self.internal_logging_params,
        )

    def _harvest_library(self, library_id, headers):
        return bigquery._harvest_library(library_id, headers)


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
               'bot_embedded_bigquery': 'BOT_SOLR_SERVICE_BIGQUERY_HANDLER',
               'anonymous': 'ANONYMOUS_SOLR_SERVICE_SEARCH_HANDLER',
               'anonymous_embedded_bigquery': 'ANONYMOUS_SOLR_SERVICE_BIGQUERY_HANDLER'}

    def get_handler_class(self):
        return handlers.classify_request()

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
               'bot_embedded_bigquery': 'BOT_SOLR_SERVICE_BIGQUERY_HANDLER',
               'anonymous': 'ANONYMOUS_SOLR_SERVICE_BIGQUERY_HANDLER',
               'anonymous_embedded_bigquery': 'ANONYMOUS_SOLR_SERVICE_BIGQUERY_HANDLER'}

    def get_handler_class(self):
        return handlers.classify_request()

    def post(self):
        handler_class = self.get_handler_class()
        payload = request.form.to_dict(flat=False)
        payload.update(request.args.to_dict(flat=False))
        if request.is_json:
            payload.update(request.json)

        query, headers = self.cleanup_solr_request(payload)
        files = self.check_for_embedded_bigquery(query, request, headers, handler_class=handler_class)

        if files and len(files) > 0:
            current_user_id = self._current_user_id()
            current_app.logger.info("Dispatching 'POST' request to endpoint '{}' for user '{}'".format(current_app.config[self.handler[handler_class]], current_user_id or "anonymous"))
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

