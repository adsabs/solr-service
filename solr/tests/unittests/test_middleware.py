"""
Tests for the pre-/post-processing middleware pipeline: ordered execution,
`applies` gating, the post-process response gate, and the extensibility
guarantee (a new processor composes via the registry alone).
"""
import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
import json
import unittest
import mock

from solr import middleware
from solr.middleware import Context, PreProcessor, PostProcessor


class _Record(PreProcessor):
    def __init__(self, name, log, applies=True):
        self.name = name
        self.log = log
        self._applies = applies

    def applies(self, ctx):
        return self._applies

    def process(self, ctx):
        self.log.append(self.name)


class TestRunPreprocess(unittest.TestCase):

    def _ctx(self):
        return Context({}, {}, None, {}, handler_key='X')

    def test_runs_in_order(self):
        log = []
        with mock.patch('solr.preprocess.PREPROCESSORS',
                        [_Record('a', log), _Record('b', log), _Record('c', log)]):
            middleware.run_preprocess(self._ctx())
        self.assertEqual(log, ['a', 'b', 'c'])

    def test_skips_non_applicable(self):
        log = []
        with mock.patch('solr.preprocess.PREPROCESSORS',
                        [_Record('a', log), _Record('skip', log, applies=False), _Record('c', log)]):
            middleware.run_preprocess(self._ctx())
        self.assertEqual(log, ['a', 'c'])

    def test_custom_processor_composes(self):
        # The extensibility guarantee: appending a processor to the registry
        # makes it run, without touching the driver or any resource.
        log = []

        class Marker(PreProcessor):
            def process(self, ctx):
                ctx.query['marker'] = 'on'

        with mock.patch('solr.preprocess.PREPROCESSORS', [Marker()]):
            ctx = self._ctx()
            middleware.run_preprocess(ctx)
        self.assertEqual(ctx.query['marker'], 'on')


class _FakeResponse(object):
    def __init__(self, payload, ok=True, status=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status
        self.text = payload
        self.headers = {}

    def json(self):
        return json.loads(self._payload)


class TestRunPostprocess(unittest.TestCase):

    def _ctx(self, response, should=True):
        ctx = Context({}, {}, None, {})
        ctx.response = response
        ctx.should_postprocess = should
        return ctx

    def test_gate_requires_should_postprocess(self):
        # should_postprocess False -> raw text passes through untouched.
        resp = _FakeResponse('{"a": 1}')
        with mock.patch('solr.postprocess.POSTPROCESSORS', []):
            body, status, headers = middleware.run_postprocess(self._ctx(resp, should=False))
        self.assertEqual(body, '{"a": 1}')
        self.assertEqual(status, 200)

    def test_gate_requires_ok_response(self):
        resp = _FakeResponse('err', ok=False, status=500)
        with mock.patch('solr.postprocess.POSTPROCESSORS', []):
            body, status, headers = middleware.run_postprocess(self._ctx(resp))
        self.assertEqual(body, 'err')
        self.assertEqual(status, 500)

    def test_runs_processors_and_serializes(self):
        resp = _FakeResponse('{"a": 1}')

        class Stamp(PostProcessor):
            def process(self, ctx):
                ctx.response_data['stamped'] = True

        with mock.patch('solr.postprocess.POSTPROCESSORS', [Stamp()]):
            body, status, headers = middleware.run_postprocess(self._ctx(resp))
        self.assertEqual(json.loads(body), {'a': 1, 'stamped': True})


class TestSeededRegistryOrder(unittest.TestCase):

    def test_preprocess_registry_order(self):
        from solr.preprocess import (PREPROCESSORS, InjectQueryParams,
                                      SearchDefaultsAndHighlightFlag,
                                      PublisherHighlightFieldInjector, BoostTypeMapper)
        self.assertEqual(
            [type(p) for p in PREPROCESSORS],
            [InjectQueryParams, SearchDefaultsAndHighlightFlag,
             PublisherHighlightFieldInjector, BoostTypeMapper])

    def test_postprocess_registry_order(self):
        from solr.postprocess import (POSTPROCESSORS, PublisherHighlightRemover,
                                      HighlightWindower, EmptyHighlightPruner,
                                      FilteredFlagSetter)
        self.assertEqual(
            [type(p) for p in POSTPROCESSORS],
            [PublisherHighlightRemover, HighlightWindower,
             EmptyHighlightPruner, FilteredFlagSetter])


if __name__ == '__main__':
    unittest.main()
