"""K-Realtime backend server. Flask App."""

from flask import json
from flask import request
from flask import render_template
from flask import make_response

import flask
import wtforms
import datetime as dt
import config as cfg
import pymongo
import pytz


app = flask.Flask(__name__)


class LogsQueryForm(wtforms.Form):
    """Form for Logs API query parameters."""

    # rather naive.. but would be okay.
    TOKEN_FMT = "%Y%m%d%H%M%S%fZ"
    DATE_FMT = "%Y-%m-%dT%H:%M:%S.000Z"

    start = wtforms.DateTimeField(format="%Y-%m-%d")
    end = wtforms.DateTimeField(format="%Y-%m-%d")
    freq = wtforms.StringField(default="hours")
    fields = wtforms.StringField()
    order = wtforms.IntegerField(default=1)
    token = wtforms.StringField()
    limit = wtforms.IntegerField(default=1)
    func = wtforms.StringField(default="avg")

    def validate_func(self, field):
        allowed_funcs = ["avg", "sum", "max", "min"]
        if field.data not in allowed_funcs:
            message = "func {} is invalid. Allowed: {}".format(field.data, allowed_funcs)
            raise wtforms.ValidationError(message)

    def validate_token(self, field):
        try:
            field.data = dt.datetime.strptime(field.data, self.TOKEN_FMT)
        except ValueError:
            raise wtforms.ValidationError("token {} is invalid".format(field.data))

    def validate_limit(self, field):
        field.data = min(field.data, 200)

    def validate_order(self, field):
        if field.data not in (-1, 1):
            raise wtforms.ValidationError("order 1 or ascending, -1 for descending")

    def validate_freq(self, field):
        if field.data is not None and \
           field.data not in ["years", "months", "days", "hours", "minutes"]:
            raise wtforms.ValidationError("{} is invalid".format(field.data))


@app.route("/api/logs/<site>", methods=["GET"])
def logs_api(site):
    """Query for chiller plant sensor logs.

    REST URL: GET /api/logs
    Args:
        site    := Chiller plant ID (eg: insead)
    Query Parameters:
        start   := %Y-%m-%d, Query logs > start time (UTC)
        end     := %Y-%m-%d, Query logs <= end time (UTC)
        freq    := years/months/days/hours/minutes, Logs sampling rate (default minutes)
        field   := Comma separated chiller plant sensor fields
        order   := 1 (ascending order), -1 (descending order)
        limit   := Integer, number of logs in the response (max 200)
        func    := Aggregate operation (avg/sum/max/min)
        token   := Next page token
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

    # start date. give token precedence.
    start_date = form.token.data or form.start.data

    # set timzones
    start_date = start_date.replace(tzinfo=pytz.UTC)
    form.end.data = form.end.data.replace(tzinfo=pytz.UTC)

    # first filter the logs by timestamp
    # Assuming timeperiod is going to be relatively smaller than data size,
    # the B+ Tree search space would highly reduced in further operations.
    # Note: Create an index on timestamp
    step_0 = {
        "$match": {
            "timestamp": {"$gt": start_date, "$lte": form.end.data},
            "_site": site
        }
    }

    # Now, group the documents with timestamp and `group_by` as format
    step_1 = {
        "$group": {"_id": {"$dateToString": {"format": group_by, "date": "$timestamp"}}}}

    # find avg of all the `fields` mentioned in query params
    func = "${}".format(form.func.data)
    for f in form.fields.data.split(","):
        key = "${}".format(f)
        step_1["$group"][f] = {func: key}

    # sort the data..
    step_2 = {"$sort": {"_id": form.order.data}}

    # limit the results (don't want irritate http)
    step_3 = {"$limit": form.limit.data}

    # query data
    # TODO: Pagination. This could be a pain in the ass.
    db = app.config["db"]
    results = [i for i in db.log.aggregate([step_0, step_1, step_2, step_3])]

    # conversion: string -> date -> string
    token_id = dt.datetime.strptime(results[-1]["_id"], form.DATE_FMT)
    token_id = token_id.strftime(form.TOKEN_FMT)

    # send the query parameters as reference
    params = form.data
    params["start"] = params["start"].strftime(form.DATE_FMT)
    params["end"] = params["end"].strftime(form.DATE_FMT)
    params["token"] = params["token"].strftime(form.TOKEN_FMT)

    data = {"token": token_id, "results": results, "params": params}
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
