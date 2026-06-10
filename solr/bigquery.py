from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import str
from past.builtins import basestring
from urllib.parse import parse_qs
import json

from flask import current_app

from .transport import parse_host


def extract_docs_values(input):
    """Pull the identifiers out of every ``docs(<id>)`` occurrence in a string.

    Returns them in order; preserves any prefix (e.g. ``library/abc``). Tolerates
    a missing closing paren by stopping at end-of-string.
    """
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


def check_for_embedded_bigquery(params, request, headers, handler_map,
                                handler_class="default", internal_logging_params=None):
    """Checks for the presence of docs() query any where inside
    the query parameters; if present - we'll verify/update
    the query with data.

    This function can also be used to process bigquery request
    (i.e. no docs() operator is present)
    """
    streams = set()
    for k, v in params.items():
        if 'q' in k: # well, i was lying - we'll only check params that *could* be a query
            if isinstance(v, basestring):
                if 'docs(' in v:
                    streams.update(extract_docs_values(v))
            else:
                for x in v:
                    if 'docs(' in x:
                        streams.update(extract_docs_values(x))

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
    files = _get_stream_data(params, list(streams), request, handler_map,
                             handler_class=handler_class,
                             internal_logging_params=internal_logging_params)

    # let requests library pick the appropriate ctype
    if len(files):
        del headers['Content-Type']

    return files


def _get_stream_data(params, streams, request, handler_map, handler_class="default",
                     internal_logging_params=None):
    # TODO: it seems natural that this functionality could live inside
    # myads; there we'd be not forced to query a remote service; however
    # I fear that is not really what people are asking for - they just
    # want any/all queries to work when we say foo AND docs(barxxxx)
    internal_logging_params = internal_logging_params or {}

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
        handler = handler_map.get(handler_class, handler_map.get("default", "-"))
        new_headers['Host'] = parse_host(current_app.config.get(handler))
        for internal_param in internal_logging_params.keys():
            if internal_param in request.headers:
                new_headers[internal_param] = request.headers[internal_param]

        docs = None

        if prefix == 'library':
            q = _harvest_library(value, new_headers)
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
    for k, v in request.files.items():
        if k not in out:
            out[k] = (v.name, v.stream, v.mimetype)
    return out


def _harvest_library(library_id, headers):
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
