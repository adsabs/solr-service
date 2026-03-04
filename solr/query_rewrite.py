import re


def rewrite_unfielded_ads_query(query):
    """
    Rewrites simple citation-like free-text queries into fielded queries.
    Returns rewritten query string or None when no supported pattern matches.
    """
    if not isinstance(query, str):
        return None

    raw = query.strip()
    if not raw:
        return None

    # Avoid rewriting explicit Solr syntax or advanced user queries.
    if _looks_fielded_or_advanced(raw):
        return None

    parsed = _extract_year(raw)
    if not parsed:
        return None
    body, year = parsed

    normalized = _normalize_body(body)
    if not normalized:
        return None

    # case: Lastname et al
    m = re.match(r'^([A-Za-z][A-Za-z\'\-]+)\s+et\s+al$', normalized, flags=re.IGNORECASE)
    if m:
        a1 = _canon(m.group(1))
        return 'first_author:"{0}" author_count:[2 TO 10000] year:{1}'.format(a1, year)

    # case: Lastname1 & Lastname2
    m = re.match(
        r'^([A-Za-z][A-Za-z\'\-]+)\s*&\s*([A-Za-z][A-Za-z\'\-]+)$',
        normalized,
        flags=re.IGNORECASE,
    )
    if m:
        a1 = _canon(m.group(1))
        a2 = _canon(m.group(2))
        return 'first_author:"{0}" author:"{1}" year:{2}'.format(a1, a2, year)

    # case: Lastname1 [,] Lastname2 & Lastname3
    m = re.match(
        r'^([A-Za-z][A-Za-z\'\-]+)\s*,?\s*([A-Za-z][A-Za-z\'\-]+)\s*&\s*([A-Za-z][A-Za-z\'\-]+)$',
        normalized,
        flags=re.IGNORECASE,
    )
    if m:
        a1 = _canon(m.group(1))
        a2 = _canon(m.group(2))
        a3 = _canon(m.group(3))
        return 'first_author:"{0}" author:("{1}" "{2}") year:{3}'.format(a1, a2, a3, year)

    tokens = normalized.split()
    if len(tokens) == 1:
        a = _canon(tokens[0])
        return '(first_author:"{0}" OR author:"{0}") year:{1}'.format(a, year)

    if len(tokens) == 2:
        a1 = _canon(tokens[0])
        a2 = _canon(tokens[1])
        return '(author:"{a1} {a2}" OR author("{a1}" "{a2}")) year:{year}'.format(
            a1=a1, a2=a2, year=year
        )

    return None


def _looks_fielded_or_advanced(query):
    # fielded terms and/or common advanced query syntax; keep conservative.
    if re.search(r'\b[A-Za-z_][A-Za-z0-9_.-]*\s*:', query):
        return True
    if any(ch in query for ch in ['(', ')', '"', '[', ']', '*', '?', '^', '~']):
        return True
    if re.search(r'\b(AND|OR|NOT)\b', query, flags=re.IGNORECASE):
        return True
    return False


def _extract_year(query):
    m = re.search(r'\b((?:19|20)\d{2})([A-Za-z]?)\s*$', query)
    if not m:
        return None
    year = m.group(1)
    body = query[:m.start()].strip()
    if not body:
        return None
    return body, year


def _normalize_body(body):
    # replace en-dash and em-dash with a hyphen
    body = body.replace(u'\u2013', '-').replace(u'\u2014', '-')
    # replace all whitespace with a regular space
    body = re.sub(r'\s+', ' ', body)
    return body.strip(' \t\r\n,.;:')


def _canon(token):
    return token.lower().strip(" \t\r\n,.;:()[]{}'\"")
