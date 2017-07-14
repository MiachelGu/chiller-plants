"""Load existing logs into MongoDB."""

from mongoengine import connect

import argparse
import models
import pandas as pd
import numpy as np


parser = argparse.ArgumentParser(description="Load sensor logs into MongoDB from CSV files")
parser.add_argument("--site", type=str, help="Chiller plant site")
parser.add_argument("--db", type=str, help="MongoDB database name")
parser.add_argument("--host", type=str, help="MongoDB Host")
parser.add_argument("--port", type=int, help="MongoDB Port")
parser.add_argument("--data", type=str, help="Path to CSV file")
args = parser.parse_args()


def main():
    print("Loading data now.. ")

    # load data as dataframe
    df = pd.read_csv(args.data)
    df = df.replace("\\N", np.nan)
    df = df.rename(columns={"Time Stamp": "timestamp"})

    # update data types
    dtypes = dict([(col, np.float64) for col in df.columns])
    dtypes["timestamp"] = "datetime64[ns]"
    df = df.astype(dtypes)
    
    print("Connecting to database.. ")

    # connect to database
    connect(db=args.db, host=args.host, port=args.port)

    # get chiller plant site
    site = models.Site.objects(name=args.site).get()

    def save_to_db(row):
        bulk = save_to_db.bulk
        data = row.to_dict()
        timestamp = data.pop("timestamp")
        for param, value in data.iteritems():
            log = models.Log(timestamp=timestamp, site=site, param=param, param_value=value)
            save_to_db.bulk.append(log)
            if len(bulk) > 10 ** 3:
                models.Log.objects.insert(bulk)
                save_to_db.bulk = []
        if len(bulk) > 0:
            models.Log.objects.insert(bulk)
            save_to_db.bulk = []

    # use this for bulk inserts
    save_to_db.bulk = []

    # Iterate
    print("Saving data.. ")
    df.apply(save_to_db, axis=1)
    
    print("Done!")


if __name__ == "__main__":
    main()
