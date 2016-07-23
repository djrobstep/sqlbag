Create and drop databases
=========================

Programmatically create and delete databases. Includes a contextmanager for creating a temporary database and dropping it when finished, useful for integration tests.

Creators and droppers
---------------------

.. autofunction:: sqlbag.temporary_database
.. autofunction:: sqlbag.create_database
.. autofunction:: sqlbag.drop_database

Helpers
-------

.. autofunction:: sqlbag.database_exists
.. autofunction:: sqlbag.can_select
