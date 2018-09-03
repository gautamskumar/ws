from datetime import datetime
from datetime import timedelta
import pymongo
import config
from bson.son import SON
import numpy as np
import math
import pandas as pd
from pandas.core.common import _maybe_box_datetimelike

db        = config.get_db()
QC_params = db.QC_params
sensors   = db.sensors
ids       = db.ids

### FOR TEMP ###

def temp(in_testing, params):
    sets = params
    deployed = map(int, in_testing.split(','))

    pipeline = [
                { "$match": { "id": { "$in": deployed } } },
                { "$group": {"_id": "$id", "t1": { "$push": "$t1" }, "h": { "$push": "$h" }, "ts": { "$push": "$ts" } } },
                { "$sort" : SON([("ts", 1)]) }
                ]
    data    = list(sensors.aggregate(pipeline, allowDiskUse = True))
    dicts = []

    ### Set Sample size
    sample  = sets["size"]
    tScore  = sets["tScore"]
    ###
    for d in data:
        uploads = []
        uploads.append([{"t": d["t1"][i], "h": d["h"][i], "ts": d["ts"][i]} for i in range(-1*sample, 0)])
        tlist = []
        hlist = []
        for upload in uploads[0]:
            tlist.append(upload["t"])
            hlist.append(upload["h"])
        dictQC = {
                    "id"     : d["_id"],
                    "uploads": uploads,
                    "tAvg"   : round(np.mean(tlist), 1),
                    "hAvg"   : round(np.mean(hlist), 1),
                    "tMOE"   : round(np.std(tlist)/math.sqrt(sample)*tScore, 1),
                    "hMOE"   : round(np.std(hlist)/math.sqrt(sample)*tScore/np.mean(hlist)*100,1)

                }
        dicts.append(dictQC)
    return dicts

### FOR RAIN ###

def rain(in_testing, params):
    sets = params
    deployed = map(int, in_testing.split(','))

    pipeline = [
                { "$match": { "id": 2000 } },
                { "$group": {"_id": "$ts", "r1": { "$last": "$t1" }, "r2": { "$last": "$h" }, "r3": { "$last": "$r" } } },
                { "$sort" : SON([("_id", -1)]) }
                ]
    data    = list(sensors.aggregate(pipeline, allowDiskUse = True))
    dicts = []

    ### Set Sample size
    sample  = sets["size"]
    tScore  = sets["tScore"]
    ###
    d0 = pd.DataFrame(data)
    df = d0.rename(columns={'_id':'ts'})

    # Offset by one, as the first is for subtracting the amount of time
    rain1 = (df.iloc[1:sample+1]).ix[:, ['ts', 'r1']]
    rain2 = (df.iloc[1:sample+1]).ix[:, ['ts', 'r2']]
    rain3 = (df.iloc[1:sample+1]).ix[:, ['ts', 'r3']]

    r1list = list(rain1["r1"])
    r2list = list(rain2["r2"])
    r3list = list(rain3["r3"])
    dicts = [{
                "id"     : deployed[0],
                "uploads": [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(rain1.columns, row) if v != None and v == v) for row in rain1.values],
                "avg"   : round(np.mean(r1list), 1),
                "MOE"   : round(np.std(r1list)/math.sqrt(sample)*tScore/np.mean(r1list)*100,1)
                },
            {
                "id"     : deployed[1],
                "uploads": [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(rain2.columns, row) if v != None and v == v) for row in rain2.values],
                "avg"   : round(np.mean(r2list), 1),
                "MOE"   : round(np.std(r2list)/math.sqrt(sample)*tScore/np.mean(r2list)*100,1)
                },
            {
                "id"     : deployed[2],
                "uploads": [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(rain3.columns, row) if v != None and v == v) for row in rain3.values],
                "avg"   : round(np.mean(r3list), 1),
                "MOE"   : round(np.std(r3list)/math.sqrt(sample)*tScore/np.mean(r3list)*100,1)
            }]
    return dicts


### FOR WIND ###

def qualityCheck(array, s, t):
    uploads = []
    uploads.append([{"w": array[0]["w"][i], "ts": array[0]["ts"][i]} for i in range(-1*s, 0)])
    wlist = []
    for upload in uploads[0]:
        wlist.append(upload["w"])
    dictQC = {
                "id"     : array[0]["_id"],
                "uploads": uploads,
                "wAvg"   : round(np.mean(wlist), 1),
                "wMOE"   : round(np.std(wlist)/math.sqrt(s)*t/np.mean(wlist)*100, 1)

            }
    return dictQC

def wind(in_testing, params):
    sets = params
    deployed = int(in_testing)
    pipeline = [
                { "$match": { "id": 2001 } },
                { "$group": {"_id": "$ts", "low": { "$last": "$t1" }, "med": { "$last": "$t2" }, "high": { "$last": "$h" } } },
                { "$sort" : SON([("_id", -1)]) }
                ]
    data    = list(sensors.aggregate(pipeline, allowDiskUse = True))
    dicts = []
    ### Set Sample size
    sample  = sets["size"]
    tScore  = sets["tScore"]
    ###
    d0 = pd.DataFrame(data)
    d1 = d0.rename(columns={'_id':'ts'})
    # Offset by one, as the first is for subtracting the amount of time
    df  = (d1.iloc[1:sample+1])
    lowlist  = list(df["low"])
    medlist  = list(df["med"])
    highlist = list(df["high"])
    dicts = {
                "uploads": [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(df.columns, row) if v != None and v == v) for row in df.values],
                "low_avg"   : round(np.mean(lowlist), 1),
                "low_MOE"   : round(np.std(lowlist)/math.sqrt(sample)*tScore/np.mean(lowlist)*100,1),
                "med_avg"   : round(np.mean(medlist), 1),
                "med_MOE"   : round(np.std(medlist)/math.sqrt(sample)*tScore/np.mean(medlist)*100,1),
                "high_avg"  : round(np.mean(lowlist), 1),
                "high_MOE"  : round(np.std(highlist)/math.sqrt(sample)*tScore/np.mean(highlist)*100,1)
                }
    return dicts

### FOR UPLOAD ##

def upload(in_testing, params):
    sets = params
    deployed = map(int, in_testing.split(','))

    ### Set Sample size
    hours   = sets["hours"]
    print hours

    pipeline = [
                { "$match": { "id": {"$in": deployed} } },
                { "$sort" : SON([("id", 1)]) }
                ]
    meta  = list(ids.aggregate(pipeline, allowDiskUse = True))

    pipeline = [
                { "$match": { "id": { "$in": deployed }, "ts": { "$gt": datetime.now() - timedelta(hours = hours - 5, minutes = -30) } } },
                { "$group": {"_id": "$id", "ts": { "$push": "$ts" } } },
                { "$sort" : SON([("_id", 1)]) }
                ]
    data    = list(sensors.aggregate(pipeline, allowDiskUse = True))

    dicts = []

    ###
    for i in range(0, data.__len__()):
        in_field  = data[i]["ts"][-1] - data[i]["ts"][0]
        uploads   = data[i]["ts"].__len__()
        try:
            uptime    = round(100*uploads/(in_field.total_seconds()/(60*int(meta[i]["freq"]))), 2)
        except:
            uptime    = round(100*uploads/(in_field.total_seconds()/(60*int(1))), 2)
        hours     = round(in_field.total_seconds()/60/60,1)
        dictQC = {
                    "id"     : data[i]["_id"],
                    "uptime" : uptime,
                    "start"  : data[i]["ts"][0],
                    "end"    : data[i]["ts"][-1],
                    "uploads": uploads,
                    "hours"  : hours

                }
        dicts.append(dictQC)
    return dicts






