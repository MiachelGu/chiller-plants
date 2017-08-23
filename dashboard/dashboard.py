"""K-Realtime backend server. Flask App."""
import datetime as dt
import config as cfg
import numpy as np
import pandas as pd
import flask
import pymongo
import pytz
import process
import forms

from flask import json
from flask import request


app = flask.Flask(__name__)


def query_logs(site, fields, start, end, freq="minutes", aggregate="avg", order=1):
    """Query for Chiller Plants data.

    Args:
        site        := string, Chiller plant ID (eg: insead, np)
        fields      := List, Chiller plant parameters (eg: cwshdr)
        start       := datetime, search starting this period
        end         := datetime, search until this period
        aggregate   := string, aggregate function to apply
        order       := int, 1 implies ascending, -1 implies descending
    Returns:
        Pymongo Cursor; Iterate this.
    """
    # first filter the logs by timestamp
    # Assuming timeperiod is going to be relatively smaller than collection size,
    # the B+ Tree search space would highly reduced in further operations.
    # Note: Create an index on timestamp
    step_0 = {
        "$match": {
            "timestamp": {"$gt": start, "$lte": end},
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
    group_by = dt_format.get(freq)
    step_1 = {
        "$group": {"_id": {"$dateToString": {"format": group_by, "date": "$timestamp"}}}}

    # Apply aggregate on all the `fields`
    # Eg: "$group": { "cwshdr": { "avg": "$cwshdr" } }
    func = "${}".format(aggregate)
    for f in fields:
        step_1["$group"][f] = {func: "${}".format(f)}

    # sort the data..
    step_2 = {"$sort": {"_id": order}}

    # query data
    db = app.config["db"]
    cursor = db.log.aggregate([step_0, step_1, step_2])
    
    # Let's give the calling function the freedom to 
    # query the way.. he wants. Why burden with O(N)..
    return cursor
    
    
def preprocess_flow_1(df, cols):
    """Preprocess chiller plant logs.

    Args:
        df  := Pandas DataFrame with timestamp as Index
    Returns:
        Processed pandas dataframe
    """
    df = process.replace_nulls(df, cols=cols)
    df = process.replace_with_near(df, cols=cols)
    df = process.smooth_data(df, cols=cols)
    return df


def find_frequency_based_abnormalities(train, test, limit=(0.1, 0.9), delta=10, field="value"):
    """Find abnormalities using frequency per hour of past values.

    Args:
        train   := pandas DataFrame used for calculating frequencies
        test    := pandas DataFrame to find abnormalities
        limit   := tuple, (min, max) threshold quartiles
        delta   := int, sensitivity in calculating rate of change
        field   := string, field value in train/test on which abnormalities are found
    Returns:
        pandas Series, with `test` index, value represents abnormal or not
    """
    if test.shape[0] == 0:
        return test[field]

    # hours
    train["hour"] = train.index.hour
    test["hour"] = test.index.hour

    # rate of change
    train["rate"] = (train[field] - train[field].shift(delta)).fillna(0)
    test["rate"] = (test[field] - test[field].shift(delta)).fillna(0)

    # upper and lower limits grouped by hour
    min_per_hr = train.groupby(["hour"]).quantile(limit[0]).rate
    max_per_hr = train.groupby(["hour"]).quantile(limit[1]).rate

    # max and min limits of test data (based on train data)
    test["min_rate"] = test.hour.apply(lambda x: min_per_hr.iloc[int(x)])
    test["max_rate"] = test.hour.apply(lambda x: max_per_hr.iloc[int(x)])

    # is this abnormal?
    test["abnormal"] = (test.rate < test.min_rate) | (test.rate > test.max_rate)

    return test[ ["min_rate", "max_rate", "abnormal", "rate"] ]


@app.route("/api/v1/abnormalities/<site>", methods=["GET"])
def frequency_based_abnormalities_api(site):
    """Find abnormalities in Chiller plant sensor logs.

    Args:
        site    := Chiller Plant ID (eg: insead)
    Query Parameters
        start   := %Y-%m-%d, Query logs > UTC start time (default 2 days before end date)
        end     := %Y-%m-%d, Query logs <= UTC end time (default today)
        freq    := years/months/days/hours/minutes, Logs sampling rate (default hours)
        field  := Find abnormalities in this field data (required)
    """
    form = forms.AbnormalitiesV1QueryForm(request.args)
    if not form.validate():
        return flask.make_response(json.jsonify(**form.errors), 400)

    # query data to find abnormalities
    test_data_query = query_logs(
        site=site,
        fields=[form.field.data],
        start=form.start.data,
        end=form.end.data,
        freq=form.freq.data,
        aggregate="avg")
    data = [
        (i[form.field.data], dt.datetime.strptime(i["_id"], "%Y-%m-%dT%H:%M:%S.%f"))
        for i in test_data_query
    ]

    test_df = pd.DataFrame(data, columns=("value", "timestamp")).set_index("timestamp")
    test_df = preprocess_flow_1(test_df, cols=["value"])

    # get data to calculate frequencies (last 15 days.. )
    lookback = 30
    train_data_query = query_logs(
        site=site,
        fields=[form.field.data],
        start=form.start.data - dt.timedelta(days=lookback),
        end=form.start.data,
        freq=form.freq.data,
        aggregate="avg")
    data = [
        (i[form.field.data], dt.datetime.strptime(i["_id"], "%Y-%m-%dT%H:%M:%S.%f"))
        for i in train_data_query
    ]
    train_df = pd.DataFrame(data, columns=("value", "timestamp")).set_index("timestamp")
    train_df = preprocess_flow_1(train_df, cols=["value"])

    # find abnormalities
    resp_df = find_frequency_based_abnormalities(train_df, test_df)

    # prepare response
    results = []
    for idx, r1, r2 in zip(test_df.index, resp_df.values, test_df.value.values):
        results.append({
            "_id": idx.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "min_value": r1[0],
            "max_value": r1[1],
            "abnormal": r1[2],
            "value": r2, # this value is "preprocessed" one. Its not "exactly" same as original.
            "rate": r1[3]
        })

    params = form.data
    params["start"] = form.start._data
    params["end"] = form.end._data
    
    response = {
        "results": results,
        "queryParams": params,
        "apiVersion": "v1"
    }

    return json.jsonify(response)


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
    form = forms.LogsQueryForm(request.args)
    if not form.validate():
        return flask.make_response(json.jsonify(**form.errors), 400)

    # query data..
    # Note: give preference to token (for pagination) -- but this is meaningless
    # as I removed `limit` feature.. 
    cursor = query_logs(
        site=site,
        fields=form.token.data or form.fields.data,
        start=form.start.data,
        end=form.end.data,
        freq=form.freq.data,
        aggregate=form.func.data,
        order=form.order.data)
    results = [i for i in cursor]

    # send the query parameters as reference (not the parsed ones...)
    params = form.data
    params["start"] = form.start._data
    params["end"] = form.end._data
    params["fields"] = form.fields._data
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
