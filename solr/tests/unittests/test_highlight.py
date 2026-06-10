"""
Characterization tests for the highlight windowing algorithm
(`SolrInterface.apply_highlight_window`, the "greedy grouping algorithm").

These lock in the exact current behavior before the function is moved into
solr/postprocess.py. Every expected string below was computed by hand from the
algorithm in solr/views.py so that a refactor cannot silently change output.
"""
import sys, os
PROJECT_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
import unittest

from solr.views import SolrInterface


class TestApplyHighlightWindow(unittest.TestCase):

    def setUp(self):
        self.si = SolrInterface()

    def window(self, text, max_len):
        return self.si.apply_highlight_window(text, max_len)

    def test_no_match_returns_empty(self):
        self.assertEqual(self.window("no highlights here", 50), [])

    def test_single_match_centered_padding(self):
        # "AAAA<em>X</em>BBBB": match spans [4, 14), extent 10, text_len 18.
        # max_len 14 -> remaining 4 -> pad 2/2 -> window [2, 16).
        text = "AAAA<em>X</em>BBBB"
        self.assertEqual(self.window(text, 14), ["AA<em>X</em>BB"])

    def test_padding_parity_extra_goes_after(self):
        # Same text, max_len 15 -> remaining 5 -> pad_before 2, pad_after 3.
        text = "AAAA<em>X</em>BBBB"
        self.assertEqual(self.window(text, 15), ["AA<em>X</em>BBB"])

    def test_match_longer_than_max_is_skipped(self):
        # extent 14 > max_len 10 -> group dropped -> empty result.
        self.assertEqual(self.window("<em>XXXXX</em>", 10), [])

    def test_two_matches_grouped_into_single_window(self):
        # max_len large enough that second match end - first start <= max_len.
        text = "<em>A</em> <em>B</em>"
        self.assertEqual(self.window(text, 21), ["<em>A</em> <em>B</em>"])

    def test_two_matches_split_into_two_windows(self):
        # max_len 10 forces separate groups.
        text = "<em>A</em> <em>B</em>"
        self.assertEqual(self.window(text, 10), ["<em>A</em>", "<em>B</em>"])

    def test_boundary_redistribution_at_start(self):
        # Match at start: win_start would be negative, padding shifts right.
        # "<em>X</em>BBBBBBBBBB": match [0,10), text_len 20, max_len 14.
        text = "<em>X</em>BBBBBBBBBB"
        self.assertEqual(self.window(text, 14), ["<em>X</em>BBBB"])

    def test_boundary_redistribution_at_end(self):
        # Match at end: win_end exceeds text_len, padding shifts left.
        # "BBBBBBBBBB<em>X</em>": match [10,20), text_len 20, max_len 14.
        text = "BBBBBBBBBB<em>X</em>"
        self.assertEqual(self.window(text, 14), ["BBBB<em>X</em>"])


if __name__ == '__main__':
    unittest.main()
