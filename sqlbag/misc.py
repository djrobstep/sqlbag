from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from pathlib import Path
import io
import sys

from .sqla import raw_execute


def quoted_identifier(identifier):
    """One-liner to add double-quote marks around an SQL identifier
    (table name, view name, etc), and to escape double-quote marks.

    Args:
        identifier(str): the unquoted identifier
    """

    return '"{}"'.format(identifier.replace('"', '""'))


def sql_from_file(fpath):
    """
    Args:
        fpath (str): The path to the file.

    Returns:
        sql (str): The file contents as a string, with any whitespace stripped
            from the start and end.

    Merely opens a file and return the contents stripped of whitespace.
    """
    with io.open(str(fpath)) as f:
        return f.read().strip()


def sql_from_folder_iter(fpath):
    """
    Args:
        fpath (str): The path to the file.
    Returns:
        sql (str): The file contents as a string, with any whitespace stripped
            from the start and end.

    Iterate through all the .sql files in a folder.
    """
    folder = Path(fpath)

    sql_files = sorted(folder.glob('**/*.sql'))

    for fpath in sql_files:
        sql = sql_from_file(fpath)
        if sql:
            yield fpath, sql


def sql_from_folder(fpath):
    return list(sql for _, sql in sql_from_folder_iter(fpath))


def load_sql_from_folder(s, fpath, verbose=False, out=None):
    """
    Args:
        s (Session): Applies the SQL to this session.
        fpath (str): The path to the file.
        verbose (bool): Prints some information as it loads files.
        out (stream): Change where verbose mode prints to. defaults to sys.stdout

    Returns:
        sql (str): The file contents as a string, with any whitespace stripped from the start and end.

    Iterate through all the .sql files in a folder.
    """

    if verbose:
        if not out:
            out = sys.stdout  # pragma: no cover
        out.write('Running all .sql files in: {}'.format(fpath))

    for fpath, text in sql_from_folder_iter(fpath):
        if verbose:
            out.write('    Running SQL in: {}'.format(fpath))
        raw_execute(s, text)


def load_sql_from_file(s_or_c, fpath):
    """
    Args:
        s_or_c: :class:`Session` or :class:`Connection` to use.
        fpath (str): The path to the file.
    Returns:
        sql (str): The sql that was executed

    Iterate through all the .sql files in a folder.
    """

    text = sql_from_file(fpath)

    if text:
        raw_execute(s_or_c, text)

    return text
