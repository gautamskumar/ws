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
import aw_closest_loc
import sm_closest_loc
import anuman_closest_loc
import imd_closest_loc
import config
import calc
import dailysums
import re
import sys
import StringIO
import requests
import api
import compvariance
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
solars      = db.solars
markets     = db.markets
aw          = db.aw
sm          = db.smnew
wrf         = db.anuman
imd         = db.imd
imd_lat_lng = db.imd_lat_lng    
imdhist     = db.imdhist
firmware    = db.firmware
R2          = db.R2
power       = db.power
traffic     = db.traffic
statePower  = db.statePower
power_price = db.power_price
dts         = db.dts
iex         = db.iex
davis       = db.davis
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
# # imdhist.create_index([("lt", pymongo.ASCENDING), ("ln", pymongo.ASCENDING), ("ts", pymongo.ASCENDING)], unique=True, sparse=True)
# dts.create_index('name')
# power.create_index('ts')
# imd.create_index("name")
# sm.create_index("loc")
# wrf.create_index("loc")
# traffic.create_index("loc")
# power.create_index([("load", pymongo.ASCENDING), ("ts", pymongo.ASCENDING)])
# power_price.create_index([("ts", pymongo.DESCENDING)])
# iex.create_index("ts")
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

@app.route('/ppm-results/<id>')
def ppmResults(id):
    return render_template('ppm.html', sensors = sensors.find({'id': int(id)}).sort('ts', pymongo.DESCENDING))    

@app.route('/imd-results/<id>')
def imdResults(id):
    #if 'username' in session:
        # if session['username'] != "gkumar09@gmail.com":
        #     if int(id) not in users.find({'username': session['username']})[0]['sensors']:
        #         return redirect(url_for('notAuthorized'))
    return render_template('results-imd.html', sensors = imd.find({'name': id.title()}).sort('ts', pymongo.DESCENDING))

@app.route('/insurance/',methods=["GET","POST"])
def insurance():
    years   = [2010,2011,2012,2013,2014]
    payouts = {}
    if request.method == 'POST':
        starts    = request.form.getlist('starts')
        ends      = request.form.getlist('ends')
        strikes   = request.form.getlist('strikes')
        exits     = request.form.getlist('exits')
        notionals = request.form.getlist('notionals')
        for i in range(0,starts.__len__()):
            strike   = float(strikes[i])
            exit     = float(exits[i])
            notional = float(notionals[i])
            
            for year in years:
                start = datetime.strptime(starts[i], '%Y-%m-%d').replace(year=year)
                end   = datetime.strptime(ends[i], '%Y-%m-%d').replace(year=year)
                print start, end
                pipeline = [
                            { "$match": { "id": "r", "ts": {"$gt": start, "$lt": end}, "lt": 28.5, "ln": 77.25 } },
                            { "$group": {"_id": "$val", "ts": {"$push": "$ts"}, "lt": {"$push": "$lt"}, "ln": {"$push": "$ln"} } },
                            { "$sort" : SON([("ts", -1)]) }
                            ]
                vals  = list(imdhist.aggregate(pipeline, allowDiskUse = True))
                total = sum([v['_id'] for v in vals])
                print "total rain:", total, ",", "strike:", strike, ",", "exit:", exit
                if total > strike and total <= exit:
                    payout = notional*(total - strike)
                    try:
                        payouts[str(i)] += payout
                    except:
                        payouts[str(i)] = payout
                    try:
                        payouts[str(year)] += round(payout,1)
                    except:
                        payouts[str(year)] = round(payout,1)
                    try:
                        payouts["cover"] += payout
                    except:
                        payouts["cover"] = payout

            payouts[str(i)] = round(payouts[str(i)]/years.__len__(),1)
        payouts["cover"] = round(payouts["cover"]/(years.__len__()),1)
        print payouts
    return render_template('insurance.html')

@app.route('/insurance-dashboard/')
def insuranceDashboard():
    hTempPhases = [
                    {
                        "start"     : datetime(2014, 7, 11),
                        "end"       : datetime(2014, 8, 12),
                        "notionals" : [20, 40],
                        "strikes"   : [10, 15, 20],
                        "threshold" : 36
                    },
                    {
                        "start"     : datetime(2014, 8, 12),
                        "end"       : datetime(2014, 9, 14),
                        "notionals" : [20, 40],
                        "strikes"   : [5, 10, 15],
                        "threshold" : 35
                    },
                    {
                        "start"     : datetime(2014, 9, 14),
                        "end"       : datetime(2014, 10, 4),
                        "notionals" : [20, 40],
                        "strikes"   : [10, 15, 20],
                        "threshold" : 20
                    },
                    {
                        "start"     : datetime(2014, 10, 4),
                        "end"       : datetime(2014, 10, 23),
                        "notionals" : [20, 40],
                        "strikes"   : [0, 5, 10],
                        "threshold" : 20
                    }
                ]
    
    hRainPhases = [
                    {
                        "start"     : datetime(2014, 7, 11),
                        "end"       : datetime(2014, 8, 12),
                        "notionals" : [10, 20],
                        "strikes"   : [220, 270, 345]
                    },
                    {
                        "start"     : datetime(2014, 8, 12),
                        "end"       : datetime(2014, 9, 14),
                        "notionals" : [10, 20],
                        "strikes"   : [200, 250, 330]
                    },
                    {
                        "start"     : datetime(2014, 9, 14),
                        "end"       : datetime(2014, 10, 4),
                        "notionals" : [10, 20],
                        "strikes"   : [160, 210, 290]
                    },
                    {
                        "start"     : datetime(2014, 10, 4),
                        "end"       : datetime(2014, 10, 23),
                        "notionals" : [10, 20],
                        "strikes"   : [130, 180, 260]
                    }
                ]

    lRainPhases = [
                    {
                        "start"     : datetime(2014, 7, 11),
                        "end"       : datetime(2014, 8, 12),
                        "notionals" : [15],
                        "strikes"   : [190, 0]
                    },
                    {
                        "start"     : datetime(2014, 8, 12),
                        "end"       : datetime(2014, 9, 14),
                        "notionals" : [10],
                        "strikes"   : [165, 0]
                    },
                    {
                        "start"     : datetime(2014, 9, 14),
                        "end"       : datetime(2014, 10, 4),
                        "notionals" : [12],
                        "strikes"   : [85, 0]
                    }
                ]
    print "Phases loaded."

    def findCoord(_DF, _LT, _LN):
        _d1 = _DF.loc[_DF["lt"] == _LT]
        _d2 = _d1.loc[_d1["ln"] == _LN]
        return _d2

    def tempPayout(_DF, _PHASES, _YEAR, _VAL):
        payouts = []
        for phase in _PHASES:
            notionals   = phase["notionals"]
            strikes     = phase["strikes"]
            payout      = 0
            start       = phase["start"].replace(year=_YEAR)
            end         = phase["end"].replace(year=_YEAR)
            d1          = _DF.loc[_DF["ts"] >= start]
            d2          = d1.loc[d1["ts"] < end]
            ## Too high temperature (High temp)
            if _VAL == 1:
                d3      = d2.loc[d2["val"] > phase["threshold"]]
                total   = (d3["val"] - phase["threshold"]).sum()
                for i in range(0, notionals.__len__()):
                    if total > strikes[i]:
                        payout += (min(strikes[i+1], total) - strikes[i])*notionals[i]
            ## Too low temperature (Low temp)
            if _VAL == 0:
                d3      = d2.loc[d2["val"] < phase["threshold"]]
                total   = (phase["threshold"] - d3["val"]).sum()
                for i in range(0, notionals.__len__()):
                    if total < strikes[i]:
                        payout += (strikes[i] - max(strikes[i+1], total))*notionals[i]
            payouts.append({"payout": payout, "total": total, "start": start, "end": end, "phase": _PHASES.index(phase)+1})
        return pd.DataFrame(payouts)[['phase', 'start', 'end', 'total', 'payout']]

    def rainPayout(_DF, _PHASES, _YEAR, _VAL):
        payouts = []
        for phase in _PHASES:
            notionals   = phase["notionals"]
            strikes     = phase["strikes"]
            payout      = 0
            start       = phase["start"].replace(year=_YEAR)
            end         = phase["end"].replace(year=_YEAR)
            d1          = _DF.loc[_DF["ts"] >= start]
            d2          = d1.loc[d1["ts"] < end]
            ## Take the sum of rainfall between phase start and end dates
            total       = d2["val"].sum()
            for i in range(0, notionals.__len__()):
                ## Too much rain (Rain surplus)
                if _VAL == 1:
                    if total > strikes[i]:
                        payout += (min(strikes[i+1], total) - strikes[i])*notionals[i]
                ## Not enough rain (Rain deficit)
                if _VAL == 0:
                    if total < strikes[i]:
                        payout += (strikes[i] - max(strikes[i+1], total))*notionals[i]
            payouts.append({"payout": payout, "total": total, "start": start, "end": end, "phase": _PHASES.index(phase)+1})
        return pd.DataFrame(payouts)[['phase', 'start', 'end', 'total', 'payout']]

    print "Functions defined."

    pipeline = [
                { "$match": { "id": "t", "lt": 25.5, "ln": 85.5 } },
                { "$sort" : SON([("ts", -1)]) }
                ]
    df = pd.DataFrame(list(imdhist.aggregate(pipeline, allowDiskUse = True)))

    print "Data loaded."

    dicts = []
    for year in range(1950,2015):
        pay = tempPayout(findCoord(df,25.5,85.5), hTempPhases, year, 1)
        for index, row in pay.iterrows():
            out = {"year": year, "legend": "Phase "+str(row['phase']), "payout": row['payout']}
            print out
            dicts.append(out)

    print "Calcs done."

    pays = pd.DataFrame(dicts)
    data = []
    for i in range(0, pays.groupby("legend")["legend"].nunique().__len__()):
        legend = pays.groupby("legend")["legend"].nunique().index[i]
        df = pays.loc[pays["legend"] == legend]
        bar_data(df["year"], df["payout"], legend, data)

    print "Generate jsons"

    title = 'Payouts'

    layout = go.Layout(
        title=title,
        barmode='stack',
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)
    return render_template('analytics.html')
    
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

@app.route('/solar-dashboard')
def solarDashboard():
    # if 'username' in session:
    #     if session['username'] != "gkumar09@gmail.com":
    #         user        = users.find({'username': session['username']})
    #         valid_ids   = user[0]['sensors']
    #         name        = user[0]['firstName']
    #         print valid_ids

    # else:
    #     return redirect(url_for('notAuthorized'))

    valid_ids = [231, 232, 233]
    valid_ids = [209]

    pipeline = [
        { "$match": { "id": {'$in': valid_ids} } },
        { "$sort" : SON([("id", 1), ("ts", 1)]) },
        { "$group": { 
            "_id": "$id",
            "ts" : { "$push": "$ts" },
            "s"  : { "$push": "$s" },
            } 
        }
        ]
    #kw, cost, depreciation, size, projected annual output, PPA
    sensorUploads = list(sensors.aggregate(pipeline, allowDiskUse = True))
    idsMeta       = list(ids.find({'id':{'$in': valid_ids}}).sort('id', pymongo.DESCENDING))
    solarMeta     = list(solars.find({'id':{'$in': valid_ids}}).sort('id', pymongo.DESCENDING))

    solarDicts = []

    for i in range(0,sensorUploads.__len__()):
        try:
            s                   = sensorUploads[i]
            freq                = int(idsMeta[i]["freq"])
            installationSize    = solarMeta[i]["size"]
            pct_dep             = solarMeta[i]["pct_dep"]
            cost                = solarMeta[i]["cost"]
            projOutput          = solarMeta[i]["projOutput"]
            lt                  = float(idsMeta[i]["lt"])
            ln                  = float(idsMeta[i]["ln"])
            stationName         = idsMeta[i]["name"]
            try:
                installDate = datetime.strptime(str(idsMeta[i]["date"]), '%Y-%m-%d %H:%M:%S')
            except:
                installDate = datetime.strptime(str(idsMeta[i]["date"]), '%Y-%m-%d')
            df                  = pd.DataFrame(s)
            df                  = df.set_index('ts').ix[installDate:]
            dailies                 = df.groupby(pd.TimeGrouper('D')).mean()
            dailies["ts"]           = dailies.index
            dailies["uptime"]       = df.groupby(pd.TimeGrouper('D')).size()/(60/freq*24)
            dailies["efficiency"]   = dailies["s"]*9/10
            dailies["power"]        = dailies["efficiency"]*(installationSize)*24
            oneDayForecast      = dailies["power"][-6:-1].mean()
            oneYearForecast     = dailies["power"].mean()*365
            #Geometric seriesL (1 - eff^years)/(1 - eff)
            tfiveYearForecast   = dailies["power"].mean()*365*((1-(1-pct_dep)**25)/(1-(1-pct_dep)))
            weekActuals         = dailies["efficiency"][-8:-1].mean()*100
            weekUptime          = dailies["uptime"][-8:-1].mean()*100
            totalActuals        = dailies["efficiency"].mean()*100
            totalUptime         = dailies["uptime"].mean()*100
            histVolatility      = dailies["efficiency"].std()/dailies["efficiency"].mean()*100
            ts                  = df[-1:].index.to_pydatetime()[0]
            solarDict = {
                            "id"                : int(df["_id"][0]),
                            "ts"                : ts,
                            "oneDayForecast"    : round(oneDayForecast,1),
                            "oneYearForecast"   : round(oneYearForecast,0),
                            "tfiveYearForecast" : round(tfiveYearForecast,0),
                            "weekActuals"       : round(weekActuals,1),
                            "weekUptime"        : round(weekUptime,1),
                            "totalActuals"      : round(totalActuals,1),
                            "totalUptime"       : round(totalUptime,1),
                            "histVolatility"    : round(histVolatility,1),
                            "lt"                : lt,
                            "ln"                : ln,
                            "name"              : stationName,
                            "projOutput"        : projOutput,
                            "pct_dep"           : pct_dep,
                            "size"              : installationSize,
                            "cost"              : cost,
                        }
            solarDicts.append(solarDict)
        except:
            continue
    return render_template('solar-dashboard.html', solarDicts = solarDicts, name = "Gaurav")
    # return redirect(url_for('notloggedin'))

@app.route('/solar-manager', methods=["GET","POST"])
def solarManger():
    if 'username' in session:
        
        if request.method == "POST":
            # Do stuff
            sensorId    = int(request.form.get('id'))
            name        = request.form.get('name')
            lt          = float(request.form.get('lt'))
            ln          = float(request.form.get('ln'))
            size        = float(request.form.get('size'))
            cost        = float(request.form.get('cost'))
            projOutput  = float(request.form.get('projOutput'))
            PPA         = float(request.form.get('PPA'))
            pct_dep     = float(request.form.get('pct_dep'))

            print "Updating IDs and solars..."

            ids.update({
              'id': sensorId
            },{
              '$set': {
                'updated_at': datetime.now(),
                'name'      : name,
                'lt'        : lt,
                'ln'        : ln
              }
            }, upsert=False, multi=False)

            solars.update({
              'id': sensorId
            },{
              '$set': {
                'updated_at': datetime.now(),
                'size'      : size,
                'cost'      : cost,
                'projOutput': projOutput,
                'PPA'       : PPA,
                'pct_dep'   : pct_dep
              }
            }, upsert=False, multi=False)

        if session['username'] != "gkumar09@gmail.com":
            valid_ids = users.find({'username': session['username']})[0]['sensors']
            idsMeta       = list(ids.find({'id':{'$in': valid_ids}}).sort('id', pymongo.DESCENDING))
            solarMeta     = list(solars.find({'id':{'$in': valid_ids}}).sort('id', pymongo.DESCENDING))

        return render_template('solar-manager.html', jsonObjs = solarMeta, idsObjs = idsMeta)
    return redirect(url_for('notloggedin'))

def getValues(col, df, target):
    values = []
    for l in df[col].tolist():
        try:
            values.append(l.values()[0])
        except:
            values.append(0)
    target[col] = values

@app.route('/energy-dashboard')
def energyDashboard():

    print "0: Initializing power..."
    step0 = time.time()
    #kw, cost, depreciation, size, projected annual output, PPA
    transformers = list(dts.find( { 'lt': { '$exists': True, '$nin': ['']  } } ) )
    cols = []
    for t in transformers:
        cols.append(t["id"])

    pipeline = [
            { "$match": {} }
            ]
    #kw, cost, depreciation, size, projected annual output, PPA
    power_data = list(power.aggregate(pipeline, allowDiskUse = True))

    step1 = time.time()
    print "1: Data loaded... (%ss)" % (round((step1 - step0), 1))

    areas  = []
    sched  = []
    load   = []
    ltimes = []
    diffs  = []
    for p in power_data:
        if p["ts"] > datetime(2017,8,31):
            try:
                sched.append(float(p[u'schedule']))
                load.append(float(p[u'load']))
                ltimes.append(p[u'ts'])
            except:
                try:
                    areas.append(p)
                except:
                    continue

    step2 = time.time()
    print "2: Power data sorted... (%ss)" % (round((step2 - step1), 1))

    df      = pd.DataFrame(areas)
    target  = pd.DataFrame(df["ts"])

    for col in cols:
        print cols.index(col), col
        getValues(col, df, target)

    peaks  = target.set_index('ts').groupby(pd.TimeGrouper('D')).max()
    peaks["ts"] = peaks.index
    peaks["weekday"] = peaks["ts"].apply(lambda x: x.weekday())
    COVs = peaks.groupby(peaks["weekday"]).std().mean()*1000*24*365*.1/1000000

    name = "Gaurav"

    energyDicts = []

    for i in range(0,cols.__len__()):
        try:
            name = transformers[i]["name"]
            lt   = float(transformers[i]["lt"])
            ln   = float(transformers[i]["ln"])
            COV  = COVs[i]
            energyDict = {
                            "name" : name,
                            "lt"   : lt,
                            "ln"   : ln,
                            "COV"  : COV
                        }
            energyDicts.append(energyDict)
            print energyDicts
        except:
            continue
    return render_template('energy-dashboard.html', energyDicts = energyDicts, name = name)

@app.route('/energy-manager', methods=["GET","POST"])
def energyManager():        
    if request.method == "POST":
        # Do stuff
        sensorId    = request.form.get('name')
        discom      = request.form.get('discom')
        lt          = float(request.form.get('lt'))
        ln          = float(request.form.get('ln'))

        print "Updating IDs and solars..."
        print sensorId, discom, lt, ln
        dts.update({
          'id': sensorId
        },{
          '$set': {
            'updated_at': datetime.now(),
            'discom'    : discom,
            'lt'        : lt,
            'ln'        : ln
          }
        }, upsert=False, multi=False)

    transformers = list(dts.find({}).sort('id', pymongo.DESCENDING))
    return render_template('energy-manager.html', idsObjs = transformers)

@app.route('/imd-dashboard')
def imdDashboard():
    if 'username' in session:
        cur_lst = []
        docs = []
        name = 'Sanjiv'

        cur_lst.append(imd_lat_lng.find({}))
        print imd_lat_lng.find({})
        for cursor in cur_lst:
            print cursor
            for doc in cursor:
                docs.append(doc)
                print doc
        
        return render_template('imd-dashboard.html', docs = docs, name = name)
    return redirect(url_for('notloggedin'))

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

@app.route('/comparison/<id1>/<id2>')
def comparison(id1, id2):
    # fetch data for that id
    sensor_data1 = sensors.find({'id': int(id1)}).sort('ts', pymongo.DESCENDING).limit(10000)
    sensor_data2 = sensors.find({'id': int(id2)}).sort('ts', pymongo.DESCENDING).limit(10000)

    print "got the data"

    data = []
    dates1 = [] # %Y-%m-%d %H:%M:%S
    temps1 = []
    humidities1 = []
    rainfall1 = []
    windspeed1 = []
    pressures1 = []
    signals1 = []
    
    dates2 = [] # %Y-%m-%d %H:%M:%S
    temps2 = []
    humidities2 = []
    rainfall2 = []
    windspeed2 = []
    pressures2 = []
    signals2 = []

    # Extract Data from JSON Objects into arrays
    for elem in sensor_data1:
        if 't1' in elem:
            dates1.append(datetime.strptime(elem['ts'], '%Y-%m-%d %H:%M:%S'))
            temps1.append(elem['t1'])
            humidities1.append(elem['h'])
            rainfall1.append(config.get_sensor_rain_calibration(float(elem['r'])))
            windspeed1.append(config.get_sensor_wind_calibration(float(elem['w'])))
            pressures1.append(elem['p'])
            if 'sg' in elem:
                signals1.append(elem['sg'])
            else:
                signals1.append(str(0))

    print "sorted sensor 1"

    for elem in sensor_data2:
        if 't1' in elem:
            dates2.append(datetime.strptime(elem['ts'], '%Y-%m-%d %H:%M:%S'))
            temps2.append(elem['t1'])
            humidities2.append(elem['h'])
            rainfall2.append(config.get_sensor_rain_calibration(float(elem['r'])))
            windspeed2.append(config.get_sensor_wind_calibration(float(elem['w'])))
            pressures2.append(elem['p'])
            if 'sg' in elem:
                signals2.append(elem['sg'])
            else:
                signals2.append(str(0))

    print "sorted sensor 2"

    start_date = ""
    end_date = ""

    trace_data(dates1, temps1, "1 Temperature (C)", data)
    trace_data(dates1, humidities1, "1 Humidity (%)", data)
    trace_data(dates1, rainfall1, "1 Rainfall (mm)", data)
    trace_data(dates1, windspeed1, "1 Wind Speed (km/h)", data)
    trace_data(dates1, signals1, "1 Signal (dB)", data)

    trace_data(dates2, temps2, "2 Temperature (C)", data)
    trace_data(dates2, humidities2, "2 Humidity (%)", data)
    trace_data(dates2, rainfall2, "2 Rainfall (mm)", data)
    trace_data(dates2, windspeed2, "2 Wind Speed (km/h)", data)
    trace_data(dates2, signals2, "2 Signal (dB)", data)

    if start_date == "":
        start = str(dates1[0].date())
        end = str(dates1[-1].date())
    else:
        start = str(start_date.date())
        end = str(end_date.date())

    title = 'Analytics for '+str(id1)+' and '+str(id2)

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#D0D0D0'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('rating.html')

@app.route('/imdhist/<state>/<loc>/<type>')
def imdHist(type, state, loc):
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        # Creating address string from state and location name
        address = loc + ",+" + state + ",+India"
        print address
        headers = {"address": address, "key": MAPS_API_KEY}
        response = requests.get(url, headers)
        json_result = json.loads(response.content)
        lat = json_result["results"][0]["geometry"]["location"]["lat"]
        lng = json_result["results"][0]["geometry"]["location"]["lng"]
        coords = [lat, lng]
        print coords
    except Exception:
        print "Error fetching information for " + loc + ", " + state
        return redirect(url_for('locationNotFound'))
    if type == "rain":
        ltln = calc.find25Locations(coords)
        lt = ltln[0]
        ln = ltln[1]
        print lt, ln
        # fetch data for that id
        pipeline = [
                    { "$match": { "id": "r", "lt": lt, "ln": ln } },
                    { "$sort" : SON([("ts", -1)]) }
                    ]
        imd_data = list(imdhist.aggregate(pipeline, allowDiskUse = True))
    elif type == "temp":
        ltln = calc.findLocation(coords)
        lt = ltln[0]
        ln = ltln[1]
        print ltln
        # fetch data for that id
        pipeline = [
                    { "$match": { "id": "t", "lt": lt, "ln": ln } },
                    { "$sort" : SON([("ts", -1)]) }
                    ]
        imd_data = list(imdhist.aggregate(pipeline, allowDiskUse = True))

    data = []
    dates = []
    vals = []
    # Extract Data from JSON Objects into arrays
    for elem in imd_data:
        dates.append(elem['ts'])
        vals.append(elem['val'])
    trace_data(dates, vals, "Temperature (C)", data)

    pct_dict = {"1":"","10":"", "30":"","70":"","90":"","99":""}

    nvals = np.array(vals)

    pct_dict["1"] = np.around(np.percentile(nvals, 1), decimals=1)
    pct_dict["10"] = np.around(np.percentile(nvals, 10), decimals=1)
    pct_dict["30"] = np.around(np.percentile(nvals, 30), decimals=1)
    pct_dict["70"] = np.around(np.percentile(nvals, 70), decimals=1)
    pct_dict["90"] = np.around(np.percentile(nvals, 90), decimals=1)
    pct_dict["99"] = np.around(np.percentile(nvals, 99), decimals=1)

    title = 'Historical Data for ' + loc.title() + ', ' + state.title() + ' (' + str(lt) + ', ' + str(ln) + ')'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#D0D0D0'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('percentiles.html', percentiles=pct_dict)

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

            aw_queue      = aw_closest_loc.closest_loc_queue(lt, ln)
            sm_queue      = sm_closest_loc.closest_loc_queue(lt, ln)
            anuman_queue  = anuman_closest_loc.closest_loc_queue(lt, ln)
            imd_queue     = imd_closest_loc.closest_loc_queue(lt, ln)
            num_locations = 1
            aw_array      = []
            sm_array      = []
            anuman_array  = []
            imd_array     = []
            for i in range(0, num_locations):
                aw_tuple     = aw_queue.get()
                sm_tuple     = sm_queue.get()
                anuman_tuple = anuman_queue.get()
                imd_tuple    = imd_queue.get()
                aw_array.append((aw_tuple[0], str(aw_tuple[1]["location"])))
                sm_array.append((sm_tuple[0], str(sm_tuple[1]["location"])))
                anuman_array.append((anuman_tuple[0], str(anuman_tuple[1]["location"])))
                imd_array.append((imd_tuple[0], str(imd_tuple[1]["location"])))
                print "appended: ", i

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
                'aw'        : aw_array,
                'sm'        : sm_array,
                'wrf'       : anuman_array,
                'imd'       : imd_array
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

@app.route('/current/<state>/<loc>/<type>/<day>')
def calculate(state, loc, type, day):
    # if 'username' in session:
    #     if session['username'] != "gkumar09@gmail.com":
    #         if int(id) not in users.find({'username': session['username']})[0]['sensors']:
    #             return redirect(url_for('notAuthorized'))
    # else:
    #     return redirect(url_for('notAuthorized'))

    # 1. Get coordinates of searched place

    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        # Creating address string from state and location name
        address = loc + ",+" + state + ",+India"
        headers = {"address": address, "key": MAPS_API_KEY}
        response = requests.get(url, headers)
        json_result = json.loads(response.content)
        lat = json_result["results"][0]["geometry"]["location"]["lat"]
        lng = json_result["results"][0]["geometry"]["location"]["lng"]
        coords = [lat, lng]
        print coords
    except Exception:
        print "Error fetching information for " + loc + ", " + state
        return redirect(url_for('locationNotFound'))

    # 2. Find names of nearest data points from sensors, AW, SM, WRF, and IMD 

    sensor_queue = sensor_closest_loc.closest_loc_queue(lat, lng)
    aw_queue = aw_closest_loc.closest_loc_queue(lat, lng)
    sm_queue = sm_closest_loc.closest_loc_queue(lat, lng)
    anuman_queue = anuman_closest_loc.closest_loc_queue(lat, lng)
    imd_queue = imd_closest_loc.closest_loc_queue(lat, lng)
    num_locations = 1
    sensor_array = []
    aw_array = []
    sm_array = []
    wrf_array = []
    imd_array = []
    for i in range(0, num_locations):
        sensor_tuple = sensor_queue.get()
        aw_tuple = aw_queue.get()
        sm_tuple = sm_queue.get()
        anuman_tuple = anuman_queue.get()
        imd_tuple = imd_queue.get()
        sensor_array.append((aw_tuple[0], str(sensor_tuple[1]["name"])))
        aw_array.append((aw_tuple[0], str(aw_tuple[1]["location"])))
        sm_array.append((sm_tuple[0], str(sm_tuple[1]["location"])))
        wrf_array.append((anuman_tuple[0], str(anuman_tuple[1]["location"])))
        imd_array.append((imd_tuple[0], str(imd_tuple[1]["location"])))
        print "appended: ", i

    sensor_name = sensor_array[0][1]
    sensor_id = ids.find_one({"name": sensor_name})["id"]
    aw_name = aw_array[0][1]
    sm_name = sm_array[0][1]
    wrf_name = wrf_array[0][1]
    imd_name = imd_array[0][1]
    print sensor_id, aw_name, sm_name, wrf_name, imd_name

    # 3. Let's start fetching some data.

    # ...from our sensors
    print "Yobi closest location: " + str(sensor_name)
    sensor_uploads = list(
        sensors.find({'id': int(207)}).sort('ts', pymongo.ASCENDING))
    print sensor_uploads

    # ...from AW
    print "Accuweather closest location: " + str(aw_name)
    aw_timestamps = list(
        aw.find({'loc': aw_name.lower(), "n_predict": (int(day)+1)}).sort('timestamp', pymongo.ASCENDING))

    if len(aw_timestamps) < 1:
        aw_timestamps = list(
            aw.find({'loc': aw_name, "n_predict": (int(day)+1)}).sort('timestamp', pymongo.ASCENDING))

    # ...from SM
    print "Skymet closest location: " + str(sm_name)
    sm_timestamps = list(
        sm.find({'loc': sm_name.lower(), "n_predict": int(day)}).sort('timestamp', pymongo.ASCENDING))

    if len(sm_timestamps) < 1:
        sm_timestamps = list(
            sm.find({'loc': sm_name, "n_predict": int(day)}).sort('timestamp', pymongo.ASCENDING))

    # ...from WRF
    print "WRF closest location: " + str(wrf_name)
    regx = re.compile("(.*)" + wrf_name, re.IGNORECASE)
    wrf_timestamps = list(
        wrf.find({'loc': regx, "n_predict": int(day)}, {"_id": 0}).sort('date', pymongo.ASCENDING))

    # ...from IMD
    print "IMD closest location: " + str(imd_name)
    imd_timestamps = list(
        imd.find({'name': imd_name}).sort('ts', pymongo.ASCENDING))

    # 4. Let's get the type of data requested
    print type

    if type == "rain":
        data = []

        # Adding up sensor rainfall for individual days:
        sensor_values = []
        sensor_dates = []
        curr_date = datetime.strptime(sensor_uploads[0]["ts"], '%Y-%m-%d %H:%M:%S')
        curr_date_rainfall = 0.0
        # for every data point
        for i in range(0, sensor_uploads.__len__()):
            # if the day is the same
            try:
                time0 = datetime.strptime(str(sensor_uploads[i]["ts"]), '%Y-%m-%d %H:%M:%S').date()
            except:
                time0 = sensor_uploads[i]["ts"].date()
            if time0 == curr_date.date():
                try:
                    curr_date_rainfall += float(sensor_uploads[i]["r"])
                except:
                    curr_date_rainfall += 0
            # if it's a new day:
            else:
                # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
                # Accounting for
                sensor_dates.append(curr_date)
                sensor_values.append(config.get_sensor_rain_calibration(curr_date_rainfall))
                try:
                    curr_date_rainfall = float(sensor_uploads[i]["r"])
                except:
                    curr_date_rainfall = 0
                try:
                    curr_date = datetime.strptime(sensor_uploads[i]["ts"], '%Y-%m-%d %H:%M:%S')
                except:
                    curr_date = sensor_uploads[i]["ts"]

        # Adding up AW rainfall data for indivual days:
        aw_dates = []
        aw_values =[]

        for i in range(0, aw_timestamps.__len__() / 2):
            aw_dates.append(aw_timestamps[2 * i]['timestamp'])
            aw_rain = (float(aw_timestamps[2 * i]["rain"]) + float(aw_timestamps[2 * i + 1]["rain"]))
            aw_values.append(aw_rain)

        # Adding up SM rainfall data:
        sm_dates = []
        sm_values = []

        for timestamp in sm_timestamps:
            sm_dates.append(datetime.strptime(timestamp['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))
            sm_values.append(timestamp['rain'])

        # Adding up WRF rainfall data:
        wrf_dates = []
        wrf_max = []
        wrf_min = []

        for timestamp in wrf_timestamps:
            wrf_dates.append(datetime.strptime(timestamp['date'], '%Y-%m-%d'))
            wrf_max.append(timestamp['rmax'])
            wrf_min.append(timestamp['rmin'])


        # Adding up IMD rainfall data:
        imd_dates = []
        imd_values = []
        curr_date = imd_timestamps[0]["ts"]
        curr_date_rainfall = 0.0
        # Iterating over found timestamps as pairs
        for i in range(0, imd_timestamps.__len__()):
            if imd_timestamps[i]["ts"].date() != curr_date.date():
            # if it's a new day:
                # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
                # Accounting for
                try:
                    curr_date_rainfall = float(imd_timestamps[i-1]["r"])
                except:
                    curr_date_rainfall = 0.0
                imd_dates.append(curr_date)
                imd_values.append(curr_date_rainfall)
                curr_date = imd_timestamps[i]["ts"]

        ltln = calc.find25Locations(coords)
        lt = ltln[0]
        ln = ltln[1]
        print lt, ln
        imdh = imdhist.find({'lt':lt,'ln':ln,'id':'r'}).sort('ts', pymongo.ASCENDING)
        # imdhistDates, imdhistValues = dailysums.imdhist(imdh)
        
        trace_data(sensor_dates, sensor_values, "Sensor (mm)", data)
        trace_data(aw_dates, aw_values, "GFS+ (mm)", data)
        trace_data(sm_dates, sm_values, "ECWMF+ (mm)", data)
        trace_data(wrf_dates, wrf_max, "WRF Max (mm)", data)
        trace_data(wrf_dates, wrf_min, "WRF Min (mm)", data)
        trace_data(imd_dates, imd_values, "IMD (mm)", data)
        # trace_data(imdhistDates, imdhistValues, "IMD Historical (mm)", data)

    if type == "temp":
        data = []

        # Adding up sensor rainfall for individual days:
        # sensor_values = []
        # sensor_dates = []
        # curr_date = datetime.strptime(sensor_uploads[0]["ts"], '%Y-%m-%d %H:%M:%S')
        # curr_date_temps = []
        # # for every data point
        # for i in range(0, sensor_uploads.__len__()):
        #     # if the day is the same
        #     if datetime.strptime(sensor_uploads[i]["ts"], '%Y-%m-%d %H:%M:%S').date() == curr_date.date():
        #         curr_date_temps.append(float(sensor_uploads[i]["t1"]))
        #     # if it's a new day:
        #     else:
        #         # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
        #         # Accounting for
        #         sensor_dates.append(curr_date)
        #         sensor_values.append(0)
        #         curr_date_temps = []
        #         curr_date = datetime.strptime(sensor_uploads[i]["ts"], '%Y-%m-%d %H:%M:%S')

        # Adding up AW rainfall data for indivual days:
        aw_dates = []
        aw_values =[]

        for i in range(0, aw_timestamps.__len__() / 2):
            aw_dates.append(aw_timestamps[2 * i]['timestamp'])
            #aw_temp = max([float(aw_timestamps[2 * i]["temp"]), float(aw_timestamps[2 * i + 1]["temp"])])
            #aw_values.append(aw_temp)

        # Adding up SM rainfall data:
        sm_dates = []
        sm_values = []

        for timestamp in sm_timestamps:
            sm_dates.append(datetime.strptime(timestamp['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))
            sm_values.append(timestamp['hightemp'])

        # Adding up WRF rainfall data:
        wrf_dates = []
        wrf_max = []

        for timestamp in wrf_timestamps:
            wrf_dates.append(datetime.strptime(timestamp['date'], '%Y-%m-%d'))
            wrf_max.append(timestamp['tmax'])


        # Adding up IMD rainfall data:
        imd_dates = []
        imd_values = []
        curr_date = imd_timestamps[0]["ts"]
        curr_date_temps = []
        # Iterating over found timestamps as pairs
        for i in range(0, imd_timestamps.__len__()):
            if imd_timestamps[i]["ts"].date():
                if imd_timestamps[i]["ts"].date() == curr_date.date():
                    try:
                        curr_date_temps.append(float(imd_timestamps[i]["t"]))
                    except:
                        curr_date_temps.append(0.0)
                else:
                    print "day over: " + str(curr_date) + ": " + str(curr_date_temps)
                    # Accounting for
                    imd_dates.append(curr_date)
                    try:
                        imd_values.append(max(curr_date_temps))
                    except:
                        imd_values.append(0.0)
                    curr_date_temps = []
                    curr_date = imd_timestamps[i]["ts"]

        ltln = calc.findLocation(coords)
        lt = ltln[0]
        ln = ltln[1]
        print ltln
        # fetch data for that id
        pipeline = [
                    { "$match": { "id": "t", "lt": lt, "ln": ln } },
                    { "$group": { "_id": "$ts", "val": { "$push": "$val" } } },
                    { "$sort" : SON([("_id", -1)]) }
                    ]
        imd_data = list(imdhist.aggregate(pipeline, allowDiskUse = True))

        # imdhistDates, imdhistValues = dailysums.imdhist_avg(imd_data)
        
        # trace_data(sensor_dates, sensor_values, "Sensor (C)", data)
        trace_data(aw_dates, aw_values, "GFS+ (C)", data)
        trace_data(sm_dates, sm_values, "ECWMF+ (C)", data)
        trace_data(wrf_dates, wrf_max, "WRF Max (C)", data)
        trace_data(imd_dates, imd_values, "IMD (C)", data)
        # trace_data(imdhistDates, imdhistValues, "IMD Historical (C)", data)

    try: 
        aw_errors = calc.imdError(sensor_dates, aw_dates, sensor_values, aw_values)
        aw_mean = np.mean(aw_errors[0])
        aw_stdev = np.std(aw_errors[0])
        aw_obs = aw_errors[0].__len__()
    except:
        aw_errors = ["Error", "Error"]
        aw_mean = "Error"
        aw_stdev = "Error"
        aw_obs = "Error"
    print aw_errors

    try:
        sm_errors = calc.imdError(sensor_dates, sm_dates, sensor_values, sm_values)
        sm_mean = np.mean(sm_errors[0])
        sm_stdev = np.std(sm_errors[0])
        sm_obs = sm_errors[0].__len__()
    except:
        sm_errors = ["Error", "Error"]
        sm_mean = "Error"
        sm_stdev = "Error"
        sm_obs = "Error"
    print sm_errors

    try:
        wrf_min_errors = calc.imdError(sensor_dates, wrf_dates, sensor_values, wrf_min)
        wrf_min_mean = np.mean(wrf_min_errors[0])
        wrf_min_stdev = np.std(wrf_min_errors[0])
        wrf_min_obs = wrf_min_errors[0].__len__()
        wrf_max_errors = calc.imdError(sensor_dates, wrf_dates, sensor_values, wrf_max)
        wrf_max_mean = np.mean(wrf_max_errors[0])
        wrf_max_stdev = np.std(wrf_max_errors[0])
        wrf_max_obs = wrf_max_errors[0].__len__()
    except:
        wrf_min_errors = ["Error", "Error"]
        wrf_min_mean = "Error"
        wrf_min_stdev = "Error"
        wrf_min_obs = "Error"
        wrf_max_errors = ["Error", "Error"]
        wrf_max_mean = "Error"
        wrf_max_stdev = "Error"
        wrf_max_obs = "Error"
    
    awcomp = aw_errors[1]
    smcomp = sm_errors[1]
    wmincomp = wrf_min_errors[1]
    wmaxcomp = wrf_max_errors[1]

    print wrf_min_errors
    #print wrf_max_errors

    try:
        awIMD   = calc.imdMetrics(awcomp)
        smIMD   = calc.imdMetrics(smcomp)
        wminIMD = calc.imdMetrics(wmincomp)
        wmaxIMD = calc.imdMetrics(wmaxcomp)
    except:
        awIMD   = {"PC": 0, "HSS": 0}
        smIMD   = {"PC": 0, "HSS": 0}
        wminIMD = {"PC": 0, "HSS": 0}
        wmaxIMD = {"PC": 0, "HSS": 0}

    awPC  = awIMD["PC"]
    awHSS = awIMD["HSS"]
    smPC  = smIMD["PC"]
    smHSS = smIMD["HSS"]
    wminPC  = wminIMD["PC"]
    wminHSS = wminIMD["HSS"]
    wmaxPC  = wmaxIMD["PC"]
    wmaxHSS = wmaxIMD["HSS"]

    title = 'Actuals recorded for '+loc.title()+', '+state.title()

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#D0D0D0'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('comparison.html',
        id = id, name = sensor_name,
        aw_loc = str(aw_name), aw_km = str(aw_array[0][0]), 
        aw_mean = aw_mean, aw_stdev = aw_stdev, aw_obs = aw_obs, 
        sm_loc = str(sm_name), sm_km = str(sm_array[0][0]), 
        sm_mean = sm_mean, sm_stdev = sm_stdev, sm_obs = sm_obs, 
        wrf_loc = str(wrf_name), wrf_km = str(wrf_array[0][0]),
        wrf_min_mean = wrf_min_mean, wrf_min_stdev = wrf_min_stdev, wrf_min_obs = wrf_min_obs, 
        wrf_max_mean = wrf_max_mean, wrf_max_stdev = wrf_max_stdev, wrf_max_obs = wrf_max_obs,
        awcomp = awcomp, awPC = awPC, awHSS = awHSS,
        smcomp = smcomp, smPC = smPC, smHSS = smHSS,
        wmincomp = wmincomp, wminPC = wminPC, wminHSS = wminHSS,
        wmaxcomp = wmaxcomp, wmaxPC = wmaxPC, wmaxHSS = wmaxHSS)

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

@app.route('/ranking-algo')
def timeSeries():
    
    step0 = time.time()
    print "0: Initializing... (ranking algo)"

    data = []
    pipeline = [
                { "$match": { "id": 4 } },
                { "$group": { "_id": "$ts", "r": { "$push": "$r" } } },
                { "$sort" : SON([("_id", 1)]) }
                ]
    yobi     = list(sensors.aggregate(pipeline, allowDiskUse = True))
    step1a   = time.time()
    print "1a: Loaded Yobi (%ss)" % (round((step1a - step0), 1))

    imd_timestamps  = list(imd.find({'name': 'Jowai'}).sort('ts', pymongo.ASCENDING))
    step1b = time.time()
    print "1b: Loaded IMD (%ss)" % (round((step1b - step1a), 1))
    aw_timestamps   = list(aw.find({'loc': 'Jowai', "n_predict": int(2)}).sort('timestamp', pymongo.ASCENDING))
    step1c = time.time()
    print "1c: Loaded AW (%ss)" % (round((step1c - step1b), 1))

    sm_timestamps   = list(sm.find({'loc': 'jowai', "n_predict": int(1)}).sort('timestamp', pymongo.ASCENDING))
    step1d = time.time()
    print "1d: Loaded SM (%ss)" % (round((step1d - step1c), 1))

    wrf_timestamps  = list(wrf.find({'loc': 'JaintiaHills_Jowai', "n_predict": int(1)}).sort('timestamp', pymongo.ASCENDING))
    step1e = time.time()
    print "1e: Loaded WRF (%ss)" % (round((step1e - step1d), 1))

    pipeline = [
                    { "$match": { "id": "r", "lt": 25.5, "ln": 92.5 } },
                    { "$group": {"_id": "$ts", "val": {"$push": "$val"} } },
                    { "$sort" : SON([("_id", 1)]) }
                    ]
    imdh = list(imdhist.aggregate(pipeline, allowDiskUse = True))
    step1f = time.time()
    print "1f: Loaded IMD historical (%ss)" % (round((step1f - step1e), 1))

    step1 = time.time()
    print "1: Data loaded... (%ss)" % (round((step1 - step0), 1))

    # Gets the daily sums for our sensors
    yobiDates, yobiValues       = dailysums.yobi(yobi)
    imdDates, imdValues         = dailysums.imd(imd_timestamps)
    awDates, awValues           = dailysums.aw(aw_timestamps)
    smDates, smValues           = dailysums.sm(sm_timestamps)
    wrfDates, wrfMax, wrfMin    = dailysums.wrf(wrf_timestamps)
    imdhistDates, imdhistValues = dailysums.imdhist(imdh)

    # Makes the prediction

    awErrorDates, awErrors         = calc.error(awDates, yobiDates, awValues, yobiValues)
    smErrorDates, smErrors         = calc.error(smDates, yobiDates, smValues, yobiValues)
    wrfMaxErrorDates, wrfMaxErrors = calc.error(wrfDates, yobiDates, wrfMax, yobiValues)
    wrfMinErrorDates, wrfMinErrors = calc.error(wrfDates, yobiDates, wrfMin, yobiValues)
    imdhErrorDates, imdhistErrors  = calc.error(imdhistDates, yobiDates, imdhistValues, yobiValues)

    step2 = time.time()
    # print "2: Making predictions... (%ss)" % (round((step2 - step1), 1))
    
    # predValues = []
    # predDates  = []

    # for i in range(0,smErrors["avgs"].__len__()):
    #     predDates.append(smDates[i])
    #     if (smValues[i] - smErrors["avgs"][i]) < 0:
    #         predValues.append(0)
    #     elif smValues[i-1] != 0 and smValues[i] < 7:
    #         predValues.append(0) 
    #     else: 
    #         predValues.append(smValues[i] - smErrors["avgs"][i])
    #     # print predDates[-1], ":", predValues[-1]

    # predErrorDates, predErrors   = calc.error(predDates, yobiDates, predValues, yobiValues)
    # step2 = time.time()
    print "3: Tracing Output... (%ss)" % (round((step2 - step1), 1))

    trace_data(yobiDates, yobiValues, "Yobi Rainfall", data)
    #trace_data(awErrorDates, awErrors["avgs"], "Avg AW Errors", data)
    trace_data(smErrorDates, smErrors["avgs"], "Avg SM Errors", data)
    trace_data(imdhErrorDates, imdhistErrors["avgs"], "Avg IMD Historical Errors", data)
    trace_data(wrfMaxErrorDates, wrfMaxErrors["avgs"], "Avg WRF Max Errors", data)
    trace_data(wrfMinErrorDates, wrfMinErrors["avgs"], "Avg WRF Min Errors", data)
    #trace_data(awErrorDates, awErrors["stds"], "Std AW Errors", data)
    trace_data(smErrorDates, smErrors["stds"], "Std SM Errors", data)
    trace_data(imdhErrorDates, imdhistErrors["stds"], "Std IMD Historical Errors", data)
    trace_data(wrfMaxErrorDates, wrfMaxErrors["stds"], "Std WRF Max Errors", data)
    trace_data(wrfMinErrorDates, wrfMinErrors["stds"], "Std WRF Min Errors", data)

    title = 'Forecast Accuracy for Rainfall'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#D0D0D0'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)
    return render_template('analytics.html')

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

@app.route('/power')
def powerView():
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    print "0: Initializing... (Power)"
    step0 = time.time()
    pipeline  = [
                { "$match": { "load": { "$exists": True } } },
                { "$group": { 
                    "_id": "$ts", 
                    "l"  : { "$last": "$load" },
                    "s"  : { "$last": "$schedule" },
                    } 
                },
                { "$sort" : SON([("_id", 1)]) }
                ]
    cursor = power.aggregate(pipeline, allowDiskUse = True)
    data   = [x for x in cursor]
    power_data = pd.DataFrame(list(data))
    step1 = time.time()
    print "1: Data Loaded... (%ss)" % (round((step1 - step0), 1))
    # data     = []
    # loads    = []
    # schedule = []
    # output   = []
    # schDiffs = []
    # times    = []
    # diffs    = []
    # for p in power_data:
    #     try:
    #         loads.append(p["load"])
    #         schedule.append(p["schedule"])
    #         times.append(p["ts"])
    #         try:
    #             output.append(p["drawl"]["Total (DTL) "])
    #         except:
    #             output.append(p["drawl"]["Total (DTL End)"])
    #         diffs.append(output[-1]/loads[-1])
    #         schDiffs.append(100 - float(p["schedule"])/float(p["load"])*100)
    #     except:
    #         continue
    

    yvars = [
                    {"val": power_data.l, "name": "Load (MW)"},
                    {"val": power_data.s, "name": "Schedule (MW)"},
                    {"val": ((power_data.l - power_data.s)/power_data.l*100).round(1), "name": "Undercapacity (%)"}
            ]
    
    data = []
    for yvar in yvars:
        if yvar:
            data.append(go.Scattergl(
                x = power_data["_id"],
                y = yvar["val"],
                name= yvar["name"],
                mode= 'lines'
            )
        )
        print "Tracing", yvar["name"]

    title = 'Power'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/transformers')
def transformersView():
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    print "0: Initializing... (Power)"
    step0 = time.time()
    pipeline  = [
                { "$match": { "load": { "$exists": False } } },
                { "$group": { 
                    "_id": "$ts", 
                    "l"  : { "$last": "$load" },
                    "s"  : { "$last": "$schedule" },
                    } 
                },
                { "$sort" : SON([("_id", 1)]) }
                ]
    cursor = power.aggregate(pipeline, allowDiskUse = True)
    data   = [x for x in cursor]
    power_data = pd.DataFrame(list(data))
    step1 = time.time()
    print "1: Data Loaded... (%ss)" % (round((step1 - step0), 1))
    # data     = []
    # loads    = []
    # schedule = []
    # output   = []
    # schDiffs = []
    # times    = []
    # diffs    = []
    # for p in power_data:
    #     try:
    #         loads.append(p["load"])
    #         schedule.append(p["schedule"])
    #         times.append(p["ts"])
    #         try:
    #             output.append(p["drawl"]["Total (DTL) "])
    #         except:
    #             output.append(p["drawl"]["Total (DTL End)"])
    #         diffs.append(output[-1]/loads[-1])
    #         schDiffs.append(100 - float(p["schedule"])/float(p["load"])*100)
    #     except:
    #         continue
    

    yvars = [
                    {"val": power_data.l, "name": "Load (MW)"},
                    {"val": power_data.s, "name": "Schedule (MW)"},
                    {"val": ((power_data.l - power_data.s)/power_data.l*100).round(1), "name": "Undercapacity (%)"}
            ]
    
    data = []
    for yvar in yvars:
        if yvar:
            data.append(go.Scattergl(
                x = power_data["_id"],
                y = yvar["val"],
                name= yvar["name"],
                mode= 'lines'
            )
        )
        print "Tracing", yvar["name"]

    title = 'Power'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/state-power/<state>')
def statePowerView(state):
    power_data = statePower.find({"loc": state}).sort('ts', pymongo.ASCENDING)
    data     = []
    loads    = []
    schedule = []
    actual   = []
    output   = []
    gen      = []
    diffs    = []
    times    = []
    for p in power_data:
        try:
            loads.append(p["demand"])
            schedule.append(p["schedulelDrawl"])
            actual.append(p["actualDrawl"])
            gen.append(p["gen"])
            output.append(p["gen"] + p["actualDrawl"])
            diffs.append((p["gen"] + p["actualDrawl"])/p["demand"])
            times.append(p["ts"])
        except:
            continue
    
    trace_data(times, loads, "Demand", data)   
    trace_data(times, schedule, "Schedule Drawl", data)   
    trace_data(times, actual, "Actual Drawl", data)   
    trace_data(times, gen, "State Generation", data)
    trace_data(times, output, "Output", data)   
    trace_data(times, diffs, "Capacity", data)   

    title = state+' Power'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/traffic/<orig>')
def trafficView(orig):
    traffic_data = list(traffic.find({"origin_addresses": orig}).sort('ts', pymongo.ASCENDING))
    data      = []
    traf_time = []
    time      = []
    times     = []
    for t in traffic_data:
        try:
            time.append(round(t["duration"]/60, 1))
            traf_time.append(round(t["duration_in_traffic"]/60, 1))
            times.append(t["ts"])
        except:
            continue

    peakTimes, peakLoads = dailysums.power(times, traf_time)

    df1 = pd.DataFrame(dict(ts = peakTimes, d = peakLoads)).reset_index(peakTimes)  
    df1["weekday"] = df1["ts"].apply(lambda x: x.weekday())
    print df1.groupby(df1["weekday"]).std(), df1.groupby(df1["weekday"]).mean(), df1.groupby(df1["weekday"]).std()/df1.groupby(df1["weekday"]).mean()
    
    trace_data(times, time, "Normal Time", data)   
    trace_data(times, traf_time, "Traffic Time", data)   
    trace_data(peakTimes, peakLoads, "Peaks Time", data)   

    title = 'Traffic'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/nyc-traffic/<loc>')
def nycTraffic(loc):
    traffic_data = pd.DataFrame(list(traffic.find({"destination_addresses": loc}).sort('ts', pymongo.ASCENDING)))
    # locs = [
    #         "230 Vesey St, New York, NY 10281, USA",
    #         "1855 1st Avenue, New York, NY 10128, USA",
    #         "490 Riverside Dr, New York, NY 10027, USA",
    #         "116th St & Broadway, New York, NY 10027, USA",
    #         "328 Malcolm X Blvd, New York, NY 10027, USA",
    #         "Hell's Kitchen, New York, NY, USA",
    #         "Water St, New York, NY, USA"]
    # pipeline = [
    #             { "$match": { "destination_addresses": {"$in": locs} } }
    #             ]
    # traffic_data = pd.DataFrame(list(traffic.aggregate(pipeline, allowDiskUse = True)))
    traffic_data["ts"] = np.array(traffic_data["ts"]) - np.timedelta64(9, 'h') - np.timedelta64(30,'m')
    traffic_data["duration"]            = traffic_data["duration"]/60
    traffic_data["duration_in_traffic"] = traffic_data["duration_in_traffic"]/60
    traffic_data.round(0)

    nyc = pd.DataFrame(list(davis.find({'name': 'apbitten3'}).sort('ts', pymongo.ASCENDING)))

    averaged = traffic_data.set_index('ts').groupby(pd.TimeGrouper('15T')).mean()
    nycaws   = nyc.set_index('time_stamp').groupby(pd.TimeGrouper('15T')).mean()
    averaged["ts"] = averaged.index
    nycaws["ts"]   = nycaws.index
    merged   = averaged.merge(nycaws, left_on="ts", right_on="ts")
    merged["ts"] = np.array(merged["ts"]) 

    times = merged.ts
    traf  = merged["duration_in_traffic"]
    rain  = [merged["r"].iloc[0]]
    for i in range(1, merged["r"].__len__()):
        r = (merged["r"][i] - merged["r"][i-1])/100
        if r > 0:
            rain.append((merged["r"][i] - merged["r"][i-1])/100)
        else:
            rain.append(0)
    merged["r"] = rain

    data     = []
    dates    = []
    values   = []
    rains    = []
    keys     = []
    dt       = times[0].date()
    trafdict = {}
    for i in range(0, times.__len__()):
        if times[i].date() == dt:
            rains.append(rain[i])
            values.append(traf[i])
            dates.append(times[i].time())
        else:
            key = str(dt).replace("-","")
            keys.append(key)
            trafdict[key] = {"traffic": values, "ts": dates, "rain": rains}
            rains  = [rain[i]]
            values = [traf[i]]
            dates  = [times[i].time()]
            dt  = times[i].date()

    for key in keys:
        trace_data(trafdict[key]["ts"], trafdict[key]["traffic"], key+" Traffic", data)    
        # trace_data(trafdict[key]["ts"], trafdict[key]["rain"], key+" Rain", data)

    trace_data(merged["ts"], merged["duration_in_traffic"], "Traffic", data)    

    title = 'Traffic '+loc

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/traffic-vol/<loc>')
def trafficVol(loc):
    step0 = time.time()
    print "Initializing traffic vol..."

    traffic_data = pd.DataFrame(list(traffic.find({"destination_addresses": loc}).sort('ts', pymongo.ASCENDING)))
    traffic_data["duration"]            = traffic_data["duration"]/60
    traffic_data["duration_in_traffic"] = traffic_data["duration_in_traffic"]/60
    traffic_data.round(0)

    step1a = time.time()
    print "1a: Pulled traffic data... (%ss)" % (round((step1a - step0), 1))

    nyc = pd.DataFrame(list(davis.find({'name': 'apbitten3'}).sort('ts', pymongo.ASCENDING)))

    step1b = time.time()
    print "1b: Pulled weather data... (%ss)" % (round((step1b - step1a), 1))

    averaged = traffic_data.set_index('ts').groupby(pd.TimeGrouper('15T')).mean()
    nycaws   = nyc.set_index('time_stamp').groupby(pd.TimeGrouper('15T')).mean()
    averaged["ts"] = averaged.index
    nycaws["ts"]   = nycaws.index
    df             = averaged.merge(nycaws, left_on="ts", right_on="ts")
    df["ts"]       = np.array(df["ts"])
    df["weekday"]  = df["ts"].apply(lambda x: x.weekday())
    rn    = [0]
    for i in range(1, df["r"].__len__()):
        r = (df["r"].iloc[i] - df["r"].iloc[i-1])/100
        if r > 0:
            rn.append(r)
        else:
            rn.append(0)

    df["r"] = calc.movingAvg(rn, 15)
    df["w"] = calc.movingAvg(df.w, 15)
    df["w"] = calc.movingAvg(df.ct, 15)
    df["p"] = calc.movingAvg(df.p, 15)
    days = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']

    stats = {}
    varts = {}
    for day in days:
        varts[day] = {}
        i = days.index(day)
        times = pd.DatetimeIndex(df[df['weekday'] == i].ts)
        varts[day]['a'] = df[df['weekday'] == i]
        varts[day]['m'] = df[df['weekday'] == i].groupby([times.hour,times.minute]).duration_in_traffic.mean()
        varts[day]['s'] = df[df['weekday'] == i].groupby([times.hour,times.minute]).duration_in_traffic.std()
        varts[day]['c'] = varts[day]['s']/varts[day]['m']

    stats = {}
    for day in days:
        stats[day] = {}
        i = days.index(day)
        times = pd.DatetimeIndex(df[df['weekday'] == i].ts)
        stats[day]['r'] = df[df['weekday'] == i].groupby([times.hour,times.minute]).duration_in_traffic.std().corr(df[df['weekday'] == i].groupby([times.hour,times.minute]).r.std()) 
        stats[day]['ct'] = df[df['weekday'] == i].groupby([times.hour,times.minute]).duration_in_traffic.std().corr(df[df['weekday'] == i].groupby([times.hour,times.minute]).ct.std()) 

    print stats["Mon"]
    print stats["Tues"]
    print stats["Wed"]
    print stats["Thurs"]
    print stats["Fri"]
    print stats["Sat"]
    print stats["Sun"]

    step2 = time.time()
    print "2: Sorted data... (%ss)" % (round((step2 - step1b), 1))

    data = []
    for day in days:
        trace_data(df.ts[36:36+96], varts[day]["m"], day+" Mean", data)    
        trace_data(df.ts[36:36+96], varts[day]["s"], day+" Std", data)    
        trace_data(df.ts[36:36+96], varts[day]["c"], day+" CoV", data)

    title = 'Traffic Vol: '+loc

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/davis')
def nycWeather():
    nyc = pd.DataFrame(list(davis.find().sort('ts', pymongo.ASCENDING)))
    nyc["time_stamp"] = np.array(nyc["time_stamp"]) - np.timedelta64(10, 'h') - np.timedelta64(30,'m')
    locs = nyc.groupby('name').first().index
    
    ws = {}
    for loc in locs:
        ws[loc] = nyc.loc[nyc['name'] == loc]
    
    data = []
    for loc in locs:
        rn    = [0]
        for i in range(1, ws[loc]["r"].__len__()):
            rn.append((ws[loc]["r"].iloc[i] - ws[loc]["r"].iloc[i-1])/100)
        trace_data(ws[loc]["time_stamp"], ws[loc]["ct"], loc+" Current Temp", data)
        trace_data(ws[loc]["time_stamp"], ws[loc]["ht"], loc+" High Temp", data)
        trace_data(ws[loc]["time_stamp"], ws[loc]["lt"], loc+" Low Temp", data)
        trace_data(ws[loc]["time_stamp"], ws[loc]["p"], loc+" Pressure", data)
        trace_data(ws[loc]["time_stamp"], ws[loc]["w"], loc+" Wind", data)
        trace_data(ws[loc]["time_stamp"], rn, loc+" Rain", data)
        trace_data(ws[loc]["time_stamp"], ws[loc]["h"], loc+" Humidity", data)

    title = 'NYC Weather'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    pct_dict = {}

    pct_dict["1"] = 1
    pct_dict["10"] = 10
    pct_dict["30"] = 30
    pct_dict["70"] = 70
    pct_dict["90"] = 90
    pct_dict["99"] = 10

    return render_template('percentiles.html.html', percentiles=pct_dict)

@app.route('/us-power/<ISO>')
def nycPower(ISO):
    step0 = time.time()
    print "0: Initializing power..."
    # California  : CISO
    # New York    : NYIS
    # Midwest     : MISO
    # Texas       : ERCO
    # Midatlantic : PJM
    # Southeast   : SOCO
    # Northeast   : ISNE
    # Tennessee   : TVA
    # Central     : SWPP
    # Florida     : FPL
    y = urllib2.urlopen('http://api.eia.gov/series/?api_key=7873e0dd0201856a83dea9763d031292&series_id=EBA.'+ISO+'-ALL.D.H')
    yobibyte = json.loads(y.read())
    demand = yobibyte["series"][0]["data"]
    demandTimes = []
    demands     = []
    for d in demand:
        demandTimes.append(datetime.strptime(d[0], '%Y%m%dT%HZ'))
        demands.append(d[1])
    step1a = time.time()
    print "1a: Loaded demand... (%ss)" % (round((step1a - step0), 1))
    y = urllib2.urlopen('http://api.eia.gov/series/?api_key=7873e0dd0201856a83dea9763d031292&series_id=EBA.'+ISO+'-ALL.DF.H')
    yobibyte = json.loads(y.read())
    dayAhead = yobibyte["series"][0]["data"]
    forecastTimes   = []
    forecasts       = []
    for d in dayAhead:
        forecastTimes.append(datetime.strptime(d[0], '%Y%m%dT%HZ'))
        forecasts.append(d[1])
    step1b = time.time()
    print "1b: Loaded forecasts... (%ss)" % (round((step1b - step1a), 1))
    # y = urllib2.urlopen('https://hourlypricing.comed.com/api?type=5minutefeed&datestart=201506031105&dateend='+datetime.strftime((datetime.now()-timedelta(days=1)).date(), '%Y%m%d')+'0000')
    # yobibyte = json.loads(y.read())
    # prices      = [1]
    # priceTimes  = []
    # vols        = []
    # for byte in yobibyte:
    #     try:
    #         vols.append((float(byte["price"])/float(prices[-1]) - 1)*100)
    #     except:
    #         vols.append(1)
    #     prices.append(byte["price"])
    #     priceTimes.append(datetime.fromtimestamp(float(byte['millisUTC'])/1000.0))
    # step1c = time.time()
    # print "1c: Loaded prices... (%ss)" % (round((step1c - step1b), 1))
    df1 = pd.DataFrame(dict(ts = demandTimes, d = demands)).reset_index(demandTimes)
    df2 = pd.DataFrame(dict(ts = forecastTimes, f = forecasts)).reset_index(forecastTimes)
    df3 = df1.merge(df2,how="left",left_on="ts",right_on="ts")
    return df3
    print df3
    print df3.head()
    #df3.to_csv('nyis.csv',sep=',')
    diffs = np.array(df3.d) - np.array(df3.f)
    pcts = np.divide(diffs,df3.d)*100

    step1 = time.time()
    print "1: Data loaded... (%ss)" % (round((step1 - step0), 1))

    data = []

    # print np.corrcoef(calc.normalize(load),calc.normalize(temps))
    # print np.corrcoef(load, temps)

    trace_data(demandTimes, demands, "Demand", data)   
    trace_data(forecastTimes, forecasts, "Forecast", data)
    trace_data(df3.ts, pcts, "Diffs", data)
    # trace_data(priceTimes, vols, "Volatilities", data)
    # trace_data(priceTimes, prices, "Price", data)
    # trace_data(df3.ts, calc.normalize(df3.d), "Demand normalized", data)
    # trace_data(df3.ts, calc.normalize(df3.f), "Forecasts normalized", data)

    title = ISO+' Power'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/price')
def prices():
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))
    print "0: Initializing... (Price)"
    step0 = time.time()

    pipeline  = [
                { "$group": { 
                    "_id": "$ts", 
                    "p"  : { "$last": "$price" },
                    } 
                },
                { "$sort" : SON([("_id", 1)]) }
                ]
    cursor = power_price.aggregate(pipeline, allowDiskUse = True)
    data   = [x for x in cursor]
    spot   = pd.DataFrame(list(data))

    dayAhead = pd.DataFrame(list(iex.find({}).sort('ts', pymongo.DESCENDING)))

    step1 = time.time()
    print "1: Data Loaded... (%ss)" % (round((step1 - step0), 1))

    data = []
    trace_data(spot["_id"], spot["p"], "DSM", data)
    trace_data(dayAhead["ts"], dayAhead["A1"]/1000, "A1 (IEX)", data)

    title = 'Pricing'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/iex')
def dayAhead():
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    prices = pd.DataFrame(list(iex.find({}).sort('ts', pymongo.DESCENDING)))

    data = []
    trace_data(prices["ts"], prices["A1"]/1000, "A1", data)

    title = 'Pricing'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('analytics.html')

@app.route('/power-forecast')
def powerForecast():
    if 'username' in session:
        if session['username'] != "gkumar09@gmail.com":
            if int(id) not in users.find({'username': session['username']})[0]['sensors']:
                return redirect(url_for('notAuthorized'))
    else:
        return redirect(url_for('notAuthorized'))

    step0 = time.time()
    print "0: Initializing power forecast... "

    power_data = power.find().sort('ts', pymongo.ASCENDING)

    step1 = time.time()
    print "1: Data loaded... (%ss)" % (round((step1 - step0), 1))

    data     = []
    loads    = []
    schedule = []
    output   = []
    schDiffs = []
    times    = []
    diffs    = []
    for p in power_data:
        try:
            loads.append(p["load"])
            schedule.append(p["schedule"])
            times.append(p["ts"])
            diffs.append(output[-1]/loads[-1])
            schDiffs.append(100 - float(p["schedule"])/float(p["load"])*100)
        except:
            continue

    step2 = time.time()
    print "2: Data sorted... (%ss)" % (round((step2 - step1), 1))

    today     = datetime.now().date()
    yesterday = datetime.now().date()-timedelta(days=1)

    df        = pd.DataFrame(dict(ts = times, d = loads))
    df.index  = df['ts']
    df1       = df['d']
    df        = df1.resample('15T').bfill()
    powerYest = df[yesterday:today]

    step3 = time.time()
    print "3: Plotting... (%ss)" % (round((step3 - step2), 1))


    times = []

    for i in range(0,96):
        times.append(datetime.combine(datetime.now().date(), datetime.min.time()) + timedelta(minutes=i*15))
    print times

    powerToday = []
    for i in range(0,96):
        powerToday.append(powerYest[i] + randint(-200,200))

    data = []
    trace_data(times, powerYest, "Yesterday", data)   
    trace_data(times, powerToday, "Today", data)   

    title = 'Delhi Power Forecast'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#000000'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.8)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('power-dash.html', today = today, yesterday = yesterday, powerYest = powerYest, powerToday = powerToday)

# https://enigmatic-caverns-27645.herokuapp.com/add_data/1=<'id':100,'t1':30,'t2':32,'h':50,'w':20,'r':0,'p':1,'s':3,'lt':25.571778,'ln':91.89559>

# set the secret key. keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
#mongodb password: 89aok03fqogpnuuqn8dlcc85s9

if __name__ == '__main__':
    app.run(debug=True)



##########################################

#http://mamenchisaurus-70930.herokuapp.com/

# @app.route('/r2p')
# def R2p():
#     cursors = []
#     analytics = []
    
#     for i in range(200, 221):
#         cursors.append(sensors.find({'id': int(i)}).sort('ts', pymongo.DESCENDING))

#     pcts = []
#     f = 1
#     for cursor in cursors:
#         ts = ""
#         count = 0
#         upload = 0
#         hang = 0
#         for document in cursor:
#             if ts == "":
#                 ts = document['ts']
#                 s_id = document['id']
#             else:
#                 fmt = '%H:%M:%S'
#                 diff = datetime.strptime(ts[11:], fmt) - datetime.strptime(document['ts'][11:], fmt)
#                 if diff < timedelta(minutes=(10*f)) and diff > timedelta(minutes=(f+.5)):
#                     count += math.floor(diff.total_seconds()/60)
#                     upload +=1
#                     # print str(count) + " | " + str(upload)
#                 elif diff > timedelta(minutes=(10*f+.5)):
#                     hang += 1
#                 else:
#                     upload += 1
#                 ts = document['ts']
#                 pct = 100 - round(100*count/float(upload), 2)
#     print pcts

#     return render_template('r2p.html', pcts = pcts)
