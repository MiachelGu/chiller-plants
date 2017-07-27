"""K-Realtime backend server. Flask App."""

from flask import json
from flask import request

import flask
import wtforms
import datetime as dt
import config as cfg
import pymongo
import pytz


app = flask.Flask(__name__)


class ListField(wtforms.Field):
    """Take a string of comma separated values, parse it to a list."""

    widget = wtforms.widgets.TextInput()

    def _value(self):
        return u",".join(self.data) if self.data else u""

    def process_formdata(self, data):
        self._data = data[0] if data else u""
        self.data = [d.strip() for d in data[0].strip(",").split(",")] if data else []


class FlexibleDateTimeField(wtforms.Field):
    """Take a string of several datatime formats and parse it to datetime object"""

    widget = wtforms.widgets.TextInput()

    def _value(self):
        return self.data.strftime("%Y-%m-%dT%H:%M:%S.%f") if self.data else ""

    def process_formdata(self, data):
        if not data:
            return u""
        allowed_fmts = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
        for fmt in allowed_fmts:
            try:
                self.data = dt.datetime.strptime(data[0], fmt)
                self._data = data[0] if data else u""
                return
            except ValueError:
                pass
        raise wtforms.ValidationError("{} is invalid".format(data))


class LogsQueryForm(wtforms.Form):
    """Form for Logs API query parameters."""

    # rather naive.. but would be okay.
    TOKEN_FMT   = "%Y%m%d%H%M%S%f"

    start       = FlexibleDateTimeField()
    end         = FlexibleDateTimeField()
    freq        = wtforms.StringField()
    fields      = ListField()
    order       = wtforms.IntegerField()
    token       = wtforms.StringField()
    limit       = wtforms.IntegerField()
    func        = wtforms.StringField()

    def validate_start(self, field):
        if not field.data:
            self.validate_end(field)
            field.data -= dt.timedelta(days=2)
        field.data = field.data.replace(tzinfo=pytz.UTC)

    def validate_end(self, field):
        if not field.data:
            field.data = dt.datetime.utcnow()
            field.data = field.data.replace(hour=0, minute=0, second=0, microsecond=0)
        field.data = field.data.replace(tzinfo=pytz.UTC)

    def validate_freq(self, field):
        if not field.data:
            field.data = "hours"
        if field.data not in ["years", "months", "days", "hours", "minutes"]:
            raise wtforms.ValidationError("{} is invalid".format(field.data))

    def validate_order(self, field):
        if not field.data:
            field.data = 1
        if field.data not in (-1, 1):
            raise wtforms.ValidationError("order 1 or ascending, -1 for descending")

    def validate_token(self, field):
        if field.data:
            try:
                field.data = dt.datetime.strptime(field.data, self.TOKEN_FMT)
                field.data = field.data.replace(tzinfo=pytz.UTC)
            except ValueError:
                raise wtforms.ValidationError("token {} is invalid".format(field.data))

    def validate_limit(self, field):
        if not field.data:
            field.data = 200
        field.data = min(field.data, 200)

    def validate_func(self, field):
        allowed_funcs = ["avg", "sum", "max", "min"]
        if not field.data:
            field.data = "avg"
        if field.data not in allowed_funcs:
            message = "func {} is invalid. Allowed: {}".format(field.data, allowed_funcs)
            raise wtforms.ValidationError(message)


@app.route("/api/v1/logs/<site>", methods=["GET"])
def logs_api(site):
    """Query for chiller plant sensor logs.

    Args:
        site    := Chiller plant ID (eg: insead)
    Query Parameters:
        start   := %Y-%m-%d, Query logs > UTC start time (default 2 days before end date)
        end     := %Y-%m-%d, Query logs <= UTC end time (default today)
        freq    := years/months/days/hours/minutes, Logs sampling rate (default hours)
        fields  := Comma separated chiller plant sensor fields (required)
        order   := 1 for ascending order, -1 for descending order (default 1)
        limit   := Integer, number of logs in the response (default 200, max allowed 200)
        func    := avg, sum, max, min Aggregate operation (default avg)
        token   := Page token (optional, default Empty)
    Example URL:
        /api/log/insead?start=2017-01-01&end=2017-01-02&limit=100&freq=hours&next=
    """
    form = LogsQueryForm(request.args)
    if not form.validate():
        return flask.make_response(json.jsonify(**form.errors), 400)

    # give token precedence to support pagination.
    start_date = form.token.data or form.start.data

    # first filter the logs by timestamp
    # Assuming timeperiod is going to be relatively smaller than collection size,
    # the B+ Tree search space would highly reduced in further operations.
    # Note: Create an index on timestamp
    step_0 = {
        "$match": {
            "timestamp": {"$gt": start_date, "$lte": form.end.data},
            "_site": site
        }
    }

    # used to group data by timestamp
    dt_format = {
        "years"   : "%Y-01-01T00:00:00.000",
        "months"  : "%Y-%m-01T00:00:00.000",
        "days"    : "%Y-%m-%dT00:00:00.000",
        "hours"   : "%Y-%m-%dT%H:00:00.000",
        "minutes" : "%Y-%m-%dT%H:%M:%S.000"
    }

    # Now, group the documents with timestamp and `group_by` as format
    group_by = dt_format.get(form.freq.data)
    step_1 = {
        "$group": {"_id": {"$dateToString": {"format": group_by, "date": "$timestamp"}}}}

    # find avg of all the `fields` mentioned in query params
    func = "${}".format(form.func.data)
    for f in form.fields.data:
        step_1["$group"][f] = {func: "${}".format(f)}

    # sort the data..
    step_2 = {"$sort": {"_id": form.order.data}}

    # limit the results (don't want irritate http)
    step_3 = {"$limit": form.limit.data}

    # query data
    db = app.config["db"]
    results = [i for i in db.log.aggregate([step_0, step_1, step_2, step_3])]

    # send the query parameters as reference (not the parsed ones...)
    params = form.data
    params["start"] = form.start._data
    params["end"] = form.end._data
    params["fields"] = form.fields._data
    if params["token"]:
        params["token"] = params["token"].strftime(form.TOKEN_FMT)

    response = {
        "results": results,
        "queryParams": params,
        "apiVersion": "v1"
    }

    # send the id of last result as page token.. but change its format
    # just to make it look like a token :p
    if len(results) > 0:
        token_id = dt.datetime.strptime(results[-1]["_id"], "%Y-%m-%dT%H:%M:%S.%f")
        response["nextPageToken"] = token_id.strftime(form.TOKEN_FMT)

    return json.jsonify(response)


@app.route("/api/info")
def api_info_page():
    return flask.render_template("api_info.html")


@app.route("/")
def index_page():
    return flask.render_template("dynamic.html")


@app.route("/view/<view_type>")
def dashboard_page(view_type):
    if view_type not in ["monthly", "daily", "dynamic"]:
        raise flask.abort(404)
    return flask.render_template("{}.html".format(view_type))


if __name__ == "__main__":
    client = pymongo.MongoClient(tz_aware=True)
    app.config["client"] = client
    app.config["db"] = client[cfg.DATABASE["db"]]
    app.run(debug=True)
