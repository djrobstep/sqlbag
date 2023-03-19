from flask import Flask
from sqlalchemy import text

from sqlbag.flask import FS, proxies, session_setup

s = proxies.s


def get_app():
    a = Flask(__name__)
    a.s = FS("postgresql:///example", echo=True)
    session_setup(a)
    return a


app = get_app()


@app.route("/")
def hello():
    # returns 'Hello World!' as a response
    return s.execute(text("select 'Hello world!'")).scalar()


if __name__ == "__main__":
    app.run()
