from __future__ import absolute_import, division, print_function, unicode_literals

import io
import os

import psycopg2
from pytest import raises
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError

from common import db  # flake8: noqa
from sqlbag import (
    C,
    S,
    _killquery,
    admin_db_connection,
    copy_url,
    get_raw_autocommit_connection,
    kill_other_connections,
    load_sql_from_file,
    load_sql_from_folder,
    raw_connection,
    session,
    sql_from_folder,
    temporary_database,
)

MYSQL_KILLQUERY_EXPECTED_ALL = """
    select
        *,
        ID as process_id,
        connection_id() as cid
    from
        information_schema.processlist
    where
        ID != connection_id()
"""

MYSQL_KILLQUERY_EXPECTED = """
    select
        *,
        ID as process_id,
        connection_id() as cid
    from
        information_schema.processlist
    where
        ID != connection_id()
 and COMMAND = 'Sleep' and DB = :databasename"""


def test_basic(db, tmpdir):
    url = copy_url(db)

    with S(db) as s:
        kill_other_connections(s, url.database)

    s = session(db)
    s.commit()
    s.close()

    with C(url) as c:
        c.execute("select 1")
        core_to_raw = raw_connection(c)

    with raises(ProgrammingError):
        with C(url) as c:
            c.execute("select bad")

    with admin_db_connection("sqlite://") as c:
        pass

    with temporary_database("mysql") as mysql_url:
        url = copy_url(mysql_url)

        with S(mysql_url) as s:
            s.execute("select 1")

        with admin_db_connection(mysql_url) as c:
            kq = _killquery(url.get_dialect().name, None, True)
            assert kq == MYSQL_KILLQUERY_EXPECTED_ALL
            kq = _killquery(url.get_dialect().name, url.database, False)
            assert kq == MYSQL_KILLQUERY_EXPECTED
            kill_other_connections(c, url.database, False)

    tempd = str(tmpdir / "sqlfiles")
    os.makedirs(tempd)

    tempf1 = str(tmpdir / "sqlfiles/f.sql")

    tempf2 = str(tmpdir / "f2.sql")
    tempf3 = str(tmpdir / "f3.sql")

    io.open(tempf1, "w").write("create table x(a text);")
    io.open(tempf2, "w").write("select * from x;")
    io.open(tempf3, "w").write("")

    out = io.StringIO()

    with S(db) as s:
        load_sql_from_folder(s, str(tempd), out=out, verbose=True)
        load_sql_from_file(s, str(tempf2))
        load_sql_from_file(s, str(tempf3))

        assert sql_from_folder(str(tempd)) == ["create table x(a text);"]

        session_to_raw = raw_connection(s)
        raw_to_raw = raw_connection(session_to_raw)

    assert type(raw_to_raw) == type(core_to_raw) == type(session_to_raw)

    a = db
    b = create_engine(db)
    c = psycopg2.connect(db)

    for x in [a, b, c]:
        cc = get_raw_autocommit_connection(x)
        try:
            assert type(cc) == type(c)
            assert cc.autocommit == True
        finally:
            cc.close()

    with raises(ValueError):
        get_raw_autocommit_connection(1)

    with raises(NotImplementedError):
        _killquery("oracle", "db", False)


import secrets


def test_transaction_separation(db):
    with S(db) as s1, S(db) as s2:
        id1 = s1.execute('select txid_current()').fetchall()[0][0]
        id2 = s2.execute('select txid_current()').fetchall()[0][0]
        assert id1 != id2
