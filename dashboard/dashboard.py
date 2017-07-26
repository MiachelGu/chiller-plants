"""K-Realtime backend server. Flask App."""

from flask import Flask
from flask import json
from flask import request
from flask import render_template

import config as cfg
import pymongo
import datetime
import pytz


app = Flask(__name__)


@app.route("/api/log/<site>", methods=["GET"])
def logs_api(site):
    """Query for chiller plant sensor logs.

    REST URL: GET /api/log/<site>
        site := Chiller plant site
    Query Parameters:
        start = String <%Y-%m-%d>, starting date [optional]
        end = String <%Y-%m-%d>, ending date [optional]
        count = Integer, maximum 200, max number of logs returned [optional]
        next = String, next page token [optional]
        freq = String (years/months/days/hours/minutes), sampling frequency [optional]
        fields = String, comma separated list of log fields [optional]
    Example URL:
        /api/log/insead?start=2017-01-01&end=2017-01-02&count=100&freq=hours&next=
    """
    end_date = datetime.datetime(2017, 1, 2, tzinfo=pytz.UTC)
    start_date = end_date - datetime.timedelta(minutes=30)

    query = {
        "timestamp": {
            "$gt":  start_date, "$lte": end_date
        }
    }

    db = app.config["db"]
    data = []
    for row in db.log.find(query):
        row.pop("_id")
        data.append(row)

    return json.jsonify(data)
    
        

@app.route("/")
def index_page():
    return render_template("index.html")


if __name__ == "__main__":
    client = pymongo.MongoClient(tz_aware=True)
    app.config["client"] = client
    app.config["db"] = client[cfg.DATABASE["db"]]
    app.run(debug=True)
