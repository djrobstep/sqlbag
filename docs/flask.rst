Database sessions for Flask apps
================================

You can set up auto-committing, thread safe database sessions as easily as this:

`FS` creates an per-request session proxy.

`session_setup` wires these `FS` objects up so that the database activity for each request's transaction is committed.

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


Session setup
-------------

.. automodule:: sqlbag.flask
.. autofunction:: sqlbag.flask.FS
.. autofunction:: sqlbag.flask.session_setup

* :ref:`genindex`
