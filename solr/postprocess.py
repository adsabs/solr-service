from __future__ import absolute_import

import re

from future import standard_library
standard_library.install_aliases()
from builtins import str
from typing import List


def postprocess_response(response_data, config):
    """Shape a Solr response in place: drop disallowed-publisher highlights,
    window every remaining highlight, prune empties, and stamp ``filtered``.

    :param response_data: the parsed Solr response dict (mutated in place)
    :param config: the flask app config
    :return: the same dict
    """
    unhighlightable_publishers = config.get('SOLR_SERVICE_DISALLOWED_HIGHLIGHTS_PUBLISHERS', [])
    unhighlightable_docs = []

    for doc in response_data['response']['docs']:
        if 'publisher' not in doc:
            continue

        if type(doc['publisher']) is list:
            for publisher in doc['publisher']:
                if publisher.lower() in unhighlightable_publishers:
                    unhighlightable_docs.append(doc['id'])
                    break
        else:
            if doc['publisher'].lower() in unhighlightable_publishers:
                unhighlightable_docs.append(doc['id'])

    for remove_doc in unhighlightable_docs:
        if remove_doc in response_data['highlighting']:
            doc_highlights = response_data['highlighting'][remove_doc]

            for remove_key in ['body', 'ack']:
                if remove_key in doc_highlights:
                    del doc_highlights[remove_key]

    max_frag = config.get('SOLR_SERVICE_MAX_FRAGSIZE', 200)
    for doc_id in list(response_data['highlighting'].keys()):
        current_highlights = response_data['highlighting'][doc_id]
        new_highlights = dict()

        for field in current_highlights.keys():
            new_highlights[field] = [
                windowed_highlight
                for highlight in current_highlights[field]
                for windowed_highlight in apply_highlight_window(highlight, max_frag)
            ]

        response_data['highlighting'][doc_id] = new_highlights

    for _, doc_highlights in response_data['highlighting'].items():
        for field, highlights in list(doc_highlights.items()):
            doc_highlights[field] = [highlight for highlight in highlights
                                     if highlight is not None and str(highlight).strip() != ""]

    response_data['filtered'] = 'true'

    return response_data


def apply_highlight_window(highlight_text, max_len):
    # type: (str, int) -> List[str]
    """Window a Solr highlight snippet down to ``max_len`` characters per group.

    Finds every ``<em>...</em>`` match, greedily groups consecutive matches that
    fit within a single ``max_len`` window, then emits one snippet per group with
    the leftover space split as padding around the matches (redistributed when a
    group sits against the start or end of the text). Groups whose matches alone
    exceed ``max_len`` are dropped. Returns ``[]`` when there are no matches.
    """
    highlight_pattern = re.compile(r'<em>[^>]*</em>', re.IGNORECASE)

    matches = list(re.finditer(highlight_pattern, highlight_text))
    if not matches:
        return []

    # Greedily group consecutive matches that fit within a single max_len window
    groups = []
    current_group = [matches[0]]
    for match in matches[1:]:
        if match.end() - current_group[0].start() <= max_len:
            current_group.append(match)
        else:
            groups.append(current_group)
            current_group = [match]
    groups.append(current_group)

    windowed_snippets = []
    text_len = len(highlight_text)

    for group in groups:
        group_start = group[0].start()
        group_end = group[-1].end()
        extent = group_end - group_start

        if extent > max_len:
            continue

        remaining = max_len - extent
        pad_before = remaining // 2
        pad_after = remaining - pad_before

        win_start = group_start - pad_before
        win_end = group_end + pad_after

        # Redistribute unused padding at text boundaries
        if win_start < 0:
            win_end = min(text_len, win_end - win_start)
            win_start = 0
        if win_end > text_len:
            win_start = max(0, win_start - (win_end - text_len))
            win_end = text_len

        windowed_snippets.append(highlight_text[win_start:win_end])

    return windowed_snippets
