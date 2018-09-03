#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, json, request, session, url_for, escape, redirect, jsonify, make_response
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.pymongo import PyMongo
import pymongo
from pymongo import MongoClient
from bson.son import SON
from bson import ObjectId
import ast
from datetime import datetime
from datetime import timedelta
import time
import csv
import math
import urllib
import urllib2
import sensor_closest_loc
import config
import calc
import dailysums
import re
import sys
import StringIO
import requests
import api
import QC
from scipy import stats
import io
from werkzeug import secure_filename

import plotly
import plotly.plotly as py
import plotly.graph_objs as go
plotly.tools.set_credentials_file(username='bharat5005', api_key='8aabplji30')
MAPS_API_KEY = config.get_maps_api_key()

import pandas as pd
from pandas.core.common import _maybe_box_datetimelike
import json
import ast
import numpy as np
from numpy import matrix
from random import *

from flask_bcrypt import Bcrypt
from flask_bcrypt import generate_password_hash

app     = Flask(__name__)
mongo   = PyMongo(app)

db          = config.get_db()
sensors     = db.sensors
ids         = db.ids
users       = db.users
phones      = db.phones
farmers     = db.farmers
firmware    = db.firmware
harvest     = db.harvest
windQC      = db.windQC
tempQC      = db.tempQC
rainQC      = db.rainQC
uploadQC    = db.uploadQC
QC_params   = db.QC_params
userTEST    = db.userTEST
testing     = True

# ids.create_index([("id", pymongo.ASCENDING)])
# sensors.create_index([("id", pymongo.ASCENDING), ("ts", pymongo.DESCENDING)], unique=True, sparse=True)
# users.create_index("username")

bcrypt = Bcrypt(app)

class User():
    
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def password(self):
        return self.password

    def hash_password(self, plaintext):
        self.password = bcrypt.generate_password_hash(plaintext, 12)

    def is_correct_password(self, plaintext):
        return bcrypt.check_password_hash(self.password, plaintext)

def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')

@app.route('/')
@app.route('/home')
def main():
    return render_template('index.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/technology')
def technology():
    return render_template('technology.html')

@app.route('/qc')
def QCviewLite():

    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if users.find({'username': session['username']})[0]['sensors'] != True:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    #if 'username' in session:
    # if session['username'] != "gkumar09@gmail.com":
    #     return redirect(url_for('notAuthorized'))
    step0 = time.time()
    print "Initializing (QC)..."
    # deployed = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,48,50,51,52,53,54,56,57,104,204,207,208,209,210,211,213]
    deployed = [1,3,4,8,9,10,17,19,20,21,24,26,31,33,48,50,51,52,53,54,56,57,58,59,60,61,104,201,202,203,204,205,206,207,208,209,210]
    all_ids  = list(ids.find({}).sort('id', pymongo.ASCENDING))
    deployed = []

    for s in all_ids:
        deployed.append(s["id"])
        
    pipeline = [
                { "$match": { "id": {"$in": deployed}, "active": 1 } },
                { "$sort" : SON([("id", 1)]) }
                ]
    sensor  = list(ids.aggregate(pipeline, allowDiskUse = True))

    valid_ids = []
    [valid_ids.append(s["id"]) for s in sensor]

    pipeline = [
            { "$match": { "id": {"$in": valid_ids}, "ts": { "$gt": datetime.now() - timedelta(days=365) } } },
            { "$sort" : SON([("_id", 1), ("ts", -1)]) },
            { "$group": { 
                "_id": "$id",
                "ts" : { "$last": "$ts" },  
                }
            }
            ]
    data    = list(sensors.aggregate(pipeline, allowDiskUse = True))
    df = pd.DataFrame(data).sort_values(by="_id")
    data = [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(df.columns, row) if v != None and v == v) for row in df.values]

    step1a = time.time()
    print "1a: Sensor data loaded... (%ss)" % (round((step1a - step0), 1))

    step1b = time.time()
    print "1: Data loaded... (%ss)" % (round((step1b - step1a), 1))
    return render_template('qc-old.html', sensors = data, ids = sensor, n_deployed = len(valid_ids))

@app.route('/qc-test',methods=["GET","POST"])
def QCview():
    #if 'username' in session:
        # if session['username'] != "gkumar09@gmail.com":
        #     return redirect(url_for('notAuthorized'))
 
    #in_testing = "8,12,18,21,23,24,28,31,32,33,34"
    in_testing = "1,2,3,4,9,10,13,14,15,16,17,19,20,21,22,23,24,25,26,28,30,31,32,33,220"

    docs = []
    t_curs = []
    testing = []

    if request.method == "POST":
        in_testing = request.form["testing"]

    for i in in_testing.split(','):
        t_curs.append(sensors.find({'id': int(i)}).sort('ts', pymongo.DESCENDING).limit(1))

    for t_cur in t_curs:
        for t in t_cur:
            testing.append(t)

    return render_template('qc-test.html', test = testing, in_test = in_testing, n_testing = len(in_testing.split(',')))
    #else:
    #    return redirect(url_for('notloggedin'))

@app.route('/qc-dashboard/<id>', methods=["GET","POST"])
def QCdashboard(id):

    if request.method == "POST":
        dict = {}
        dict["hours"]  = int(float(request.form["hours"]))
        dict["uptime"] = int(float(request.form["uptime"]))
        dict["size"]   = int(float(request.form["size"]))
        dict["tScore"] = round(stats.t.ppf(1-0.025, int(float(request.form["size"]))),3)
        dict["r"]      = float(request.form["rain"])
        dict["lw"]     = float(request.form["lwind"])
        dict["mw"]     = float(request.form["mwind"])
        dict["hw"]     = float(request.form["hwind"])
        dict["h"]      = float(request.form["hum"])
        dict["t"]      = float(request.form["temp"])
        dict["id"]     = "Default"
        QC_params.update({"id":"Default"}, {"$set": dict})

    _id  = int(id)
    sets = QC_params.find_one({})
    temp = tempQC.find_one({"id":_id})
    wind = windQC.find_one({"id":_id})
    # rain    = rainQC.find_one({"id":_id})
    rain = {}
    rain["MOE"] = 1.4
    upload  = uploadQC.find_one({"id":_id})

    try:
        if temp["tMOE"] < sets["t"] and temp["hMOE"] < sets["h"] and wind["low_MOE"] < sets["lw"] and wind["high_MOE"] < sets["hw"] and rain["MOE"] < sets["r"] and upload["uptime"] > sets["uptime"]:
            result = 1
        else:
            result = 0
    except:
        result = 0
    return render_template('qc-dashboard.html', id = _id, sets = sets, temp = temp, wind = wind, rain = rain, upload = upload, result = result)

@app.route('/qc-dashboard', methods=["GET","POST"])
def QCoverview():

    temp_deployed   = map(int, (tempQC.find_one({"id": 0})["testing"]).split(','))
    upload_deployed = map(int, (uploadQC.find_one({"id": 0})["testing"]).split(','))
    lwind_deployed  = int(windQC.find_one({"id": 0})["lower"])
    hwind_deployed  = int(windQC.find_one({"id": 0})["higher"])
    rain_deployed   = int(rainQC.find_one({"id": 0})["testing"])

    sets    = QC_params.find_one({})

    temps   = list(tempQC.find({"id": {"$in": temp_deployed } }))
    lwind   = windQC.find_one({"id":lwind_deployed, "speed": "low"})
    hwind   = windQC.find_one({"id":hwind_deployed, "speed": "high"})
    print lwind_deployed
    print lwind
    rains = list(rainQC.find_one({"id":rain_deployed}))
    uploads = list(uploadQC.find({"id": {"$in": upload_deployed } } ))

    return render_template('qc-overview.html', sets = sets, temps = temps, lwind = lwind, hwind = hwind, uploads = uploads)

@app.route('/temp-test',methods=["GET","POST"])
def tempTest():

    sets = QC_params.find_one({})

    in_testing = tempQC.find_one({"id": 0})["testing"]

    if request.method == "POST":
        in_testing = request.form["testing"]
        dict = {"id": 0, "testing": in_testing}
        tempQC.update({"id":0}, {"$set": dict}, upsert=True)
        print dict

    dicts = QC.temp(in_testing, sets)
    return render_template('temp-test.html', dicts = dicts, in_test = in_testing, tStandard = sets["t"], hStandard = sets["h"])

@app.route('/temp-test-upload/<all_ids>')
def tempTestUpload(all_ids):

    sets = QC_params.find_one({})
    dicts = QC.temp(all_ids, sets)
    
    for dict in dicts:
        tempQC.update({"id":dict["id"]}, {"$set": dict}, upsert=True)
    
    return redirect(url_for('tempTest'))

@app.route('/wind-test',methods=["GET","POST"])
def windTest():
    #if 'username' in setsssion:
        # if session['username'] != "gkumar09@gmail.com":
        #     return redirect(url_for('notAuthorized'))

    sets = QC_params.find_one({})
    # in_testing = windQC.find_one({"id": 0})["testing"]
    in_testing = 242

    if request.method == "POST":
        in_testing = request.form["testing"]
        update = {"id": 0, "testing": in_testing}
        rainQC.update({"id":0}, {"$set": update}, upsert=True)
        print update

    cursor = sensors.find({"id":2001}).sort('ts', pymongo.DESCENDING).limit(sets["size"]+1)
    data   = [x for x in cursor]
    d0     = pd.DataFrame(data)
    winds  = d0["w"].iloc[0:10]
    d0.index = d0["ts"]
    d0["diffs"] = d0.index.to_series().diff() 
    df          = d0.iloc[1:]
    df["diffs"] = (d0.diffs.iloc[1:]/np.timedelta64(1, 's')).astype(int)*-1
    df["threshold"] = list(winds)
    df["_id"] = df["_id"].astype('string')
    data = [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(df.columns, row) if v != None and v == v) for row in df.values]
    low  = {"avg": df.t1.mean(), "moe": round(np.std(df.t1)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.t1)*100,1)}
    med  = {"avg": df.t2.mean(), "moe": round(np.std(df.t2)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.t2)*100,1)}
    high = {"avg": df.h.mean(), "moe": round(np.std(df.h)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.h)*100,1)}
    rpm1 = {"avg": df.v.mean(), "moe": round(np.std(df.v)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.v)*100,1)}
    rpm2 = {"avg": df.bv.mean(), "moe": round(np.std(df.bv)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.bv)*100,1)}
    rpm3 = {"avg": df.s.mean(), "moe": round(np.std(df.s)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.s)*100,1)}
    time        = {"avg": df.diffs.mean(), "moe": round(np.std(df.diffs)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.diffs)*100,1)}
    threshold   = {"avg": round(df.threshold.mean(),1), "moe": round(np.std(df.threshold)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.threshold)*100,1)}
    return render_template('wind-test-new.html', in_test = in_testing, tStandard = sets["r"], uploads = data, low = low, med = med, high = high, time = time, threshold = threshold, rpm1 = rpm1, rpm2 = rpm2, rpm3 = rpm3)

@app.route('/wind-test-upload/<in_testing>')
def windTestUpload(in_testing):
    
    sets = QC_params.find_one({})
    wind = QC.wind(in_testing, sets)
    windQC.update({"id": int(in_testing)}, {"$set": wind}, upsert=True)
    
    return redirect(url_for('windTest'))

@app.route('/wind-test-remove/<_id>')
def windTestRemove(_id):
    
    sensors.remove({"_id": ObjectId(str(_id))})
    return redirect(url_for('windTest'))

@app.route('/rain-test',methods=["GET","POST"])
def rainTest():
    #if 'username' in setsssion:
        # if session['username'] != "gkumar09@gmail.com":
        #     return redirect(url_for('notAuthorized'))

    sets = QC_params.find_one({})
    in_testing = rainQC.find_one({"id": 0})["testing"]

    if request.method == "POST":
        in_testing = request.form["testing"]
        update = {"id": 0, "testing": in_testing}
        rainQC.update({"id":0}, {"$set": update}, upsert=True)
        print update

    cursor = sensors.find({"id":1001}).sort('ts', pymongo.DESCENDING).limit(sets["size"]+1)
    data   = [x for x in cursor]
    d0     = pd.DataFrame(data)
    d0.index = d0["ts"]
    d0["diffs"] = d0.index.to_series().diff() 
    df          = d0.iloc[1:]
    df["diffs"] = (d0.diffs.iloc[1:]/np.timedelta64(1, 's')).astype(int)*-1
    data = [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(df.columns, row) if v != None and v == v) for row in df.values]
    rain1  = {"avg": df.t1.mean(), "moe": round(np.std(df.t1)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.t1)*100,1)}
    rain2  = {"avg": df.h.mean(), "moe": round(np.std(df.h)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.h)*100,1)}
    rain3  = {"avg": df.r.mean(), "moe": round(np.std(df.r)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.r)*100,1)}
    time   = {"avg": df.diffs.mean(), "moe": round(np.std(df.diffs)/math.sqrt(sets["size"])*sets["tScore"]/np.mean(df.diffs)*100,1)}
    return render_template('rain-test.html', in_test = in_testing, tStandard = sets["r"], uploads = data, rain1 = rain1, rain2 = rain2, rain3 = rain3, time = time)


@app.route('/rain-test-upload/<all_ids>')
def rainTestUpload(all_ids):

    sets = QC_params.find_one({})
    dicts = QC.rain(all_ids, sets)
    
    for dict in dicts:
        rainQC.update({"id":dict["id"]}, {"$set": dict}, upsert=True)
    
    return redirect(url_for('rainTest'))

@app.route('/rain-test-remove/<_id>')
def rainTestRemove(_id):
    
    sensors.remove({"_id": ObjectId(str(_id))})
    return redirect(url_for('rainTest'))

@app.route('/upload-test',methods=["GET","POST"])
def uploadTest():
    #if 'username' in setsssion:
        # if session['username'] != "gkumar09@gmail.com":
        #     return redirect(url_for('notAuthorized'))

    sets = QC_params.find_one({})
    in_testing = uploadQC.find_one({"id": 0})["testing"]

    if request.method == "POST":
        in_testing = request.form["testing"]
        dict = {"id": 0, "testing": in_testing}
        uploadQC.update({"id":0}, {"$set": dict}, upsert=True)
        print dict

    dicts = QC.upload(in_testing, sets)
    return render_template('upload-test.html', dicts = dicts, in_test = in_testing, sets = sets)

@app.route('/upload-test-upload/<all_ids>')
def uploadTestUpload(all_ids):
    sets = QC_params.find_one({})
    dicts = QC.upload(all_ids, sets)
    
    for dict in dicts:
        uploadQC.update({"id":dict["id"]}, {"$set": dict}, upsert=True)
    
    return redirect(url_for('uploadTest'))

@app.route('/results/<id>')
def resultsById(id):
    # if 'username' in session:
    #     if session['username'] != "gkumar09@gmail.com":
    #         if int(id) not in users.find({'username': session['username']})[0]['sensors']:
    #             return redirect(url_for('notAuthorized'))
    return render_template('results.html', sensors = sensors.find({'id': int(id)}).sort('ts', pymongo.DESCENDING).limit(5000))    
    # return redirect(url_for('notloggedin'))
    
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        print "0: Initializing dashboard..."
        step0 = time.time()
        if session['username'] != "gkumar09@gmail.com":
            user        = users.find_one({"username": session['username'] })
            valid_ids   = user['sensors']
            name        = user['firstName']

        else:
            pipeline = [
                { "$match": { "active": 1 } },
                { "$sort" : SON([("id", 1)]) }
                ]

            sensor  = list(ids.aggregate(pipeline, allowDiskUse = True))
            valid_ids = [s["id"] for s in sensor]
            name = "Admin"

        step1 = time.time()
        print "1: Fetched valid IDs... (%ss)" % (round((step1 - step0), 1))
                    
        print valid_ids
        pipeline = [
            { "$match": { "id": {"$in": valid_ids}, "ts": { "$gt": datetime.now() - timedelta(days=365) } } },
            { "$sort" : SON([("_id", 1), ("ts", -1)]) },
            { "$group": { 
                "_id": "$id",
                "ts" : { "$last": "$ts" },
                "t"  : { "$last": "$t1" },
                "r"  : { "$last": "$r" },
                "h"  : { "$last": "$h" },
                "w"  : { "$last": "$w" },    
                }
            }
            ]
        sensorUploads = list(sensors.aggregate(pipeline, allowDiskUse = True))
        d0 = pd.DataFrame(sensorUploads).sort_values(by="_id")

        step2 = time.time()
        print "2: Fetched last sensor uploads... (%ss)" % (round((step2 - step1), 1))
        
        pipeline = [
                { "$match": { "id": {"$in": valid_ids} } },
                { "$sort" : SON([("id", 1)]) },
                { "$group": { 
                    "_id"  : "$id",
                    "lt"   : { "$last": "$lt" },
                    "ln"   : { "$last": "$ln" },
                    "name" : { "$last": "$name" },
                    }
                }
                ]
        idsMeta = list(ids.aggregate(pipeline, allowDiskUse = True))
        d1 = pd.DataFrame(idsMeta).sort_values(by="_id")
        df = d1.merge(d0, left_on="_id", right_on="_id", how="outer")
        uploads = [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(df.columns, row) if v != None and v == v) for row in df.values]

        step3 = time.time()
        print "3: Fetched sensor metadata... (%ss)" % (round((step3 - step2), 1))
        
        # print [s["id"] for s in idsMeta]
        # print [s["_id"] for s in sensorUploads]
        return render_template('old-dashboard.html', uploads = uploads, name = name)
    return redirect(url_for('notloggedin'))

def getValues(col, df, target):
    values = []
    for l in df[col].tolist():
        try:
            values.append(l.values()[0])
        except:
            values.append(0)
    target[col] = values

@app.route('/ws/<id>')
def dataDownload(id):
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    print "0: Initializing download..."
    step0 = time.time()

    sensor = ids.find_one({'id': int(id)})
    try:
        installDate = datetime.strptime(str(sensor["date"]), '%Y-%m-%d %H:%M:%S')
    except:
        installDate = dat=etime.strptime(str(sensor["date"]), '%Y-%m-%d')

    pipeline = [
                { "$match": { "id": int(id), "ts": {"$gt": installDate} } },
                { "$group": { "_id": "$ts", "rain": { "$last": "$r" }, "temp1": { "$last": "$t1" }, "temp2": { "$last": "$t2" }, "humidity": { "$last": "$h" }, "wind_speed": { "$last": "$w" } } },
                { "$sort" : SON([("_id", 1)]) }
                ]
    
    data = list(sensors.aggregate(pipeline, allowDiskUse = True))

    step1 = time.time()
    print "1: Data loaded... (%ss)" % (round((step1 - step0), 1))
    
    df                  = pd.DataFrame(data)
    df["rain"]          = config.get_sensor_rain_calibration(df["rain"])
    df["wind_speed"]    = config.get_sensor_rain_calibration(df["wind_speed"])

    csv = df.to_csv(sep=',')
    name = sensor["name"]+" "+str(data[-1]["_id"])[0:16]+'.csv'
    response = make_response(csv)
    cd = 'attachment; filename='+name
    response.headers['Content-Disposition'] = cd 
    response.mimetype='text/csv'

    step1 = time.time()
    print "1: Completed... (%ss)" % (round((step1 - step0), 1))

    return response

    #     return redirect(url_for('dashboard'))
    # return redirect(url_for('notloggedin'))

def trace_data(x_data, y_data, name, data):
    trace = go.Scattergl(
        x=x_data,
        y=y_data,
        name=name,
        mode='lines'
    )
    data.append(trace)
    print "Tracing " + name

def scatter_data(x_data, y_data, name, data):
    trace = go.Scatter(
        x=x_data,
        y=y_data,
        name=name,
        mode='markers'
    )
    data.append(trace)
    print "Scattering " + name

def bar_data(x_data, y_data, name, data):
    trace = go.Bar(
        x=x_data,
        y=y_data,
        name=name
    )
    data.append(trace)
    print "Bar " + name

@app.route('/analytics/<id>',methods=["GET","POST"])
def analytics(id):
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    # fetch data for that id
    step0 = time.time()
    print "0: Initializing (analytics)..."
    
    sensor      = ids.find_one({'id': int(id)})

    name         = sensor["name"]    
    lat          = sensor["lt"]
    lon          = sensor["ln"]
    mob_no       = sensor["ph"]
    carrier      = sensor["carrier"]
    f            = int(sensor["freq"])
    try:
        install_date = datetime.strptime(str(sensor["date"]), '%Y-%m-%d %H:%M:%S')
    except:
        install_date = datetime.strptime(str(sensor["date"]), '%Y-%m-%d')

    pipeline = [
                    { "$match": { "id": int(id), "ts": {"$gt": install_date } } },
                    { "$sort" : SON([("ts", 1)]) }
                ]
    sensor_data     = pd.DataFrame(list(sensors.aggregate(pipeline, allowDiskUse = True)))

    # sensor_data     = pd.DataFrame(list(sensors.find({"id": int(id), "ts": {"$gt": install_date} }).sort('ts', pymongo.ASCENDING)))

    step1 = time.time()
    print "1: Data loaded... (%ss)" % (round((step1 - step0), 1))
    
    dates    = sensor_data.ts

    sensor_data.index = sensor_data.ts
    d1 = {}
    d1["start"] = sensor_data.iloc[0:-1].index
    d1["end"]   = sensor_data.iloc[1:].index
    d1["diffs"] = sensor_data.index.to_series().diff()[1:]
    d2 = pd.DataFrame(d1)[["start", "end", "diffs"]]
    d2["misses"] = (d2["diffs"]/timedelta(minutes=f)-1).round(0)
    missesDF = d2.loc[d2.misses > 0]    
    hangsDF  = d2.loc[d2.misses >= 10]

    misses   = d2.misses.sum() - hangsDF.misses.sum()
    hangs    = hangsDF.misses.count()
    uploads  = sensor_data.__len__()
    attempts = uploads + misses

    in_field  = dates.iloc[-1] - dates.iloc[0]
    pct       = round(100*uploads/attempts, 2)
    uptime    = round(100*uploads/(in_field.total_seconds()/(60*f)), 2)
    analytics = {"id": id, "name": name, "last_update": dates.iloc[-1], "uptime": uptime, "infield_days": in_field.days, "pct": pct, "attempts": format(int(attempts), ","), "uploads": format(uploads, ","), "misses": format(int(misses), ","), "hangs": hangs, "lt": lat, "ln": lon, "mob_no": mob_no, "carrier": carrier, "freq": str(f), "install_date": install_date.strftime("%Y-%m-%d")}

    step2 = time.time()
    print "2: Uptime done... (%ss)" % (round((step2 - step1), 1))

    # Bad signal
    if np.std(sensor_data.sg) > 3:
        situation = 2
    # Down for a while
    elif datetime.now() - dates.iloc[-1] > timedelta(days=2):
        situation = 3
    else: 
        situation = 0
    
    rain    = sensor_data.groupby(pd.TimeGrouper('1H')).sum()["r"]
    df      = sensor_data.groupby(pd.TimeGrouper('1H')).median()
    df["r"] = rain
    
    def checkCol(_DF, _COL, _NAME, _LIST):
        if _COL in _DF.columns:
            _LIST.append({"val": _DF[_COL], "name": _NAME})

    yvars = [
                    {"val": df.t1, "name": "Temperature (C)"},
                    {"val": df.t2, "name": "Temperature 2 (C)"},
                    {"val": df.h, "name": "Humidity (%)"},
                    {"val": config.get_sensor_rain_calibration(df.r), "name": "Rainfall (mm)"},
                    {"val": config.get_sensor_rain_calibration(df.w), "name": "Wind Speed (km/h)"},
                    # {"val": df.s, "name": "Current (A)"},
                    # {"val": df.sg, "name": "Signal (dB)"},
            ]

    # checkCol(df, "v", "Voltage (V)", yvars)
    # checkCol(df, "bv", "Battery (V)", yvars)
    if "v" in df:
        yvars.append({"val": (df.s*df.v/5*100).clip_lower(0), "name": "Power (W)"})

    step3 = time.time()
    print "4: Prep for ploting done... (%ss)" % (round((step3 - step2), 1))
    
    data = []
    for yvar in yvars:
        if yvar:
            data.append(go.Scattergl(
                x = df.index,
                y = yvar["val"],
                name= yvar["name"],
                mode= 'lines'
            )
    )
    title = 'Analytics for '+name        
    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )
    fig=dict(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    step4 = time.time()
    print "4: Completed... (%ss)" % (round((step4 - step0), 1))
    
    return render_template('sensor-dash.html', analytics = analytics, situation = situation)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' not in session:
        error = None
        
        if request.method == 'POST':
            username = request.form['username'].lower()
            print username

            user = users.find_one({'username': username})
            hashed_pwd = user["password"]

            if hashed_pwd:
                usr = User(username, hashed_pwd)

            if usr.is_correct_password(request.form['password']):
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid username/password'
        
        return render_template('login.html', error = error)

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/error')
def notloggedin():
    return render_template('error.html')

@app.route('/restricted')
def notAuthorized():
    return render_template('movealong.html')

@app.route('/location-not-found')
def locationNotFound():
    return render_template('not-found.html')    

def valid_login(user, password):
    if users.find({'username':user, 'password': password}).count() == 1:
        return True

    return False

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

@app.route('/add_data')
def AddData():
    string = "Add data by setting variables in the url equal to the values \nFor example: /add_data/1=<'id':2, 'wind_speed':5, 'rainfall':10>&2=<'id':4, 'wind_speed':8, 'rainfall':15>"
    return string

@app.route('/add_data/<datastring>')
def InsertData(datastring):

    # valDict = { 'last_update': "", 'id': "", 'air_temp': "", 'humidity': "", 'wind_speed': "", 'rainfall': "", 'air_pressure': "", 'solar_radiation': "", 'latitude': "", 'longitude': "" }
    # valLst = ['id', 'air_temp', 'air_pressure', 'humidity', 'rainfall', 'wind_speed', 'solar_radiation', 'solar_radiation', 'latitude', 'longitude', 'last_update']
    
    ## FREQUENCY OF UPLOAD##
    f = 1
    ##

    minutes = []
    dictStrings = []
    index = 0

    # 1=<blahblahblah>
    # we extract <blahblahblah>

    for i, char in enumerate(datastring):
        if char == '<':
            index = i
        if char == '>':
            dictStrings.append(datastring[index:i+1])

    s = ""

    for hashstring in dictStrings:
        minute = f*(len(dictStrings)-dictStrings.index(hashstring)-1)
        string = "{"+hashstring[1:len(hashstring)-1]+"}"
        valDict = ast.literal_eval(string)
        valDict["ts"] = datetime.now() + timedelta(hours=5, minutes=30)
        print valDict
        sensor_id = sensors.insert_one(valDict).inserted_id
        return str(valDict)

    return s

@app.route('/maytheforcebewithyou', methods=["GET","POST"])
def yobiOne():
    if request.method == "GET":
        # valDict = { 'last_update': "", 'id': "", 'air_temp': "", 'humidity': "", 'wind_speed': "", 'rainfall': "", 'air_pressure': "", 'solar_radiation': "", 'latitude': "", 'longitude': "" }
        # valLst = ['id', 'air_temp', 'air_pressure', 'humidity', 'rainfall', 'wind_speed', 'solar_radiation', 'solar_radiation', 'latitude', 'longitude', 'last_update']
        # http://localhost:5000/maytheforcebewithyou?id=207&t1=31.1&t2=31.2&h=52.4&w=10&r=0&s=27&sg=28
        
        document = {}
        
        document["id"] = int(request.args.get('id'))
        try:
            document["ts"] = datetime.strptime(request.args.get('ts'), '%Y-%m-%dT%H:%M:%S')
        except:
            document["ts"] = datetime.now() + timedelta(hours=5, minutes=30)
        try:
            document["t1"] = float(request.args.get('t1'))
        except:
            document["t1"] = 0
        try:
            document["t2"] = float(request.args.get('t2'))
        except:
            document["t2"] = 0
        try: 
            document["h"]  = float(request.args.get('h'))
        except:
            document["h"]  = 0
        try:
            document["w"]  = float(request.args.get('w'))
        except:
            document["w"]  = 0
        try:
            document["r"]  = float(request.args.get('r'))
        except:
            document["r"]  = 0
        try:
            document["a"] = float(request.args.get('a'))
        except:
            document["a"] = 0
        try:
            document["sg"] = float(request.args.get('sg'))
        except:
            document["sg"] = 0
        try:
            document["s"]  = float(request.args.get('s'))
        except:
            document["s"]  = 0
        try:
            document["v"]  = float(request.args.get('v'))
        except:
            document["v"]  = 0
        try:
            document["bv"]  = float(request.args.get('bv'))
        except:
            document["bv"]  = 0
        try:
            document["pm01"]  = float(request.args.get('pm01'))
        except:
            pass
        try:
            document["pm25"]  = float(request.args.get('pm25'))
        except:
            pass
        try:
            document["pm10"]  = float(request.args.get('pm10'))
        except:
            pass
        sensor_id = sensors.insert_one(document).inserted_id

        return str(document)

@app.route('/bulk-upload', methods=["GET","POST"])
def bulkUpload():
    if request.method == 'POST':
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                df = pd.read_csv(file)
                try:
                    df["ts"] = pd.to_datetime(df["ts"])
                except:
                    df["ts"] = datetime.now() + timedelta(hours=5, minutes = 30)
                response = df.iloc[-1].to_json()
                my_list = [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(df.columns, row) if v != None and v == v) for row in df.values]
                sensors.insert_many(my_list)
                print df
                return response
    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    """

@app.route('/blank')
def blank():
    return render_template('blank.html')

@app.route('/admin-control', methods=["GET","POST"])
def adminControl():     
    if request.method == "POST":
        # Update users
        username    = request.form.get('username')
        firstName   = request.form.get('firstName')
        try:
            password    = bcrypt.generate_password_hash(request.form.get('password'), 12)
        except:
            password    = userTEST.find_one({"username": username})["password"]
        states      = request.form.getlist('states')
        print states
        userTEST.update({
              'username': username
            },{
              '$set': {
                'updated_at'    : datetime.now(),
                'firstName'     : firstName,
                'states'        : states,
                'password'      : password,
              }
            }, upsert=True, multi=False)
        return redirect(redirect_url())
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    allUsers = list(userTEST.find({}))
    states   = list(set(list(pd.DataFrame(list(ids.find({})))["state"])))

    return render_template('admin-control.html', allUsers = allUsers, states = states)

@app.route('/remove-user/<uName>')
def removeUser(uName):
    userTEST.remove({'username': uName})
    return redirect(url_for('adminControl'))

@app.route('/edit-permissions/<uName>')
def editPermissions(uName):
    states   = list(set(list(pd.DataFrame(list(ids.find({})))["state"])))
    return render_template('edit-permissions.html')

@app.route('/check-id')
def checkID():

    # Iterate by 1, adding to the current highest ID number

    last_id = list(pd.DataFrame(list(ids.find())).sort_values(by="id")["id"])[-1]+1
    return render_template('india_clock.html', time = last_id)

@app.route('/create-id', methods=["GET","POST"])
def createID():
    if request.method == "GET":
        try:
            document = {}
            document["id"]      = int(request.args.get('id'))
            document["name"]    = "New AWS"
            document["lt"]      = float(request.args.get('lt'))
            document["ln"]      = float(request.args.get('ln'))
            document["ph"]      = "Unknown"
            document["carrier"] = "Unknown"
            document["date"]    = datetime.now() + timedelta(hours=5, minutes=30)
            document["freq"]    = request.args.get('freq')
            document["active"]  = 1
        
        except:
            resp = {"Error": "Problem creating ID data."}
            return jsonify(**resp)

        all_ids = list(pd.DataFrame(list(ids.find()))["id"])

        if document["id"] not in all_ids:
            sensor_id = ids.insert_one(document).inserted_id
            return str(document)
        else:
            resp = {"Error": "ID already exists."}
            return jsonify(**resp)

@app.route('/get-phone', methods=["GET","POST"])
def getPhone():
    if request.method == "POST":
        phone = "+"+request.form.get('sender')
        _id   = int(request.form.get('content').split('HK9D7 NEWID ')[1])
        print _id, phone
        ids.update({
              'id': int(_id)
            },{
              '$set': {
                'updated_at': datetime.now(),
                'ph'        : phone
              }
            }, upsert=False, multi=False)
        message = "Done"
        return render_template('india_clock.html', time = message)

@app.route('/id-dash', methods=["GET","POST"])
def edit_ids():
    admin = 0
    if 'username' in session:        
        if request.method == "POST":
            # Do stuff
            sensorId = int(request.form.get('id'))
            name     = request.form.get('name')
            state    = request.form.get('state')
            lt       = float(request.form.get('lt'))
            ln       = float(request.form.get('ln'))
            carrier  = request.form.get('carrier')
            phone    = request.form.get('ph')
            date     = datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M')
            freq     = request.form.get('freq')
            try:
                active   = int(request.form.get('active'))
            except:
                active   = 0

            # # Automatically create state name
            # url = "https://maps.googleapis.com/maps/api/geocode/json"
            # latlng = str(lt)+","+str(ln)
            # headers = {"latlng": latlng, "key": MAPS_API_KEY}
            # response = requests.get(url, headers)
            # json_result = json.loads(response.content)
            # state = json_result["results"][0]["address_components"][-3]["long_name"]
            # print state

            # aw_array now contains the closest accuweather locations alongside their distances
            print "Updating", sensorId
            ids.update({
              'id': int(sensorId)
            },{
              '$set': {
                'updated_at': datetime.now(),
                'name'      : name,
                'state'     : state,
                'lt'        : lt,
                'ln'        : ln,
                'carrier'   : carrier,
                'ph'        : phone,
                'date'      : date,
                'freq'      : freq,
                'active'    : active,
              }
            }, upsert=False, multi=False)
            return redirect(redirect_url())

        if session['username'] != "gkumar09@gmail.com":
            valid_ids = users.find({'username': session['username']})[0]['sensors']
            cursor    = list(ids.find({'id':{'$in': valid_ids}}).sort('id', pymongo.ASCENDING))
        else:
            admin   = 1
            cursor  = list(ids.find({}).sort('id', pymongo.ASCENDING))
        idDicts = []
        for d in cursor:
            try:
                ts = datetime.strftime(d["date"], '%Y-%m-%dT%H:%M')
            except:
                try:
                    ts = datetime.strptime(d["date"], '%Y-%m-%d')
                except:
                    ts = "2017-01-01T00:00"
            try:
                f = d["freq"]
            except:
                f = 4
            try:
                act = int(d["active"])
            except:
                act = 0
            try:
                state = d["state"]
            except:
                state = ""
            idDicts.append({
                            "id"     : d["id"],
                            "state"  : state,
                            "name"   : d["name"], 
                            "lt"     : d["lt"], 
                            "ln"     : d["ln"], 
                            "carrier": d["carrier"],
                            "ph"     : d["ph"],
                            "date"   : ts,
                            "freq"   : f,
                            "active" : act
                        })
        return render_template('edit_ids.html', idDicts = idDicts, admin = admin)
    return redirect(url_for('notloggedin'))

@app.route('/alert-dash/<sid>')
def alertDash(sid):
    id = int(sid)

    # Pull yesterday and today's weather, to allow dailysums function to operate properly, as
    # it needs two days to sum rainfall values for one day

    yesterday = datetime.combine(datetime.now().date() - timedelta(days=1), datetime.min.time())
    tomorrow  = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())
    
    pipeline  = [
                { "$match": { "id": id, "ts": { "$gt": yesterday, "$lt": tomorrow } } },
                { "$group": { 
                    "_id": "$ts", 
                    "r"  : { "$push": "$r" },
                    "t"  : { "$push": "$t1" },
                    "h"  : { "$push": "$h" }, 
                    } 
                },
                { "$sort" : SON([("_id", 1)]) }
                ]     

    yobi = list(sensors.aggregate(pipeline, allowDiskUse = True))
    sm0  = list(sm.find({'loc': 'gaya', 'n_predict':0}).sort('timestamp', pymongo.DESCENDING).limit(1))
    sm1  = list(sm.find({'loc': 'gaya', 'n_predict':1}).sort('timestamp', pymongo.DESCENDING).limit(1))

    try:
        yobiDates, yobiValues = dailysums.yobi(yobi)
        temps = []
        hums  = []
        for y in yobi:
            temps.append(y["t"][0])
            hums.append(y["h"][0])
        yest_max_temp = round(max(temps), 1)
        yest_min_temp = round(min(temps), 1)
        yest_max_hum  = round(max(hums), 1)
        yest_min_hum  = round(min(hums), 1)
        yest_rain     = yobiValues[0]
        yestValues    = True
    except:
        yestValues = False

    today_max_temp = sm0[0]['hightemp']
    today_min_temp = sm0[0]['lowtemp']
    today_max_hum  = sm0[0]['highhumidity']
    today_min_hum  = sm0[0]['lowhumidity']
    today_rain     = sm0[0]['rain']

    tom_max_temp   = sm1[0]['hightemp']
    tom_min_temp   = sm1[0]['lowtemp']
    tom_max_hum    = sm1[0]['highhumidity']
    tom_min_hum    = sm1[0]['lowhumidity']
    tom_rain       = sm1[0]['rain']

    # nums = '+919654315871, +917011479828, +917506402645, +917982431043, +919631195456, +919934931659, +919635975077, +918459499599, +919810208119, +917982563362'
    contact  = farmers.find_one({"id": id})
    username = contact["username"]
    if testing == True:
        nums = "".join(str(n)+"," for n in contact["numbers"])+"+919654315871,+917011479828,+918459499599,+919810208119"
    else:
        nums = "".join(str(n)+"," for n in contact["numbers"])
    if contact["language"] == "Hindi":
        mes = username+'\n'
        if contact["days"]["yest"] == 1 and yestValues != False:
            mes += ('बिता कल\n').decode('utf-8')
        if contact["inputs"]["temp"] == 1 and yestValues != False:
            mes += ('गर्मी: '+str(yest_max_temp)+'C/'+str(yest_min_temp)+'C\n').decode('utf-8')
        if contact["inputs"]["hum"] == 1 and yestValues != False:
            mes += ('नमी: '+str(yest_max_hum)+'%/'+str(yest_min_hum)+'%\n').decode('utf-8')
        if contact["inputs"]["rain"] == 1 and yestValues != False:
            mes += ('बारिश: '+str(yest_rain)+'mm\n\n').decode('utf-8')
        if contact["days"]["tod"] == 1:
            mes += ('आज\n').decode('utf-8')
        if contact["inputs"]["temp"] == 1:
            mes += ('गर्मी: '+str(today_max_temp)+'C/'+str(today_min_temp)+'C\n').decode('utf-8')
        if contact["inputs"]["hum"] == 1:
            mes += ('नमी: '+str(today_max_hum)+'/'+str(today_min_hum)+'\n').decode('utf-8')
        if contact["inputs"]["rain"] == 1:
            mes += ('बारिश: '+str(today_rain)+'mm\n\n').decode('utf-8')
        if contact["days"]["tom"] == 1:
            mes += ('आने वाला कल\n').decode('utf-8')
        if contact["inputs"]["temp"] == 1:
            mes += ('गर्मी: '+str(tom_max_temp)+'C/'+str(tom_min_temp)+'C\n').decode('utf-8')
        if contact["inputs"]["hum"] == 1:
            mes += ('नमी: '+str(tom_max_hum)+'/'+str(tom_min_hum)+'\n').decode('utf-8')
        if contact["inputs"]["rain"] == 1:
            mes += ('बारिश: '+str(tom_rain)+'mm').decode('utf-8')
    else:
        mes = username+'\n'
        if yestValues != False:
            mes += ('YESTERDAY\n').decode('utf-8')
        if contact["inputs"]["temp"] == 1 and yestValues != False:
            mes += ('Temp: '+str(yest_max_temp)+'C/'+str(yest_min_temp)+'C\n').decode('utf-8')
        if contact["inputs"]["hum"] == 1 and yestValues != False:
            mes += ('Hum: '+str(yest_max_hum)+'%/'+str(yest_min_hum)+'%\n').decode('utf-8')
        if contact["inputs"]["rain"] == 1 and yestValues != False:
            mes += ('Rain: '+str(yest_rain)+'mm\n\n').decode('utf-8')
        mes += ('TODAY\n').decode('utf-8')
        if contact["inputs"]["temp"] == 1:
            mes += ('Temp: '+str(today_max_temp)+'C/'+str(today_min_temp)+'C\n').decode('utf-8')
        if contact["inputs"]["hum"] == 1:
            mes += ('Hum: '+str(today_max_hum)+'/'+str(today_min_hum)+'\n').decode('utf-8')
        if contact["inputs"]["rain"] == 1:
            mes += ('Rain: '+str(today_rain)+'mm\n\n').decode('utf-8')
        mes += ('TOMORROW\n').decode('utf-8')
        if contact["inputs"]["temp"] == 1:
            mes += ('Temp: '+str(tom_max_temp)+'C/'+str(tom_min_temp)+'C\n').decode('utf-8')
        if contact["inputs"]["hum"] == 1:
            mes += ('Hum: '+str(tom_max_hum)+'/'+str(tom_min_hum)+'\n').decode('utf-8')
        if contact["inputs"]["rain"] == 1:
            mes += ('Rain: '+str(tom_rain)+'mm').decode('utf-8')
    return render_template('SMS.html', nos = nums, msg = mes, id = id)

@app.route('/changePass', methods=["GET","POST"])
def changePassword():
    if 'username' in session:
        user = users.find_one({'username': session['username']})

        username = user['username']

        if request.method == "GET":
            return render_template('changepass.html', username = username)

        elif request.method == "POST":
            newpassword = request.form.get('password')
            confirmpass = request.form.get('confirmpass')
            cur_hashed_pwd = user['password']

            usr = User(username, cur_hashed_pwd)

            if confirmpass != newpassword:
                comment = "Confirm Password and New Password were different"

            elif newpassword == "":
                comment = "No Password Entered"

            elif usr.is_correct_password(newpassword): # checks if the  new password is the same as the old password
                comment = "Error: Same password entered"
        
            else:
                usr.hash_password(newpassword)
                user['password'] = usr.password
                print user
                users.remove({'username': username})

                users.insert_one(user)

                comment =  "Password for "+username+" was changed"

            return render_template('changepass.html', username = username, comment=comment)

    return redirect(url_for('notloggedin'))

@app.route('/OTA-upload',methods=["GET","POST"])
@app.route('/ota-upload',methods=["GET","POST"])
def OTAupload():
    if request.method == "POST":
        code    = str(request.form["code"]).rstrip('\r\n\t')
        version = str(request.form["version"])
        if not version:
            version = float(list(firmware.find().sort('updated_at',-1).limit(1))[0]["version"]) + .01
        firmware.insert({"code": code, "version": version, "updated_at": datetime.now()})
    code = list(firmware.find({}).sort('updated_at', pymongo.DESCENDING).limit(1))[0]
    return render_template('OTA-upload.html', code = code)

@app.route('/OTA/<id>')
@app.route('/ota/<id>')
def OTA(id):
    code = list(firmware.find({}).sort('updated_at', pymongo.DESCENDING).limit(1))[0]
    return render_template('OTA.html', id = id, code = code)

@app.route('/IST')
def setIST():
    IST = str(datetime.now() + timedelta(hours=5, minutes=30))[0:19]
    return render_template('india_clock.html', time = IST)

@app.route('/version')
def checkVersion():
    version = str(list(firmware.find().sort('updated_at',-1).limit(1))[0]["version"])
    return render_template('india_clock.html', time = version)

@app.route('/sms-builder/<id>',methods=["GET","POST"])
def phoneUpload(id):
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    locId = int(id)
    if request.method == "POST":
        numbers  = re.split(',|,\r\n|,|, |\r\n|',request.form.get('numbers'))
        while '' in numbers: numbers.remove('')
        username = request.form.get('username')
        language = request.form.get('language')
        try:
            temp = int(request.form.get('temp'))
        except:
            temp = 0
        try:
            rain = int(request.form.get('rain'))
        except:
            rain = 0
        try:
            hum  = int(request.form.get('hum'))
        except:
            hum  = 0
        try:
            yest  = int(request.form.get('yest'))
        except:
            yest  = 0
        try:
            tod  = int(request.form.get('tod'))
        except:
            tod  = 0
        try:
            tom  = int(request.form.get('tom'))
        except:
            tom  = 0
        farmers.update({
              'id': locId
            },{
              '$set': {
                'numbers'   : numbers,
                'updated_at': datetime.now(),
                'username'  : username,
                'inputs'    : {"temp": temp, "rain": rain, "hum": hum},
                'days'    : {"yest": yest, "tod": tod, "tom": tom},
                'language'  : language
              }
            }, upsert=False, multi=False)
        return redirect(url_for('smsManager'))
        # def batchStatus(apikey, batchID):
        #     data = urllib.urlencode({'apikey': apikey, 'batch_id' : batchID})
        #     data = data.encode('utf-8')
        #     req = urllib2.Request("https://api.textlocal.in/status_batch/?", data)
        #     response = urllib2.urlopen(req)
        #     return response.read()
        # batches = contacts["responses"]
        # 339204474
        # print batchStatus('mnpbat79E4I-h5eoJDsq1UHHiTJeAiqi3euEPsLdJl', 339204474)
    contacts = farmers.find_one({"id": locId})
    sensors  = ids.find_one({'id': locId})
    return render_template('sms-builder.html', contacts = contacts, sensors = sensors)

@app.route('/sms-harvest/<id>',methods=["GET","POST"])
def SMSharvest(id):
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    locId = int(id)
    if request.method == "POST":
        numbers  = re.split(',|,\r\n|,|, |\r\n|',request.form.get('numbers'))
        while '' in numbers: numbers.remove('')
        username = request.form.get('username')
        language = request.form.get('language')
        start    = request.form.get('start')
        end      = request.form.get('end')
        algo     = request.form.get('algo')
        try:
            tod  = int(request.form.get('tod'))
        except:
            tod  = 0
        try:
            tom  = int(request.form.get('tom'))
        except:
            tom  = 0
        try:
            daf  = int(request.form.get('daf'))
        except:
            daf  = 0
        harvest.update({
              'id': locId
            },{
              '$set': {
                'numbers'   : numbers,
                'updated_at': datetime.now(),
                'username'  : username,
                'start'     : start,
                'end'       : end,
                'language'  : language,
                'days'    : {"tod": tod, "tom": tom, "daf": daf},
                'algo'      : algo
              }
            }, upsert=False, multi=False)
        # def batchStatus(apikey, batchID):
        #     data = urllib.urlencode({'apikey': apikey, 'batch_id' : batchID})
        #     data = data.encode('utf-8')
        #     req = urllib2.Request("https://api.textlocal.in/status_batch/?", data)
        #     response = urllib2.urlopen(req)
        #     return response.read()
        # batches = contacts["responses"]
        # 339204474
        # print batchStatus('mnpbat79E4I-h5eoJDsq1UHHiTJeAiqi3euEPsLdJl', 339204474)
    step0 = time.time()

    contacts = farmers.find_one({"id": locId})
    harv     = harvest.find_one({"id": locId})
    station  = ids.find_one({'id': locId})

    sensor      = ids.find_one({'id': locId})
    try:
        installDate = datetime.strptime(str(sensor["date"]), '%Y-%m-%d %H:%M:%S')
    except:
        installDate = datetime.strptime(str(sensor["date"]), '%Y-%m-%d')

    pipeline = [
                    { "$match": { "id": locId, "ts": {"$gt": installDate} } },
                    { "$group": { "_id": "$ts", "r": { "$push": "$r" }, "s": { "$push": "$s" }, "v": { "$push": "$v" }, "t": { "$push": "$t1" }, "h": { "$push": "$h" } } },
                    { "$sort" : SON([("_id", 1)]) }
                    ]
    sensor_data     = list(sensors.aggregate(pipeline, allowDiskUse = True))

    step1 = time.time()
    print "1: Data Loaded... (%ss)" % (round((step1 - step0), 1))

    data        = []
    dates       = [] # %Y-%m-%d %H:%M:%S
    rainfall    = []
    temps       = []
    humidities  = []
    solars      = []

    # Extract Data from JSON Objects into arrays
    for i in range(0, sensor_data.__len__()):
        if isinstance(sensor_data[i]['_id'], basestring) == True:
            ts = datetime.strptime(sensor_data[i]['_id'], '%Y-%m-%d %H:%M:%S')
        else:
            ts = sensor_data[i]['_id']
        if ts > installDate:
            dates.append(ts)
            rainfall.append(config.get_sensor_rain_calibration(float(sensor_data[i]['r'][0])))
            temps.append(float(sensor_data[i]['t'][0]))
            humidities.append(float(sensor_data[i]['h'][0]))
            try:
                if sensor_data[i]['s'] < 0:
                    solars.append(0)
                else:
                    solars.append(sensor_data[i]['s'][0]*sensor_data[i]['v'][0]/5*100)
            except:
                solars.append(0)

    solarDates, solarValues  = dailysums.power(dates, solars)
    tempDates, tempValues    = dailysums.power(dates, temps)
    humDates, humValues      = dailysums.power(dates, humidities)
    rainDates, rainValues    = dailysums.yobi(sensor_data)
    length = min(solarDates.__len__(), rainDates.__len__(), tempDates.__len__(), humDates.__len__())

    step2 = time.time()
    print "2: Data Sorted... (%ss)" % (round((step2 - step1), 1))

    # create file-like string to capture output
    codeOut = StringIO.StringIO()
    codeErr = StringIO.StringIO()

    code = harv["algo"]

    # capture output and errors
    sys.stdout = codeOut
    sys.stderr = codeErr    

    vgoods  = []
    vgdates = []
    goods   = []
    gdates  = []
    bads    = []
    bdates  = []
    for i in range(0, length):
        solar    = solarValues[i-length]
        rain     = rainValues[i-length]
        temp     = tempValues[i-length]
        humidity = humValues[i-length]
        exec code
        out = har(rain, solar)
        if out == "Very good":
            vgoods.append(2)
            vgdates.append(rainDates[i-length])
        if out == "Good":
            goods.append(1)
            gdates.append(rainDates[i-length])
        if out == "Bad":
            bads.append(0)
            bdates.append(rainDates[i-length])

    # restore stdout and stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    s = codeErr.getvalue()

    print "error:\n%s\n" % s

    s = codeOut.getvalue()

    print "output:\n%s" % s

    codeOut.close()
    codeErr.close()

    step3 = time.time()
    print "3: Function evaluated... (%ss)" % (round((step3 - step2), 1))

    scatter_data(vgdates, vgoods, "Very Good", data)
    scatter_data(gdates, goods, "Good", data)
    scatter_data(bdates, bads, "Bad", data)
    trace_data(rainDates, rainValues, "Rain", data)
    trace_data(solarDates, solarValues, "Solar", data)

    title = 'Harvest Recommendations'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('sms-harvest.html', contacts = contacts, sensors = station, harvest = harv)

@app.route('/sms-manager')
def smsManager():
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            print session["username"]
            valid_ids = users.find({'username': session['username']})[0]['sensors']
            contacts = list(farmers.find({"id": {'$in': valid_ids}}).sort('id', pymongo.DESCENDING))
            all_ids = []
            for s in contacts:
                all_ids.append(s["id"])
        else: 
            contacts = list(farmers.find().sort('id', pymongo.DESCENDING))
            all_ids = []
            for s in contacts:
                all_ids.append(s["id"])
        sensors  = list(ids.find({'id': {'$in': all_ids}}).sort('id', pymongo.DESCENDING))
        totals = []
        for contact in contacts:
            try:
                total = pd.DataFrame(contact['responses'])["num_messages"].sum()
            except:
                total = 0
            totals.append(total)
        # def batchStatus(apikey, batchID):
        #     data = urllib.urlencode({'apikey': apikey, 'batch_id' : batchID})
        #     data = data.encode('utf-8')
        #     req = urllib2.Request("https://api.textlocal.in/status_batch/?", data)
        #     response = urllib2.urlopen(req)
        #     return response.read()
        # batches = contacts["responses"]
        # 339204474
        # print batchStatus('mnpbat79E4I-h5eoJDsq1UHHiTJeAiqi3euEPsLdJl', 339204474)
        return render_template('sms-dashboard.html', contacts = contacts, sensors = sensors, totals = totals)
    return redirect(url_for('notloggedin'))

@app.route('/api', methods = ["GET", "POST"])
# @api.requires_auth
def API():
    step0 = time.time()
    print "0: Initializing... (API)"
    if request.method == "GET":
        try:
            username = request.args.get("user")
            password = request.args.get("password")
            user_id  = int(request.args.get("id"))
        except:
            response = jsonify(**{"Error": "No API key entered."})

        user     = users.find_one({'username': username})
        
        if user:
            hashed_pwd = user["password"]

            if hashed_pwd:
                usr = User(username, hashed_pwd)

            if usr.is_correct_password(password):
                step1 = time.time()
                print "1: Credentials match... (%ss)" % (round((step1 - step0), 1))
                if user["sensors"] == True or user_id in user["sensors"]:
                    dict = {}

                    step2 = time.time()
                    print "2: Retreiving meta data... (%ss)" % (round((step2 - step1), 1))

                    pipeline = [
                                { "$match": { "id": user_id } },
                                { "$group": { "_id": "$id", "lt": { "$push": "$lt" }, "ln": { "$push": "$ln" }, "name": { "$push": "$name" }, "installDate": { "$push": "$date" } } },
                                { "$sort" : SON([("_id", 1)]) }
                                ]
                    dict["meta"] = list(ids.aggregate(pipeline, allowDiskUse = True))
                    try:
                        installDate  = datetime.strptime(dict["meta"][0]["installDate"][0], "%Y-%m-%d")
                    except:
                        installDate  = dict["meta"][0]["installDate"][0]

                    step3 = time.time()
                    print "3: Retreiving sensor data... (%ss)" % (round((step3 - step2), 1))
                    
                    pipeline = [
                                { "$match": { "id": user_id, "ts": {"$gt": installDate} } },
                                { "$group": { "_id": "$id", "ts": { "$push": "$ts" }, "rain": { "$push": "$r" }, "temp": { "$push": "$t1" }, "hum": { "$push": "$h" }, "wind": { "$push": "$w" }, "solar": { "$push": "$s" } } },
                                { "$sort" : SON([("_id", 1)]) }
                                ]
                    dict["uploads"] = list(sensors.aggregate(pipeline, allowDiskUse = True))

                    step4 = time.time()
                    print "4: Printing data... (%ss)" % (round((step4 - step3), 1))

                    response = jsonify(**dict)
                else:   
                    response = jsonify(**{"Error": "Unauthorized access."})
            else:   
                    response = jsonify(**{"Error": "Wrong username and password."})
        else:
            response = jsonify(**{"Error": "User doesn't exist."})

    response.headers.add('Access-Control-Allow-Origin', '*')
    step5 = time.time()
    print "5: Completed... (%ss)" % (round((step5 - step0), 1))
    return response

@app.route('/api-last', methods = ["GET", "POST"])
# @api.requires_auth
def APIlast():
    step0 = time.time()
    print "0: Initializing... (API)"
    if request.method == "GET":
        try:
            username = request.args.get("user")
            password = request.args.get("password")
            user_id  = int(request.args.get("id"))
        except:
            response = jsonify(**{"Error": "No API key entered."})

        user     = users.find_one({'username': username})
        
        if user:
            hashed_pwd = user["password"]

            if hashed_pwd:
                usr = User(username, hashed_pwd)

            if usr.is_correct_password(password):
                step1 = time.time()
                print "1: Credentials match... (%ss)" % (round((step1 - step0), 1))
                if user["sensors"] == True or user_id in user["sensors"]:
                    dict = {}

                    step2 = time.time()
                    print "2: Retreiving meta data... (%ss)" % (round((step2 - step1), 1))

                    pipeline = [
                                { "$match": { "id": user_id } },
                                { "$group": { "_id": "$id", "lt": { "$push": "$lt" }, "ln": { "$push": "$ln" }, "name": { "$push": "$name" }, "installDate": { "$push": "$date" } } },
                                { "$sort" : SON([("_id", 1)]) }
                                ]
                    dict["meta"] = list(ids.aggregate(pipeline, allowDiskUse = True))
                    try:
                        installDate  = datetime.strptime(dict["meta"][0]["installDate"][0], "%Y-%m-%d")
                    except:
                        installDate  = dict["meta"][0]["installDate"][0]

                    step3 = time.time()
                    print "3: Retreiving sensor data... (%ss)" % (round((step3 - step2), 1))

                    pipeline = [
                                { "$sort" : SON([("ts", -1)]) },
                                { "$match": { "id": user_id, "ts": {"$gt": installDate} } },
                                { "$limit": 1},
                                { "$group": { 
                                    "_id": "$id", 
                                    "ts": { "$push": "$ts" }, 
                                    "rain": { "$push": "$r" }, 
                                    "temp": { "$push": "$t1" }, 
                                    "hum": { "$push": "$h" }, 
                                    "wind": { "$push": "$w" }, 
                                    "solar": { "$push": "$s" } 
                                    } 
                                }
                                ]
                    dict["uploads"] = list(sensors.aggregate(pipeline, allowDiskUse = True))

                    step4 = time.time()
                    print "4: Printing data... (%ss)" % (round((step4 - step3), 1))

                    response = jsonify(**dict)
                else:   
                    response = jsonify(**{"Error": "Unauthorized access."})
            else:   
                    response = jsonify(**{"Error": "Wrong username and password."})
        else:
            response = jsonify(**{"Error": "User doesn't exist."})

    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/pandas-api', methods = ["GET", "POST"])
# @api.requires_auth
def docsAPI():
    step0 = time.time()
    print "0: Initializing... (API)"
    if request.method == "GET":
        try:
            username = request.args.get("user")
            password = request.args.get("password")
            user_id  = int(request.args.get("id"))
        except:
            response = jsonify(**{"Error": "No API key entered."})

        user     = users.find_one({'username': username})
        
        if user:
            hashed_pwd = user["password"]

            if hashed_pwd:
                usr = User(username, hashed_pwd)

            if usr.is_correct_password(password):
                step1 = time.time()
                print "1: Credentials match... (%ss)" % (round((step1 - step0), 1))
                if user["sensors"] == True or user_id in user["sensors"]:
                    output = {}

                    pipeline = [
                                { "$match": { "id": user_id } },
                                { "$group": { "_id": "$id", "lt": { "$push": "$lt" }, "ln": { "$push": "$ln" }, "name": { "$push": "$name" }, "installDate": { "$push": "$date" } } },
                                { "$sort" : SON([("_id", 1)]) }
                                ]
                    cursor = ids.aggregate(pipeline, allowDiskUse = True)
                    data = [x for x in cursor]
                    output["meta"] = list(data)
                    try:
                        installDate  = datetime.strptime(output["meta"][0]["installDate"][0], "%Y-%m-%d")
                    except:
                        installDate  = output["meta"][0]["installDate"][0]

                    step2 = time.time()
                    print "2: Meta data loaded... (%ss)" % (round((step2 - step1), 1))
                    
                    pipeline = [
                                { "$match": { "id": user_id, "ts": {"$gt": installDate} } },
                                { "$group": { "_id": "$ts", "rain": { "$last": "$r" }, "temp1": { "$last": "$t1" }, "temp2": { "$last": "$t2" }, "humidity": { "$last": "$h" }, "wind_speed": { "$last": "$w" } } },
                                { "$sort" : SON([("_id", 1)]) }
                                ]
                    cursor = sensors.aggregate(pipeline, allowDiskUse = True)
                    data   = [x for x in cursor]
                    d0     = pd.DataFrame(data)

                    step3 = time.time()
                    print "3: Sensor data loaded... (%ss)" % (round((step3 - step2), 1))
                    df = d0.rename(columns={"_id":"datetime"})
                    df["rain"]          = config.get_sensor_rain_calibration(df["rain"])
                    df["wind_speed"]    = config.get_sensor_rain_calibration(df["wind_speed"])
                    output["uploads"]     = [dict((k, _maybe_box_datetimelike(v)) for k, v in zip(df.columns, row) if v != None and v == v) for row in df.values]

                    step4 = time.time()
                    print "4: Printing data... (%ss)" % (round((step4 - step3), 1))

                    response = jsonify(**output)
                else:   
                    response = jsonify(**{"Error": "Unauthorized access."})
            else:   
                    response = jsonify(**{"Error": "Wrong username and password."})
        else:
            response = jsonify(**{"Error": "User doesn't exist."})

    response.headers.add('Access-Control-Allow-Origin', '*')
    step5 = time.time()
    print "5: Completed... (%ss)" % (round((step5 - step0), 1))
    return response


# https://enigmatic-caverns-27645.herokuapp.com/add_data/1=<'id':100,'t1':30,'t2':32,'h':50,'w':20,'r':0,'p':1,'s':3,'lt':25.571778,'ln':91.89559>

# set the secret key. keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#mongodb password: 89aok03fqogpnuuqn8dlcc85s9

if __name__ == '__main__':
    app.run(debug=True)



##########################################
