from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()

import json
from flask import current_app


class Context(object):
    """Carries everything a pre-/post-processor might touch through the request
    pipeline. Processors mutate it in place (matching the service's historical
    in-place-mutation semantics), so new behavior can hook in without changing
    any call signatures.
    """

    def __init__(self, query, headers, request, config,
                 handler_class="default", handler_key=None, files=None):
        self.query = query                  # outbound payload dict (mutated)
        self.headers = headers              # outbound headers dict (mutated)
        self.request = request              # the inbound flask.request
        self.config = config                # the flask app config
        self.handler_class = handler_class  # bot / anonymous / default (+_embedded_bigquery)
        self.handler_key = handler_key      # resolved config key for the solr url
        self.files = files or {}            # multipart files for embedded bigquery
        self.response = None                # the solr requests.Response (set post-dispatch)
        self.response_data = None           # parsed response dict (set by run_postprocess)
        self.should_postprocess = False     # set by a pre-processor; gates post-processing


class PreProcessor(object):
    """A pre-dispatch step. ``applies`` decides whether ``process`` runs."""
    def applies(self, ctx):  # type: (Context) -> bool
        return True

    def process(self, ctx):  # type: (Context) -> None
        raise NotImplementedError


class PostProcessor(object):
    """A post-dispatch step operating on the parsed response dict in ``ctx``."""
    def applies(self, ctx):  # type: (Context) -> bool
        return True

    def process(self, ctx):  # type: (Context) -> None
        raise NotImplementedError


def run_preprocess(ctx):
    """Run every applicable pre-processor in registration order.

    The ordered registry lives in :mod:`solr.preprocess` (co-located with the
    processors); it is imported lazily here to keep the dependency one-way.
    """
    from .preprocess import PREPROCESSORS
    for processor in PREPROCESSORS:
        if processor.applies(ctx):
            processor.process(ctx)


def run_postprocess(ctx):
    """Run post-processors (gated by should_postprocess + response.ok) and return
    the final ``(body, status, headers)`` tuple for the resource to hand back.

    When post-processing applies, the parsed response dict is mutated by the
    registry and serialized once here (the string passes straight through the
    app's JSON representation without re-serialization). On any failure, or when
    no post-processing is needed, the raw Solr text is returned unchanged.
    """
    from .postprocess import POSTPROCESSORS
    r = ctx.response
    if ctx.should_postprocess and r.ok:
        try:
            ctx.response_data = r.json()
            for processor in POSTPROCESSORS:
                if processor.applies(ctx):
                    processor.process(ctx)
            return json.dumps(ctx.response_data), r.status_code, r.headers
        except Exception as e:
            current_app.logger.error(e.with_traceback())

    return r.text, r.status_code, r.headers
