from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()


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
