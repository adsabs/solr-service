from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from typing import List

import json
from flask import current_app

from . import preprocess as _preprocess
from . import postprocess as _postprocess


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


# --- seeded registries -------------------------------------------------------
# Stage 3 seeds each registry with a single adapter delegating to the (still
# monolithic) preprocess/postprocess functions. Stage 4 replaces these with
# discrete, individually-testable processors in the same order. Appending a new
# processor here is all it takes to add behavior.

class _PreprocessAdapter(PreProcessor):
    def process(self, ctx):
        ctx.should_postprocess = _preprocess.preprocess_request(
            ctx.handler_key, ctx.query, ctx.config)


class _PostprocessAdapter(PostProcessor):
    def process(self, ctx):
        _postprocess.postprocess_response(ctx.response_data, ctx.config)


PREPROCESSORS = [_PreprocessAdapter()]   # type: List[PreProcessor]
POSTPROCESSORS = [_PostprocessAdapter()] # type: List[PostProcessor]


# --- drivers -----------------------------------------------------------------

def run_preprocess(ctx):
    """Run every applicable pre-processor in registration order."""
    for processor in PREPROCESSORS:
        if processor.applies(ctx):
            processor.process(ctx)


def run_postprocess(ctx):
    """Run post-processors (gated by should_postprocess + response.ok) and return
    the final ``(body, status, headers)`` tuple for the resource to hand back.

    When post-processing applies, the response dict is mutated by the registry
    and serialized once here (the string passes straight through the app's JSON
    representation without re-serialization). On any failure, or when no
    post-processing is needed, the raw Solr text is returned unchanged.
    """
    r = ctx.response
    if ctx.should_postprocess and r.ok:
        try:
            response_data = r.json()
            for processor in POSTPROCESSORS:
                if processor.applies(ctx):
                    ctx.response_data = response_data
                    processor.process(ctx)
            return json.dumps(response_data), r.status_code, r.headers
        except Exception as e:
            current_app.logger.error(e.with_traceback())

    return r.text, r.status_code, r.headers
