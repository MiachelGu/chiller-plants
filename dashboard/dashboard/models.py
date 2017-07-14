"""Database models for the Dashboard.

Some MongoDB models are inherited from `DynamicDocument` given the
variety of parameters sent by various chiller plant sensors.
It would be cumbersome to maintain all attributes. However, by maintaining 
a separate collection for each chiller plant would make things less difficult.
However, there are *many* chiller plants. 
""" 

from mongoengine import DynamicDocument
from mongoengine import StringField, ComplexDateTimeField, ReferenceField, FloatField

import datetime


class Site(DynamicDocument):
    name = StringField(required=True)


class Log(DynamicDocument):
    timestamp = ComplexDateTimeField(required=True)
    stored_on = ComplexDateTimeField(default=datetime.datetime.now(), required=True)
    site = ReferenceField(Site, required=True)
