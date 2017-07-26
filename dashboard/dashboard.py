"""K-Realtime backend server. Flask App."""

from flask import Flask
from flask import json
from flask import request
from flask import render_template
from flask import make_response

import flask
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
        start = String <%Y-%m-%d>, starting date
        end = String <%Y-%m-%d>, ending date
        freq = String (years/months/days/hours/minutes), sampling frequency
        field = String, parameter of chiller plant
    Example URL:
        /api/log/insead?start=2017-01-01&end=2017-01-02&limit=100&freq=hours&next=
    """
    start_date = datetime.datetime.strptime(request.args["start"], "%Y-%m-%d").replace(tzinfo=pytz.UTC)
    end_date = datetime.datetime.strptime(request.args["end"], "%Y-%m-%d").replace(tzinfo=pytz.UTC)
    field = request.args["field"]
    freq = request.args["freq"]

    if freq == "years":
        group_by = "%Y-01-01T00:00:00.000Z"
    elif freq == "months":
        group_by = "%Y-%m-01T00:00:00.000Z"
    elif freq == "days":
        group_by = "%Y-%m-%dT00:00:00.000Z"
    elif freq == "hours":
        group_by = "%Y-%m-%dT%H:00:00.000Z"
    else:
        group_by = "%Y-%m-%dT%H:%M:%S.000Z"

    pipeline = [
        {
            "$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}
        },
        {
            "$group": {
                "_id": {"$dateToString": { "format": group_by, "date": "$timestamp"}},
                "value": {"$avg": "${}".format(field)}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    db = app.config["db"]
    data = [i for i in db.log.aggregate(pipeline)]
    return json.jsonify(data)


@app.route("/")
def index_page():
    return render_template("dynamic.html")


@app.route("/view/<view_type>")
def dashboard_page(view_type):
    if view_type not in ["monthly", "daily", "dynamic"]:
        raise flask.abort(404)
    return render_template("{}.html".format(view_type))


if __name__ == "__main__":
    client = pymongo.MongoClient(tz_aware=True)
    app.config["client"] = client
    app.config["db"] = client[cfg.DATABASE["db"]]
    app.run(debug=True)
