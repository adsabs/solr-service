from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()

from flask import current_app, request


def classify_request():
    """Classify the inbound request into a handler class used to pick the Solr
    backend: ``bot`` (recognised service token), ``anonymous`` (the shared
    anonymous uid), or ``default`` (an authenticated user).

    The bearer token is read from ``X-Forwarded-Authorization`` when present,
    otherwise ``Authorization`` (dropping the ``Bearer `` prefix via ``[7:]``).
    """
    forwarded_authorization = request.headers.get('X-Forwarded-Authorization', [])
    if forwarded_authorization and len(forwarded_authorization) > 7:
        request_token = forwarded_authorization[7:]
    else:
        request_token = request.headers.get('Authorization', [])[7:]
    if request_token in current_app.config.get('BOT_TOKENS', []):
        return "bot"
    elif int(request.headers.get("X-api-uid", 0)) == 1:
        return "anonymous"
    else:
        return "default"


def resolve_handler_key(handler_map, handler_class):
    """Resolve a handler class to the config key for its Solr url, falling back
    to the ``default`` handler when the class is not in the map."""
    return handler_map.get(handler_class, handler_map.get("default"))
