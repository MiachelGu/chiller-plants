from mongoengine import Document
from mongoengine import StringField, ComplexDateTimeField, ReferenceField, FloatField

import datetime


class Site(Document):
    name = StringField(required=True)


class Log(Document):
    timestamp = ComplexDateTimeField(required=True)
    stored_on = ComplexDateTimeField(default=datetime.datetime.now(), required=True)
    site = ReferenceField(Site, required=True)
    param = StringField(required=True)
    param_value = FloatField(required=True)
    param_type = StringField()
