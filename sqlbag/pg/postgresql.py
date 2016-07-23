from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys

from sqlbag import raw_connection
from psycopg2 import errorcodes as pgerrorcodes

import six

if not six.PY2:
    unicode = str


def errorcode_from_error(e):
    """
    Get the error code from a particular error/exception caused by PostgreSQL.
    """
    return e.orig.pgcode


def pg_errorname_lookup(pgcode):
    """
    Args:
        pgcode(int): A PostgreSQL error code.

    Returns:
        The error name from a PostgreSQL error code as per: https://www.postgresql.org/docs/9.5/static/errcodes-appendix.html
    """

    return pgerrorcodes.lookup(str(pgcode))


def pg_notices(s, wipe=False):
    """
    Args:
        s(:class:`sqlalchemy.orm.Session`): The session in question.
        wipe(bool): If true, clears the notices after reading them.

    Returns:
        notices(list): The list of notices.

    Grab the list of notices that PostgreSQL has generated for the connection.

    Optionally wipes/clears the list so you won't see the same ones if you check again later.
    """

    c = raw_connection(s)
    notices = list(c.notices)
    if wipe:
        del c.notices[:]
    return notices


def pg_print_notices(s, out=None, wipe=True):
    """
    Args:
        s(sqlalchemy.orm.Session): The session.
        out(stream): Output stream to print notices to. If None, use sys.stdout
        wipe(bool): If True, wipes the current notices after reading them.

    Print the notices generated for a session.
    """
    if not out:
        out = sys.stdout  # pragma: no cover

    for n in pg_notices(s, wipe=wipe):
        for line in n.splitlines():
            out.write(unicode(line))
