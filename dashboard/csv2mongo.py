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

import pymongo
import argparse
import pandas as pd
import numpy as np
import pytz


parser = argparse.ArgumentParser(description="Load sensor logs into MongoDB from CSV files")
parser.add_argument("--site", type=str, help="Chiller Plant site ID")
parser.add_argument("--db", type=str, help="MongoDB database name")
parser.add_argument("--host", type=str, help="MongoDB Host")
parser.add_argument("--port", type=int, help="MongoDB Port")
parser.add_argument("--data", type=str, help="Path to CSV file")
args = parser.parse_args()


def main():
    # load data as dataframe
    print("Loading data now.. ")
    df = pd.read_csv(args.data, low_memory=False)
    df = df.replace("\\N", np.nan)
    df = df.rename(columns={"Time Stamp": "timestamp"})

    # update data types
    dtypes = dict([(col, np.float64) for col in df.columns if col != "timestamp"])
    df = df.astype(dtypes)
    df.timestamp = pd.to_datetime(df.timestamp)
    df.timestamp = df.timestamp.apply(lambda t: t.tz_localize(pytz.UTC))

    # connect to database
    print("Connecting to database.. ")
    client = pymongo.MongoClient(host=args.host, port=args.port, tz_aware=True)
    db = client[args.db]

    # get chiller plant site
    if db.site.find_one({"_id": args.site}) is None:
        raise Exception("Chiller Plant site ID is not found in the database!")

    def save_to_db(row):
        save_to_db.bulk = getattr(save_to_db, "bulk", [])
        row["_site"] = args.site
        save_to_db.bulk.append(row.to_dict())
        if len(save_to_db.bulk) > 30 ** 3 or row.name == len(df)-1:
            print("Saving at {0}...".format(row.name))
            db.log.insert_many(save_to_db.bulk)
            save_to_db.bulk = []

    # Iterate
    df.apply(save_to_db, axis=1)
    print("Done!")


if __name__ == "__main__":
    main()
