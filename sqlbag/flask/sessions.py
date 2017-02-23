# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from flask import _app_ctx_stack

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from flask import current_app
from werkzeug.local import LocalProxy


FLASK_SCOPED_SESSION_MAKERS = []
COMMIT_AFTER_REQUEST = []


def session_setup(app):
    """Args:
        app (Flask Application): The flask application to set up.

    Wires up any sessions created with `FS` to commit automatically once the request response is complete.
    """
    f = flask_smart_after_request
    fteardown = flask_smart_teardown_appcontext

    funcs = app.after_request_funcs.get(None, [])

    if f not in funcs:
        funcs.append(f)
        app.after_request_funcs[None] = funcs

    if fteardown not in app.teardown_appcontext_funcs:
        app.teardown_appcontext_funcs.append(fteardown)


def FS(*args, **kwargs):
    """
    Args:
        args: Same arguments as SQLAlchemy's create_engine.
        kwargs: Same arguments as SQLAlchemy's create_engine.

    Returns:
        scoped_session: An SQLAlchemy scoped_session object (for more details,
            see SQLAlchemy docs).

    create this object in your initialization code.

    >>> s = FS('postgresql:///webdb')

    and make sure you've called `session_setup` somewhere in your init code also. After that, simply use it in your route methods like so:

    >>> results = s.execute('select a from b')

    all usages of this `s` object within the same request will use this same session.
    """

    commit_after_request = kwargs.get('commit_after_request', True)

    s = scoped_session(
        sessionmaker(bind=create_engine(*args, **kwargs)),
        scopefunc=_app_ctx_stack.__ident_func__)

    FLASK_SCOPED_SESSION_MAKERS.append(s)
    COMMIT_AFTER_REQUEST.append(bool(commit_after_request))
    return s


def flask_smart_after_request(resp):
    is_error = 400 <= resp.status_code < 600

    for do_commit, scoped in \
            zip(COMMIT_AFTER_REQUEST, FLASK_SCOPED_SESSION_MAKERS):

        if do_commit:
            if not is_error:
                scoped.commit()
    return resp


def flask_smart_teardown_appcontext(exception=None):
    for scoped in FLASK_SCOPED_SESSION_MAKERS:
        scoped.remove()


class Proxies(object):
    def __getattr__(self, name):
        def get_proxy():
            return getattr(current_app, name)
        return LocalProxy(get_proxy)


proxies = Proxies()
