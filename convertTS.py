import pandas as pd
from pandas.core.common import _maybe_box_datetimelike
import config
from pymongo import MongoClient
import time
from bson.son import SON
from datetime import datetime

db = config.get_db()
sensors = db.sensors
ids     = db.ids

sensors.create_index([("id", pymongo.ASCENDING)], unique=True, sparse=True)
sensors.create_index([("ts", pymongo.DESCENDING)], unique=True, sparse=True)

def updateTS(_ID):
    step0 = time.time()
    pipeline = [
                    { "$match": { "id": _ID } },
                    { "$sort" : SON([("ts", 1)]) }
                ]
    try:
        _TEST = pd.DataFrame(list(sensors.aggregate(pipeline, allowDiskUse = True)))
        print "Total rows:", _TEST.__len__()
        print "Data loaded in %ss" % (round((time.time() - step0), 1))
        _TEST.ts = pd.to_datetime(_TEST.ts)
        
        #https://stackoverflow.com/questions/20167194/insert-a-pandas-dataframe-into-mongodb-using-pymongo/49127811
        my_list = [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(_TEST.columns, row) if v != None and v == v) for row in _TEST.values]
        bulk = sensors.initialize_unordered_bulk_op()
        for i in range (0, len(my_list)):
            bulk.find( { '_id':  my_list[i]["_id"]}).update({ '$set': {  "ts" : my_list[i]["ts"] }})
        
        #https://stackoverflow.com/questions/46458618/how-can-i-update-a-whole-collection-in-mongodb-and-not-document-by-document
        print bulk.execute()
        # output = list(sensors.find({"id": _ID}))
        # print output[0]
        print "Completed ID %s in %ss" % (_ID, (round((time.time() - step0), 1)))
        # return output
    except:
        print "ID %s does not exist." % _ID

# output = updateTS(10)
updateTS(4)

def upload1(id, i, freq, days):
    sensor      = ids.find_one({'id': int(id)})
    install_date = datetime.strptime(str(sensor["date"]), '%Y-%m-%d %H:%M:%S')
    step0 = time.time()
    pipeline = [
                { "$match": { "id": int(id), "ts": {"$gt": install_date } } },
                { "$sort" : SON([("ts", 1)]) },
                { "$limit": (freq*24*days) }
            ]
    sensor_data     = pd.DataFrame(list(sensors.aggregate(pipeline, allowDiskUse = True)))
    step1 = time.time()
    print i, ": Data loaded... (%ss)" % (round((step1 - step0), 1))
    return sensor_data

def upload2(id, i):
    sensor      = ids.find_one({'id': int(id)})
    install_date = datetime.strptime(str(sensor["date"]), '%Y-%m-%d %H:%M:%S')
    step0 = time.time()
    pipeline = [
                { "$match": { "id": int(id), "ts": {"$gt": install_date } } },
                { "$sort" : SON([("ts", 1)]) }
            ]
    sensor_data     = sensors.aggregate(pipeline, allowDiskUse = True)
    data = pd.DataFrame([x for x in sensor_data])
    step1 = time.time()
    print i, ": Data loaded... (%ss)" % (round((step1 - step0), 1))
    return data


def read_mongo(collection, query=None, chunksize = 1000, page_num=1, no_id=True):
    # Calculate number of documents to skip
    skips = chunksize * (page_num - 1)
    # Sorry, this is in spanish
    # https://www.toptal.com/python/c%C3%B3digo-buggy-python-los-10-errores-m%C3%A1s-comunes-que-cometen-los-desarrolladores-python/es
    if not query:
        query = {}
    # Make a query to the specific DB and Collection
    cursor = collection.find(query).skip(skips).limit(chunksize)
    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))
    # Delete the _id
    if no_id:
        del df['_id']
    return df

def upload3(id, j):
    step0 = time.time()
    frames = []
    for i in range(1,50):
        frames.append(read_mongo(sensors,{"id":id},page_num=i))
    step1 = time.time()
    df = pd.concat(frames)
    print j, ": Data loaded... (%ss)" % (round((step1 - step0), 1))
    return df

pipeline = [
                { "$match": { "id": int(id), "ts": {"$gt": install_date } } },
                { "$sort" : SON([("ts", 1)]) }
            ]
    sensor_data     = sensors.aggregate(pipeline, allowDiskUse = True)


def read_mongo(collection, chunksize = 1000, page_num=1, no_id=True):
    # Calculate number of documents to skip
    skips = chunksize * (page_num - 1)
    print skips
    # Sorry, this is in spanish
    # https://www.toptal.com/python/c%C3%B3digo-buggy-python-los-10-errores-m%C3%A1s-comunes-que-cometen-los-desarrolladores-python/es
    # Make a query to the specific DB and Collection
    pipeline = [
                { "$match": { "id": 209, "ts": {"$gt": install_date } } },
                { "$skip" : skips},
                { "$limit": chunksize },
                { "$sort" : SON([("ts", 1)]) },
            ]
    cursor     = collection.aggregate(pipeline, allowDiskUse = True)
    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))
    # Delete the _id
    if no_id:
        del df['_id']
    return df

def upload4(i):
    step0 = time.time()
    frames = []
    for i in range(1,50):
        frames.append(read_mongo(sensors,page_num=i))
    step1 = time.time()
    df = pd.concat(frames)
    print j, ": Data loaded... (%ss)" % (round((step1 - step0), 1))
    return df

for i in range(0,5):
    d1 = upload1(209,i)

for i in range(0,3):
    d2 = upload2(209,i)

for j in range(0,5):
    d3 = upload3(209,j)

for j in range(0,5):
    d4 = upload4(j)


def idlimit(page_size, last_id=None):
        if last_id is None:
            # When it is first page
            cursor = sensors.find({"id":209}).limit(page_size)
        else:
            cursor = sensors.find({{'_id': {'$gt': last_id}}, {"id":209}}).limit(page_size)
        # Get the data      
        data = [x for x in cursor]
        if not data:
            # No documents left
            return None, None
        # Since documents are naturally ordered with _id, last document will
        # have max id.
        last_id = data[-1]['_id']
        # Return data and last_id
        return data, last_id



