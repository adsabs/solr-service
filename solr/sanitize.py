from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import str
from flask import current_app
from sqlalchemy import or_

from .models import Limits
from ._compat import safe_int
from .transport import parse_host


def apply_protective_filters(payload, user_id, protected_fields, key):
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


def cleanup_solr_request(payload, request, handler_map, handler_class="default",
                         internal_logging_params=None, user_id=None):
    """
    Sanitizes a request before it is passed to solr

    :param payload: dict, raw request payload. Warning: we'll
        modify the dictionary directly
    :param request: the current flask.request
    :param handler_map: dict mapping handler_class -> config key for the solr url
    :param handler_class: string, which handler the request is bound for
    :param internal_logging_params: dict of header name -> default, forwarded to solr
    :kwarg user_id: string, identifying the user

    :return: tuple - (sanitized payload, headers for solr)
    """
    internal_logging_params = internal_logging_params or {}

    if not user_id:
        user_id = request.headers.get('X-Adsws-Uid', 'default')
        if user_id == 'default':
            user_id = request.headers.get('X-api-uid', 'default')

    headers = {}
    _h = request.headers.get('Content-Type', 'application/x-www-form-urlencoded')
    if 'big-query' not in _h: # only let big-query headers pass unmolested
        _h = 'application/x-www-form-urlencoded'
    headers['Content-Type'] =  _h

    # trace id, Host, token header are important for proper routing/logging
    handler = handler_map.get(handler_class, handler_map.get("default", "-"))
    headers['Host'] = parse_host(current_app.config.get(handler))
    internal_logging = []
    for internal_param, default in internal_logging_params.items():
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
        start = safe_int(payload['start'], default=0)
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
    max_frag = current_app.config.get('SOLR_SERVICE_MAX_FRAGSIZE', 200)*4

    # Highlight queries need to be limited per publisher agreements,
    # so inject the limit terms if they don't exist.
    if 'hl' in payload:
        if 'hl.maxHighlightCharacters' not in payload:
            payload['hl.maxHighlightCharacters'] = max_frag

    for k,v in list(payload.items()):
        if 'hl.' in k:
            if '.snippets' in k:
                payload[k] = max(0, min(safe_int(v, default=max_hl), max_hl))
            elif '.fragsize' in k:
                payload[k] = max(1, min(safe_int(v, default=max_frag), max_frag)) #0 would return whole field
                payload['hl.maxHighlightCharacters'] = payload[k]
        if k == 'hl.fl':
            _cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_HIGHLIGHTS_FIELDS'))
        if k == 'fl' or ('.fl' in k and k != 'hl.fl'):
            _cleanup_fl(payload, user_id, k)
        if k == 'rows' or '.rows' in k:
            _cleanup_rows(payload, k)
        if k == 'facet.field':
            _cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_FACET_FIELDS'))
        if k == 'facet.pivot':
            _cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_FACET_PIVOT'))
        if k == 'stats.field':
            _cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_STATS_FIELDS'))
        if k == 'sort':
            _cleanup_fields(payload, k, current_app.config.get('SOLR_SERVICE_ALLOWED_SORT_FIELDS'))

    return payload, headers


def _cleanup_fields(payload, key, allowed_fields):
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


def _cleanup_rows(payload, key):
    """Ensure rows does not bypass the max rows limit"""
    value = payload[key]
    default_rows = current_app.config.get('SOLR_SERVICE_DEFAULT_ROWS', 10)
    max_rows = int(current_app.config.get('SOLR_SERVICE_MAX_ROWS', 100))
    payload[key] = min(safe_int(value, default=default_rows), max_rows)


def _cleanup_fl(payload, user_id, key):
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
        apply_protective_filters(payload, user_id, protected_fields, key)
