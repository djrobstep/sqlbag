from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import random
import string
import getpass
import os
import tempfile
import copy

from contextlib import contextmanager

from sqlalchemy import create_engine

from sqlbag import quoted_identifier

from .sqla import copy_url, admin_db_connection, \
    kill_other_connections, \
    connection_from_s_or_c


from sqlalchemy.exc import \
    ProgrammingError, \
    OperationalError, \
    InternalError


def database_exists(db_url, test_can_select=False):
    url = copy_url(db_url)
    name = url.database
    db_type = url.get_dialect().name

    if not test_can_select:
        if db_type == 'sqlite':
            return name is None or name == ':memory:' \
                or os.path.exists(name)
        elif db_type in ['postgresql', 'mysql']:
            with admin_db_connection(url) as s:
                return _database_exists(s, name)
    return can_select(url)


def can_select(url):
    text = 'select 1'

    e = create_engine(url)

    try:
        e.execute(text)
        return True
    except (ProgrammingError, OperationalError, InternalError):
        return False


def _database_exists(session_or_connection, name):
    c = connection_from_s_or_c(session_or_connection)
    e = copy.copy(c.engine)
    url = copy_url(e.url)
    dbtype = url.get_dialect().name

    if dbtype == 'postgresql':
        EXISTENCE = """
            SELECT 1
            FROM pg_catalog.pg_database
            WHERE datname = %s
        """

        result = c.execute(EXISTENCE, (name, )).scalar()

        return bool(result)
    elif dbtype == 'mysql':
        EXISTENCE = """
            SELECT SCHEMA_NAME
            FROM INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = %s
        """

        result = c.execute(EXISTENCE, (name, )).scalar()

        return bool(result)


def create_database(db_url, template=None, wipe_if_existing=False):
    target_url = copy_url(db_url)
    dbtype = target_url.get_dialect().name

    if wipe_if_existing:
        drop_database(db_url)

    if database_exists(target_url):
        return False
    else:

        if dbtype == 'sqlite':
            can_select(target_url)
            return True

        with admin_db_connection(target_url) as c:
            if template:
                t = 'template {}'.format(quoted_identifier(template))
            else:
                t = ''

            c.execute("""
                create database {} {};
            """.format(
                quoted_identifier(target_url.database), t))
        return True


def drop_database(db_url):
    url = copy_url(db_url)

    dbtype = url.get_dialect().name
    name = url.database

    if database_exists(url):
        if dbtype == 'sqlite':
            if name and name != ':memory:':
                os.remove(name)
                return True
            else:
                return False
        else:
            with admin_db_connection(url) as c:
                if dbtype == 'postgresql':

                    REVOKE = 'revoke connect on database {} from public'
                    revoke = REVOKE.format(quoted_identifier(name))
                    c.execute(revoke)

                kill_other_connections(c, name, hardkill=True)

                c.execute("""
                    drop database if exists {};
                """.format(quoted_identifier(name)))
            return True
    else:
        return False


def _current_username():
    return getpass.getuser()


@contextmanager
def temporary_database(dialect='postgresql', do_not_delete=False):
    """
    Args:
        dialect(str): Type of database to create (either 'postgresql', 'mysql', or 'sqlite').
        do_not_delete: Do not delete the database as this method usually would.

    Creates a temporary database for the duration of the context manager scope. Cleans it up when finished unless do_not_delete is specified.

    PostgreSQL, MySQL/MariaDB, and SQLite are supported. This method's mysql creation code uses the pymysql driver, so make sure you have that installed.
    """
    if dialect == 'sqlite':
        tmp = tempfile.NamedTemporaryFile(delete=False)

        try:
            url = 'sqlite:///' + tmp.name
            yield url

        finally:
            if not do_not_delete:
                os.remove(tmp.name)

    else:
        rnd = ''.join([random.choice(string.ascii_lowercase)
                       for _ in range(10)])
        tempname = 'sqlbag_tmp_' + rnd

        current_username = _current_username()

        url = '{}://{}@/{}'.format(dialect, current_username, tempname)

        if url.startswith('mysql:'):
            url = url.replace('mysql:', 'mysql+pymysql:', 1)

        try:
            create_database(url)
            yield url
        finally:
            if not do_not_delete:
                drop_database(url)
