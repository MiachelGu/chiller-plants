import pymongo
import datetime
import pytz


client = pymongo.MongoClient()
db = client.dashboard

start = datetime.datetime(2016,12,31, tzinfo=pytz.UTC)
end = start + datetime.timedelta(days=60)

print(start.isoformat())
print(end.isoformat())

query = {
    "timestamp": {"$gte": start.isoformat(), "$lte": end.isoformat()}
}

print(db.log.find_one(query))
