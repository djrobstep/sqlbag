"""Miscellaneous helpful stuff for working with the SQLAlchemy core."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import copy
import getpass

from sqlalchemy.sql import text

from contextlib import contextmanager

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine

import sqlalchemy.exc
import sqlalchemy.orm
import sqlalchemy.engine.url
from six import string_types

from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
import sqlalchemy.orm.session

from .util_mysql import MYSQL_KILLQUERY_FORMAT as MYSQL_KILL
from .util_pg import PSQL_KILLQUERY_FORMAT_INCLUDING_DROPPED \
    as PG_KILL

DB_ERROR_TUPLE = (sqlalchemy.exc.OperationalError,
                  sqlalchemy.exc.InternalError,
                  sqlalchemy.exc.ProgrammingError)

SCOPED_SESSION_MAKERS = {}


def copy_url(db_url):
    """
    Args:
        db_url: Already existing SQLAlchemy :class:`URL`, or URL string.
    Returns:
        A brand new SQLAlchemy :class:`URL`.

    Make a copy of a SQLAlchemy :class:`URL`.
    """
    return copy.copy(make_url(db_url))


def connection_from_s_or_c(s_or_c):
    """Args:
        s_or_c (str): Either an SQLAlchemy ORM :class:`Session`, or a core
            :class:`Connection`.

    Returns:
        Connection: An SQLAlchemy Core connection. If you passed in a
            :class:`Session`, it's the Connection associated with that session.

    Get you a method that can do both. This is handy for writing methods
    that can accept both :class:`Session`s and core :class:`Connection`s.

    """
    try:
        s_or_c.engine
        return s_or_c
    except AttributeError:
        return s_or_c.connection()


def get_raw_autocommit_connection(url_or_engine_or_connection):
    """
    Args:
        url_or_engine_or_connection (str): A URL string or SQLAlchemy engine object, or already existing DBAPI connection.

    Returns:
        A connection in autocommit mode.

    Sometimes you want just want to autocommit.

    """
    x = url_or_engine_or_connection

    if isinstance(x, string_types):
        import psycopg2
        c = psycopg2.connect(x)
        x = c
    elif isinstance(x, Engine):
        sqla_connection = x.connect()
        sqla_connection.execution_options(isolation_level="AUTOCOMMIT")
        sqla_connection.detach()
        x = sqla_connection.connection.connection
    elif hasattr(x, 'protocol_version'):
        # this is already a DBAPI connection object
        pass
    else:
        raise \
            ValueError('must pass a url or engine or DBAPI connection object')
    x.autocommit = True
    return x


def session(*args, **kwargs):
    """
    Returns:
        Session: A new SQLAlchemy :class:`Session`.

    Boilerplate method to create a database session.

    Pass in the same parameters as you'd pass to create_engine. Internally,
    this uses SQLAlchemy's `scoped_session` session constructors, which means
    that calling it again with the same parameters will reuse the
    `scoped_session`.

    :class:`S <S>` creates a session in the same way but in the form of a
    context manager.
    """
    Session = get_scoped_session_maker(*args, **kwargs)
    return Session()


@contextmanager
def S(*args, **kwargs):
    """Boilerplate context manager for creating and using sessions.

    This makes using a database session as simple as:

    .. code-block:: python

        with S('postgresql:///databasename') as s:
            s.execute('select 1;')

    Does `commit()` on close, `rollback()` on exception.

    Also uses `scoped_session` under the hood.

    """
    Session = get_scoped_session_maker(*args, **kwargs)

    try:
        session = Session()
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_scoped_session_maker(*args, **kwargs):
    """
    Creates a scoped session maker, and saves it for reuse next time.

    """
    tup = (args, frozenset(kwargs.items()))
    if tup not in SCOPED_SESSION_MAKERS:
        SCOPED_SESSION_MAKERS[tup] = scoped_session(sessionmaker(
            bind=create_engine(*args, **kwargs)))
    return SCOPED_SESSION_MAKERS[tup]


def raw_connection(s_or_c_or_rawc):
    """
    Args:
        s_or_c_or_rawc (str): SQLAlchemy :class:`Session` or :class:`Connection` or already existing DBAPI connection.
    Returns:
        connection (str): Raw DBAPI connection

    Get the raw DBAPI connection from
    """
    x = s_or_c_or_rawc

    try:
        return connection_from_s_or_c(x).connection
    except TypeError:
        return x


def raw_execute(s, statements):
    raw_connection(s).cursor().execute(statements)


@contextmanager
def C(*args, **kwargs):
    """
    Hello it's me.
    """
    e = create_engine(*args, **kwargs)
    c = e.connect()
    trans = c.begin()

    try:
        yield c
        trans.commit()
    except:
        trans.rollback()
        raise
    finally:
        c.close()


@contextmanager
def admin_db_connection(db_url):
    url = copy_url(db_url)
    dbtype = url.get_dialect().name

    if dbtype == 'postgresql':
        url.database = ''

        if not url.username:
            url.username = getpass.getuser()

    elif not dbtype == 'sqlite':
        url.database = None

    if dbtype == 'postgresql':
        with C(url, poolclass=NullPool, isolation_level='AUTOCOMMIT') as c:
            yield c

    elif dbtype == 'mysql':
        with C(url, poolclass=NullPool) as c:
            c.execute("""
                SET sql_mode = 'ANSI';
            """)
            yield c

    elif dbtype == 'sqlite':
        with C(url, poolclass=NullPool) as c:
            yield c


def _killquery(dbtype, dbname, hardkill):
    where = []

    if dbtype == 'postgresql':
        sql = PG_KILL

        if not hardkill:
            where.append("psa.state = 'idle'")
        if dbname:
            where.append('datname = :databasename')
    elif dbtype == 'mysql':
        sql = MYSQL_KILL

        if not hardkill:
            where.append("COMMAND = 'Sleep'")
        if dbname:
            where.append('DB = :databasename')
    else:
        raise NotImplementedError

    where = ' and '.join(where)

    if where:
        sql += ' and {}'.format(where)
    return sql


def kill_other_connections(s_or_c, dbname=None, hardkill=False):
    """
    Args:
        s_or_c: SQLAlchemy Session or Connection. Needs to have the appropriate permssions to kill connections. For best results use :class:`admin_db_connection`.
        dbname: Name of database. If `None`, kills connections to all databases on the server.

    Returns:
        None

    Kill other connections to this database (or entire database server).
    """
    c = connection_from_s_or_c(s_or_c)

    dbtype = c.engine.dialect.name

    killquery = _killquery(dbtype, dbname=dbname, hardkill=hardkill)

    if dbname:
        results = c.execute(text(killquery), databasename=dbname)
    else:  # pragma: no cover
        results = c.execute(text(killquery))

    if dbtype == 'mysql':
        for x in results:
            kill = text('kill connection :pid')

            try:
                c.execute(kill, pid=x.process_id)
            except sqlalchemy.exc.InternalError as e:  # pragma: no cover
                code, message = e.orig.args
                if 'Unknown thread id' in message:
                    pass
                else:
                    raise
