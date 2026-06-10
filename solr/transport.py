from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()


def parse_host(url):
    """Extract the ``host[:port]`` portion from a Solr handler URL.

    Accepts both full URLs (``http://host:8983/solr/select``) and bare
    ``host:port/path`` forms.
    """
    parts = url.split('/')
    if 'http' in parts[0].lower():
        return parts[2]
    return parts[0]
