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


def select_cookies(request, config):
    """Pick out the request cookies whose name is in
    ``SOLR_SERVICE_FORWARDED_COOKIES`` (e.g. the ``sroute`` affinity cookie).

    :param request: the current flask.request
    :param config: the flask app config
    :return: dict of forwarded cookies, or None when there are none
    """
    cookie_names = config.get('SOLR_SERVICE_FORWARDED_COOKIES', {})
    cookie = {}
    for cookie_name in cookie_names:
        value = request.cookies.get(cookie_name, None)
        if value:
            cookie[cookie_name] = value
    if cookie:
        return cookie
    else:
        return None
