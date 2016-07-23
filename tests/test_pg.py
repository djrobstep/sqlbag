from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from common import db  # flake8: noqa

from sqlbag import S, copy_url
from sqlbag.pg import pg_errorname_lookup, \
    errorcode_from_error, pg_notices, pg_print_notices

from pytest import raises

from sqlalchemy.exc import ProgrammingError
from sqlalchemy.pool import NullPool
import io

from sqlbag import DB_ERROR_TUPLE

from datetime import datetime

USERNAME = 'testonly_sqlbag_user'
PW = 'duck'


def test_errors_and_messages(db):
    assert pg_errorname_lookup(22005) == 'ERROR_IN_ASSIGNMENT'

    with S(db) as s:
        s.execute('drop table if exists x')
        assert pg_notices(s) == [
            'NOTICE:  table "x" does not exist, skipping\n'
        ]
        assert pg_notices(s, wipe=True) == [
            'NOTICE:  table "x" does not exist, skipping\n'
        ]
        assert pg_notices(s) == []

        out = io.StringIO()
        s.execute('drop table if exists x')
        pg_print_notices(s, out=out)

        assert out.getvalue() == \
            'NOTICE:  table "x" does not exist, skipping'

        out = io.StringIO()
        pg_print_notices(s, out=out)

        assert out.getvalue() == ''

        s.execute('create table x(id text)')

    try:
        with S(db) as s:
            s.execute('create table x(id text)')
    except DB_ERROR_TUPLE as e:
        assert errorcode_from_error(e) == '42P07'
