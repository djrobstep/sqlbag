Connections
===========

Connections, flask setup, read-only user setup, SQLAlchemy ORM helpers, temporary database setup and teardown (handy for integration tests)

.. module:: sqlbag

Connections as context managers
-------------------------------

Use these context managers to connect to databases conveniently. The scope of the context manager defines the scope of the transaction.

.. autofunction:: S
.. autofunction:: C


More connection things
----------------------

More ways to make connections.

.. autofunction:: session
.. autofunction:: admin_db_connection
.. autofunction:: kill_other_connections
.. autofunction:: get_raw_autocommit_connection

Database URLs
-------------

.. autofunction:: sqlbag.copy_url
