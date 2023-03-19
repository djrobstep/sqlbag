from __future__ import absolute_import, division, print_function, unicode_literals

import copy
import getpass
import os
import random
import string
import tempfile
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.exc import InternalError, OperationalError, ProgrammingError
from sqlalchemy.engine.base import Connection

from sqlbag import quoted_identifier

from .sqla import (
    admin_db_connection,
    connection_from_s_or_c,
    make_url,
    kill_other_connections,
)


def database_exists(db_url, test_can_select=False):
    url = make_url(db_url)
    name = url.database
    db_type = url.get_dialect().name

    if not test_can_select:
        if db_type == "sqlite":
            return name is None or name == ":memory:" or os.path.exists(name)
        elif db_type in ["postgresql", "mysql"]:
            with admin_db_connection(url) as s:
                return _database_exists(s, name)
    return can_select(url)


def can_select(url):
    select1 = text("select 1")

    e = create_engine(url)

    try:
        with e.begin() as c:
            c.execute(select1)
        return True
    except (ProgrammingError, OperationalError, InternalError):
        return False


def _database_exists(session_or_connection, name):
    c = connection_from_s_or_c(session_or_connection)
    e = copy.copy(c.engine)
    url = make_url(e.url)
    dbtype = url.get_dialect().name

    if dbtype == "postgresql":
        EXISTENCE = text(
            """
            SELECT 1
            FROM pg_catalog.pg_database
            WHERE datname = :name
        """
        )

        result = c.execute(EXISTENCE, dict(name=name)).scalar()

        return bool(result)
    elif dbtype == "mysql":
        EXISTENCE = text(
            """
            SELECT SCHEMA_NAME
            FROM INFORMATION_SCHEMA.SCHEMATA
            WHERE SCHEMA_NAME = :name
        """
        )

        result = c.execute(EXISTENCE, dict(name=name)).scalar()

        return bool(result)


def create_database(db_url, template=None, wipe_if_existing=False):
    target_url = make_url(db_url)
    dbtype = target_url.get_dialect().name

    if wipe_if_existing:
        drop_database(db_url)

    if database_exists(target_url):
        return False
    else:

        if dbtype == "sqlite":
            can_select(target_url)
            return True

        with admin_db_connection(target_url) as c:
            if template:
                t = "template {}".format(quoted_identifier(template))
            else:
                t = ""

            c.execute(
                text(
                    """
                create database {} {};
            """.format(
                        quoted_identifier(target_url.database), t
                    )
                )
            )
        return True


def drop_database(db_url):
    url = make_url(db_url)

    dbtype = url.get_dialect().name
    name = url.database

    if database_exists(url):
        if dbtype == "sqlite":
            if name and name != ":memory:":
                os.remove(name)
                return True
            else:
                return False
        else:
            with admin_db_connection(url) as c:
                if dbtype == "postgresql":

                    REVOKE = "revoke connect on database {} from public"
                    revoke = text(REVOKE.format(quoted_identifier(name)))
                    c.execute(revoke)

                kill_other_connections(c, name, hardkill=True)

                c.execute(
                    text(
                        """
                    drop database if exists {};
                """.format(
                            quoted_identifier(name)
                        )
                    )
                )
            return True
    else:
        return False


def _current_username():
    return getpass.getuser()


def temporary_name(prefix="sqlbag_tmp_"):
    random_letters = [random.choice(string.ascii_lowercase) for _ in range(10)]
    rnd = "".join(random_letters)
    tempname = prefix + rnd
    return tempname


@contextmanager
def temporary_database(dialect="postgresql", do_not_delete=False, host=None):
    """
    Args:
        dialect(str): Type of database to create (either 'postgresql', 'mysql', or 'sqlite').
        do_not_delete: Do not delete the database as this method usually would.

    Creates a temporary database for the duration of the context manager scope. Cleans it up when finished unless do_not_delete is specified.

    PostgreSQL, MySQL/MariaDB, and SQLite are supported. This method's mysql creation code uses the pymysql driver, so make sure you have that installed.
    """

    host = host or ""

    if dialect == "sqlite":
        tmp = tempfile.NamedTemporaryFile(delete=False)

        try:
            url = "sqlite:///" + tmp.name
            yield url

        finally:
            if not do_not_delete:
                os.remove(tmp.name)

    else:
        tempname = temporary_name()

        current_username = _current_username()

        url = "{}://{}@{}/{}".format(dialect, current_username, host, tempname)

        if url.startswith("mysql:"):
            url = url.replace("mysql:", "mysql+pymysql:", 1)

        try:
            create_database(url)
            yield url
        finally:
            if not do_not_delete:
                drop_database(url)
