from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import str

from .middleware import PreProcessor, Context


class InjectQueryParams(PreProcessor):
    """Inject forced query params from SOLR_INJECT_QUERY_PARAMS (without
    clobbering anything the caller already supplied)."""

    def applies(self, ctx):
        return bool(ctx.config.get("SOLR_INJECT_QUERY_PARAMS", {}))

    def process(self, ctx):
        injected_params = ctx.config.get("SOLR_INJECT_QUERY_PARAMS", {})
        for injected_param, value in injected_params.items():
            if injected_param not in ctx.query.keys():
                ctx.query[injected_param] = value


class SearchDefaultsAndHighlightFlag(PreProcessor):
    """For the search handler: fill the default field list, and when
    highlighting is requested wire up ``hl.q`` and flag post-processing."""

    def applies(self, ctx):
        return bool(ctx.config.get('SOLR_SERVICE_DEFAULT_FIELDS', [])) \
            and ctx.handler_key == 'SOLR_SERVICE_SEARCH_HANDLER'

    def process(self, ctx):
        query = ctx.query
        if 'fl' not in query:
            query['fl'] = ",".join(ctx.config.get('SOLR_SERVICE_DEFAULT_FIELDS', []))

        # We now post-process highlights with a windowing function to restrict the total text returned
        if 'hl' in query:
            ctx.should_postprocess = True

            if 'hl.q' not in query:
                query['hl.q'] = query['q']


class PublisherHighlightFieldInjector(PreProcessor):
    """When highlights may need to be stripped per publisher agreements, make
    sure ``publisher`` is fetched so post-processing can act on it."""

    def applies(self, ctx):
        return bool(ctx.config.get('SOLR_SERVICE_DEFAULT_FIELDS', [])) \
            and ctx.handler_key == 'SOLR_SERVICE_SEARCH_HANDLER' \
            and bool(ctx.config.get('SOLR_SERVICE_DISALLOWED_HIGHLIGHTS_PUBLISHERS', [])) \
            and 'hl' in ctx.query

    def process(self, ctx):
        query = ctx.query
        if 'publisher' not in query['fl']:
            query['fl'] = query['fl'] + ',publisher'
        ctx.should_postprocess = True


class BoostTypeMapper(PreProcessor):
    """Map the friendly ``boostType`` parameter onto a Solr ``boost`` expression."""

    def applies(self, ctx):
        return bool(ctx.config.get('SOLR_SERVICE_BOOST_TYPES', dict())) \
            and 'boostType' in ctx.query

    def process(self, ctx):
        query = ctx.query
        boost_type_map = ctx.config.get('SOLR_SERVICE_BOOST_TYPES', dict())
        boost_types = []
        if isinstance(query['boostType'], str):
            boost_types = [query['boostType']]
        elif isinstance(query['boostType'], list):
            boost_types = query['boostType']

        if 'defType' not in query:
            query['defType'] = 'aqp'
        query['boost'] = " ".join([boost_type_map[boost_type] for boost_type in boost_types
                                   if boost_type in boost_type_map])


# Ordered pre-dispatch pipeline. Order matters: SearchDefaults fills `fl` before
# PublisherHighlightFieldInjector reads it. Add new behavior by inserting here.
PREPROCESSORS = [
    InjectQueryParams(),
    SearchDefaultsAndHighlightFlag(),
    PublisherHighlightFieldInjector(),
    BoostTypeMapper(),
]


def preprocess_request(handler, query, config):
    """Run the pre-processing pipeline over ``query`` and report whether the
    response will need post-processing. Thin convenience wrapper around the
    PREPROCESSORS registry; mutates ``query`` in place.
    """
    from . import middleware
    ctx = Context(query, {}, None, config, handler_key=handler)
    middleware.run_preprocess(ctx)
    return ctx.should_postprocess
