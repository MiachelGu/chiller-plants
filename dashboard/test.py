import pymongo
import datetime
import pytz


client = pymongo.MongoClient(tz_aware=True)
db = client.dashboard

start = datetime.datetime(2017,1,1, tzinfo=pytz.UTC)
end = start + datetime.timedelta(minutes=30)

print(start.isoformat())
print(end.isoformat())

pipeline = [
    {
        "$match": {"timestamp": {"$gte": start, "$lt": end}}
    },
    {
        "$group": {
            "_id": {"$dateToString": { "format": "%Y-%m-%d %H:%M", "date": "$timestamp"}},
            "value": {"$avg": "$cwshdr"}
        }
    }
]

data = [i for i in db.log.aggregate(pipeline)]
print(data[-1])
print(len(data))
