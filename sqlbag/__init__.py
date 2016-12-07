# -*- coding: utf-8 -*-
"""sqlbag is a bunch of handy SQL things.

This is a whole bunch of useful boilerplate and helper methods, for working
with SQL databases, particularly PostgreSQL.

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from .misc import quoted_identifier, load_sql_from_folder, \
    load_sql_from_file, sql_from_file, sql_from_folder, \
    sql_from_folder_iter

from .sqla import S, raw_execute, admin_db_connection, _killquery, \
    kill_other_connections, session, DB_ERROR_TUPLE, raw_connection, \
    get_raw_autocommit_connection, copy_url, connection_from_s_or_c, C

from .sqla_orm import row2dict, Base, metadata_from_session, \
    sqlachanges, get_properties

from .createdrop import \
    database_exists, create_database, \
    drop_database, temporary_database, can_select

try:
    from . import pg
except ImportError:
    pg = None

__all__ = (
    'C', 'get_inspector', 'S', 'raw_execute', 'load_sql_from_folder',
    'admin_db_connection', '_killquery', 'kill_other_connections', 'session',
    'quoted_identifier', 'DB_ERROR_TUPLE', 'raw_connection', 'copy_url',
    'connection_from_s_or_c', 'load_sql_from_file', 'sql_from_file',
    'sql_from_folder', 'sql_from_folder_iter', 'row2dict', 'get_properties',
    'Base', 'metadata_from_session', 'database_exists', 'create_database',
    'drop_database', 'temporary_database', 'pg', 'ColumnInfo',
    'get_raw_autocommit_connection', 'can_select', 'sqlachanges'
)
