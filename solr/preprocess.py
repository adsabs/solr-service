from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import str


def preprocess_request(handler, query, config):
    """Rewrite the outbound query before it is dispatched to Solr.

    Injects configured query params, fills the default ``fl`` for the search
    handler, wires up highlight post-processing (``hl.q`` and the publisher
    field), and maps ``boostType`` onto a Solr ``boost`` expression.

    :param handler: the resolved config key for the target handler url
    :param query: the outbound query dict (mutated in place)
    :param config: the flask app config
    :return: bool, whether the response will need post-processing
    """
    should_postprocess_response = False

    if config.get("SOLR_INJECT_QUERY_PARAMS", {}):
        injected_params = config.get("SOLR_INJECT_QUERY_PARAMS", {})
        for injected_param, value in injected_params.items():
            if injected_param not in query.keys():
                query[injected_param] = value

    unhighlightable_publishers = config.get('SOLR_SERVICE_DISALLOWED_HIGHLIGHTS_PUBLISHERS', [])
    default_fields = config.get('SOLR_SERVICE_DEFAULT_FIELDS', [])

    if default_fields and handler == 'SOLR_SERVICE_SEARCH_HANDLER':
        if 'fl' not in query:
            query['fl'] = ",".join(default_fields)

        # We now post-process highlights with a windowing function to restrict the total text returned
        if 'hl' in query:
            should_postprocess_response = True

            if 'hl.q' not in query:
                query['hl.q'] = query['q']

        if unhighlightable_publishers and 'hl' in query:
            if 'publisher' not in query['fl']:
                query['fl'] = query['fl'] + ',publisher'
            should_postprocess_response = True

    boost_type_map = config.get('SOLR_SERVICE_BOOST_TYPES', dict())
    if boost_type_map and 'boostType' in query:
        boost_types = []
        if isinstance(query['boostType'], str):
            boost_types = [query['boostType']]
        elif isinstance(query['boostType'], list):
            boost_types = query['boostType']

        if 'defType' not in query:
            query['defType'] = 'aqp'
        query['boost'] = " ".join([boost_type_map[boost_type] for boost_type in boost_types
                                   if boost_type in boost_type_map])

    return should_postprocess_response
