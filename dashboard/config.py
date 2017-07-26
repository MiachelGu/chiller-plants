"""Configuration settings for flask app."""

import datetime
import pytz

# database configuration settings
DATABASE = {
    "db": "dashboard",
    "host": "localhost",
    "port": 27017,
    "user": None,
    "password": None
}

DEBUG = True

# assumes current time as this while processing queries
# useful for debugging. set this to None in production..
CURRENT_TIME = datetime.datetime(2017, 1, 1, tzinfo=pytz.UTC)
