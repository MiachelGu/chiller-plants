"""K-Realtime backend server. Flask App."""

from flask import json
from flask import request
from flask import render_template
from flask import make_response

import flask
import wtforms
import config as cfg
import pymongo
import datetime
import pytz


app = flask.Flask(__name__)


class LogsQueryForm(wtforms.Form):
    """Form for Logs API query parameters."""

    start = wtforms.DateTimeField(format="%Y-%m-%d")
    end = wtforms.DateTimeField(format="%Y-%m-%d")
    freq = wtforms.StringField()
    fields = wtforms.StringField()

    def validate_freq(self, field):
        if field.data is not None and \
           field.data not in ["years", "months", "days", "hours", "minutes"]:
            raise wtforms.ValidationError("{} is invalid".format(field.data))


@app.route("/api/logs/<site>", methods=["GET"])
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
    form = LogsQueryForm(request.args)
    if not form.validate():
        data = {"http_code": 400, "errors": form.errors}
        return make_response(json.jsonify(**data), 400)

    if form.freq.data == "years":
        group_by = "%Y-01-01T00:00:00.000Z"
    elif form.freq.data == "months":
        group_by = "%Y-%m-01T00:00:00.000Z"
    elif form.freq.data == "days":
        group_by = "%Y-%m-%dT00:00:00.000Z"
    elif form.freq.data == "hours":
        group_by = "%Y-%m-%dT%H:00:00.000Z"
    else:
        group_by = "%Y-%m-%dT%H:%M:%S.000Z"

    # first filter the logs by timestamp
    # Assuming timeperiod is going to be relatively smaller than data size,
    # the B+ Tree search space would highly reduced in further operations.
    # Note: Create an index on timestamp
    step_0 = {
        "$match": {"timestamp": {"$gte": form.start.data, "$lte": form.end.data}}}

    # Now, group the documents with timestamp and `group_by` as format
    step_1 = {
        "$group": {"_id": {"$dateToString": {"format": group_by, "date": "$timestamp"}}}}

    # find avg of all the `fields` mentioned in query params
    for f in form.fields.data.split(","):
        key = "${}".format(f)
        step_1["$group"][f] = {"$avg": key}

    # sort the data..
    step_2 = {"$sort": {"_id": 1}}

    # query data
    # TODO: Pagination. This could be a pain in the ass.
    db = app.config["db"]
    data = [i for i in db.log.aggregate([step_0, step_1, step_2])]

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
