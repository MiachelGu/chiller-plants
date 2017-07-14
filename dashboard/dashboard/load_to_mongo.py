"""Load existing logs into MongoDB.

How to use the script:

python load_to_mongo.py
    --db=dashboard [database name]
    --host=localhost [database host name]
    --port=27017 [database port name]
    --site=np --[dataset chiller plant site. eg. North Point, np]
    --data=/c/path-to-csv.csv

To implement:
    Add optional arguments to pass username and password of database
"""

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
        log = models.Log(**data)
        save_to_db.bulk.append(log)
        if len(bulk) > 30 ** 3:
            models.Log.objects.insert(bulk)
            save_to_db.bulk = []

    # use this for bulk inserts
    save_to_db.bulk = []

    # Iterate
    print("Saving data.. ")
    df.apply(save_to_db, axis=1)

    # Finally,
    if len(save_to_db.bulk) > 0:
        models.Log.objects.insert(save_to_db.bulk)
        save_to_db.bulk = []
    
    print("Done!")


if __name__ == "__main__":
    main()
