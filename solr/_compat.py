from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()


def safe_int(val, default=0):
    """Coerce ``val`` to int, tolerating list/tuple wrappers and bad values."""
    if isinstance(val, (list, tuple)):
        val = val[0]
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


class ClosingTuple(tuple):
    """A tuple that propagates ``close()`` to its members.

    The sole raison d'etre of this class is to accommodate Flask, which wants to
    call ``close()`` on anything inside ``request.files``; and to allow requests
    to use files as ``(name, fileobj, mimetype)``.
    """
    def close(self):
        for x in self:
            if hasattr(x, 'close'):
                x.close()
