"""K-Realtime backend server. Flask App."""

from flask import Flask
from flask import render_template

import config as cfg
import mongoengine as mg


app = Flask(__name__)


@app.route("/")
def index_page():
    return render_template("index.html")


if __name__ == "__main__":
    app.config.update([(k, getattr(cfg, k)) for k in dir(cfg) if not k.startswith("__")])
    mg.connect(**app.config["DATABASE"])
    app.run(debug=True)
