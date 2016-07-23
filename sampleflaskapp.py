from sqlbag.flask import FS, session_setup

s = FS('postgresql:///example')

from flask import Flask
app = Flask(__name__)

session_setup(app)

@app.route("/")
def hello():
    # returns 'Hello World!' as a response
    return s.execute("select 'Hello world!'").scalar()

if __name__ == "__main__":
    app.run()
