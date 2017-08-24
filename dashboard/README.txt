K-RealTime Dashboard
====================

Environment
-----------

Python 3.6

Development setup instructions
-------------------------------

1. Install Tensorflow, Keras on the system
2. Install MongoDB 
2. pip install -r requirements.txt


Setup Database
---------------

Use csv2mongo.py script to load Chiller Plant logs into MongoDB.
Docs in the script may offer insight. It's just a customized alternative Mongo
already offers out of the box.

$ python csv2mongo.py --help

$ python csv2mongo.py
    --db=dashboard [database name]
    --host=localhost [database host name]
    --port=27017 [database port name]
    --site=np --[dataset chiller plant site. eg. North Point, np]
    --data=/c/path-to-csv.csv


Start Dashboard
----------------

$ python dashboard.py


Notes
-----

1. I think ML model isn't releasing memory after usage.. Check this out!!
