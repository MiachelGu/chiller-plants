import pymongo
import numpy as np
import pandas as pd
import datetime as dt
import pytz
import pprint
import process

client = pymongo.MongoClient(tz_aware=True)


def preprocess_flow(df):
    cols = ["value"]
    df = process.replace_nulls(df, cols=cols)
    df = process.replace_with_near(df, cols=cols)
    df = process.smooth_data(df, cols=cols)
    df = process.get_normalized_df(df, cols=cols)
    return df


def find_frequency_based_abnormalities(train, test, limit=(0.1, 0.9), delta=10, field="value"):
    # hours
    train["hour"] = train.index.hour
    test["hour"] = test.index.hour

    # rate of change
    train["rate"] = (train[field] - train[field].shift(delta)).fillna(method="pad")
    test["rate"] = (test[field] - test[field].shift(delta)).fillna(method="pad")

    # upper and lower limits grouped by hour
    min_per_hr = train.groupby(["hour"]).quantile(limit[0]).rate
    max_per_hr = train.groupby(["hour"]).quantile(limit[1]).rate

    # max and min limits of test data (based on train data)
    test["min_value"] = test.hour.apply(lambda x: min_per_hr.iloc[int(x)])
    test["max_value"] = test.hour.apply(lambda x: max_per_hr.iloc[int(x)])

    # is this abnormal?
    is_abnormal = (test[field] < test.min_value) | (test[field] > test.max_value)

    return is_abnormal


def main():
    # database
    db = client.dashboard

    # get historic data for calculating frequency
    start_date = dt.datetime(2017, 1, 1, tzinfo=pytz.UTC)
    end_date = dt.datetime(2017, 1, 15, tzinfo=pytz.UTC)
    query = {"timestamp": {"$gt": start_date, "$lte": end_date}}
    train_df = pd.DataFrame(
        [(i["cwshdr"], i["timestamp"]) for i in db.log.find(query)], 
        columns=("value", "timestamp")).set_index("timestamp")
    train_df = preprocess_flow(train_df)

    # get test data
    start_date = dt.datetime(2017, 1, 16, tzinfo=pytz.UTC)
    end_date = dt.datetime(2017, 1, 16, 1, tzinfo=pytz.UTC)
    query = {"timestamp": {"$gt": start_date, "$lte": end_date}}
    test_df = pd.DataFrame(
        [(i["cwshdr"], i["timestamp"]) for i in db.log.find(query)], 
        columns=("value", "timestamp")).set_index("timestamp")
    test_df = preprocess_flow(test_df)

    resp = find_frequency_based_abnormalities(train_df, test_df)

    pprint.pprint(resp)





if __name__ == "__main__":
    main()


# data = find_abnormalities("cwshdr", start, end)
# pprint.pprint(data)
