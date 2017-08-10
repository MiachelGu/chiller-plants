import pymongo
import numpy as np
import pandas as pd
import datetime as dt
import pytz
import pprint

client = pymongo.MongoClient(tz_aware=True)
db = client.dashboard
start = dt.datetime(2017,1,1, 1,0,0,tzinfo=pytz.UTC)
end = dt.datetime(2017,1,1, 1,5,0,tzinfo=pytz.UTC)


def find_abnormalities(field, start, end, lookback=1, freq="minutes"):
    """Find abnormalities in chiller plant timeseries. 

    Args
        field     := String, chiller plant parameter
        start     := Datetime, start time of time series
        end       := Datetime, end time of time series
        lookback  := Int, compare each time series value x(t) with past value x(t-lookback)
        freq      := String, frequence of time series
    Returns
        List, timestamp and values that are identified as abnormal
    """
    delta = dt.timedelta(**{freq: lookback})

    # x1 := [t, t-1, t-2, t-3, ... t-N]
    #
    # x2 := [t-1, t-2, t-3, t-4, ... t-N-1] for lookback = 1
    # x2 := [t-2, t-3, t-4, t-5, ... t-N-2] for lookback = 2...
    #
    # This could be done in Pandas with fewer lines but I guess performance
    # is better in Mongo.
    step0 = {
        "$facet": {
            "x1": [ 
                {
                    "$match": {
                        "timestamp": {"$gt": start, "$lte": end}
                    }
                },
                {
                    "$sort": {"_id": -1}
                },
                {
                    "$project": {
                        field: 1, "timestamp": 1, "_id": 0,
                    }
                }
            ],

            "x2": [
                {
                    "$match": {
                        "timestamp": {"$gt": start-delta, "$lte": end-delta}
                    }
                },
                {
                    "$sort": {"_id": -1}
                },
                {
                    "$project": {
                        field: 1, "timestamp": 1, "_id": 0,
                    }
                }
            ]
        }
    }

    # Extract data. 
    result = db.log.aggregate([step0]).next()
    x1 = pd.DataFrame(result["x1"])
    x2 = pd.DataFrame(result["x2"])

    # Calculate (x1-x2). 
    # TODO: Can we do this directly in Mongo?
    first_diff = (x1-x2).drop("timestamp", axis=1)

    # Filter abnormalities
    window_size = 50 # 50-units back.. 
    abs_mean_func = lambda x: np.abs(np.mean(x))
    mean = first_diff.rolling(window_size, min_periods=1).apply(abs_mean_func)



    # Filter out abnormal values in x1.
    # Definition(s) of abnormality
    return result



data = find_abnormalities("cwshdr", start, end)
pprint.pprint(data)

