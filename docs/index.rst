sqlbag: miscellaneous sql utilities
===================================

This is just a collection of handy code for doing database things.

What is in the box
------------------

Connections, flask setup, SQLAlchemy ORM helpers, temporary database setup and teardown (handy for integration tests).

Database sessions like this:

.. code-block:: python

    from sqlbag import S

    with S('postgresql:///example') as s:
        s.execute('select 1;')

Temporary databases (for integration tests etc) like this:

.. code-block:: python

    from sqlbag import S, temporary_database

    with temporary_database('postgresql') as temporary_database_url:
        with S(temporary_database_url) as s:
            s.execute('select 1;')

Thread-safe database connections for your flask app like this:

.. code-block:: python

    from sqlbag.flask import FS, session_setup
    from flask import Flask

    app = Flask(__name__)

    s = FS('postgresql:///example')
    session_setup(app)

    @app.route("/")
    def hello():
        # returns 'Hello World!' as a response
        return s.execute("select 'Hello world!'").scalar()

    if __name__ == "__main__":
        app.run()


Installation
------------

Simply install with `pip <https://pip.pypa.io>`_:

.. code-block:: shell

    $ pip install sqlbag

If you want you can install the database drivers you need at the same time, by specifying one of the optional bundles.

If you're using postgres, this installs ``sqlbag`` and ``psycopg2``:

.. code-block:: shell

    $ pip install sqlbag[pg]

If you're installing MySQL/MariaDB then this installs ``pymysql`` as well:

.. code-block:: shell

    $ pip install sqlbag[maria]


API/Interface Details
---------------------

.. toctree::
   :maxdepth: 3

   connections.rst
   sqlalchemy.rst
   misc.rst
   createdrop.rst
   flask.rst
   postgres.rst

* :ref:`genindex`

Useful Links
------------

Source Code: `github.com/djrobstep/sqlbag <https://github.com/djrobstep/sqlbag>`_

PyPI package info: `sqlbag@PyPI <https://pypi.python.org/pypi/sqlbag>`_
