#!/usr/bin/python
# -*- coding: utf-8 -*-

import pymongo
import config
from datetime import datetime
from datetime import timedelta
import time
from bson.son import SON
import dailysums
import json
import urllib
import urllib2
import re

db        = config.get_db()
sensors   = db.sensors
ids       = db.ids
sm        = db.smnew
farmers   = db.farmers
forecasts = db.forecasts

testing = True

locs = ["gaya"]
ids  = [205]

# Pull yesterday and today's weather, to allow dailysums function to operate properly, as
# it needs two days to sum rainfall values for one day

yesterday = datetime.combine(datetime.now().date() - timedelta(days=1), datetime.min.time())
tomorrow  = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())
messes = ""
for i in range(0,ids.__len__()):

    id  = ids[i]
    loc = locs[i]

    sensors.create_index("id")
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
    sm0  = list(sm.find({'loc': loc, 'n_predict':0}).sort('timestamp', pymongo.DESCENDING).limit(1))
    sm1  = list(sm.find({'loc': loc, 'n_predict':1}).sort('timestamp', pymongo.DESCENDING).limit(1))

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

    today_max_temp = int(re.findall(r'\d+', sm0[0]['hightemp'])[0])
    today_min_temp = int(re.findall(r'\d+', sm0[0]['lowtemp'])[0])
    today_max_hum  = int(re.findall(r'\d+', sm0[0]['highhumidity'])[0])
    today_min_hum  = int(re.findall(r'\d+', sm0[0]['lowhumidity'])[0])
    today_rain     = int(re.findall(r'\d+', sm0[0]['rain'])[0])

    tom_max_temp   = int(re.findall(r'\d+', sm1[0]['hightemp'])[0])
    tom_min_temp   = int(re.findall(r'\d+', sm1[0]['lowtemp'])[0])
    tom_max_hum    = int(re.findall(r'\d+', sm1[0]['highhumidity'])[0])
    tom_min_hum    = int(re.findall(r'\d+', sm1[0]['lowhumidity'])[0])
    tom_rain       = int(re.findall(r'\d+', sm1[0]['rain'])[0])

    forecast = {
                    "id": id,
                    "today_max_temp": today_max_temp,
                    "today_min_temp": today_min_temp,
                    "today_max_hum" : today_max_hum,
                    "today_min_hum" : today_min_hum,
                    "today_rain"    : today_rain,
                    "tom_max_temp"  : tom_max_temp,
                    "tom_min_temp"  : tom_min_temp,
                    "tom_max_hum"   : tom_max_hum,
                    "tom_min_hum"   : tom_min_hum,
                    "tom_rain"      : tom_rain,
                }

    forecasts.insert_one(forecast)
    print forecast

    # nums = '+919654315871, +917011479828, +917506402645, +917982431043, +919631195456, +919934931659, +919635975077, +918459499599, +919810208119, +917982563362'
    contact  = farmers.find_one({"id": id})
    username = contact["username"]
    if testing == True:
        nums = "".join(str(n)+"," for n in contact["numbers"])+"+919654315871,+917011479828,+918459499599,+919810208119"
    else:
        nums = "".join(str(n)+"," for n in contact["numbers"])
    mes = (username+'\n').encode('utf-8')
    if contact["language"] == "Hi":
        if contact["days"]["tom"] == 1 and contact["days"]["yest"] == 1 and yestValues != False:
            mes += ('बिता कल\n')
        elif contact["days"]["yest"] == 1 and yestValues != False:
            mes += ('कल\n')
        if contact["inputs"]["temp"] == 1 and yestValues != False and contact["days"]["yest"] == 1:
            mes += ('गर्मी: '+str(yest_max_temp)+'C/'+str(yest_min_temp)+'C\n')
        if contact["inputs"]["hum"] == 1 and yestValues != False and contact["days"]["yest"] == 1:
            mes += ('नमी: '+str(yest_max_hum)+'% / '+str(yest_min_hum)+'%\n')
        if contact["inputs"]["rain"] == 1 and yestValues != False and contact["days"]["yest"] == 1:
            mes += ('बारिश: '+str(yest_rain)+'mm\n\n')
        if contact["days"]["tod"] == 1:
            mes += ('आज\n')
        if contact["inputs"]["temp"] == 1 and contact["days"]["tod"] == 1:
            mes += ('गर्मी: '+str(today_max_temp)+'C/'+str(today_min_temp)+'C\n')
        if contact["inputs"]["hum"] == 1 and contact["days"]["tod"] == 1:
            mes += ('नमी: '+str(today_max_hum)+'/'+str(today_min_hum)+'\n')
        if contact["inputs"]["rain"] == 1 and contact["days"]["tod"] == 1:
            mes += ('बारिश: '+str(today_rain)+'mm\n\n')
        if contact["days"]["tom"] == 1 and contact["days"]["yest"] == 1 and yestValues != False:
            mes += ('आने वाला कल\n')
        elif contact["days"]["tom"] == 1:
            mes += ('कल\n')
        if contact["inputs"]["temp"] == 1 and contact["days"]["tom"] == 1:
            mes += ('गर्मी: '+str(tom_max_temp)+'C/'+str(tom_min_temp)+'C\n')
        if contact["inputs"]["hum"] == 1 and contact["days"]["tom"] == 1:
            mes += ('नमी: '+str(tom_max_hum)+'/'+str(tom_min_hum)+'\n')
        if contact["inputs"]["rain"] == 1 and contact["days"]["tom"] == 1:
            mes += ('बारिश: '+str(tom_rain)+'mm')
    else:
        # if yestValues != False:
        #     mes += ('YESTERDAY\n')
        # if contact["inputs"]["temp"] == 1 and yestValues != False:
        #     mes += ('Temp: '+str(yest_max_temp)+'C/'+str(yest_min_temp)+'C\n')
        # if contact["inputs"]["hum"] == 1 and yestValues != False:
        #     mes += ('Hum: '+str(yest_max_hum)+'%/'+str(yest_min_hum)+'%\n')
        # if contact["inputs"]["rain"] == 1 and yestValues != False:
        #     mes += ('Rain: '+str(yest_rain)+'mm\n\n')
        # mes += ('TODAY\n')
        # if contact["inputs"]["temp"] == 1:
        #     mes += ('Temp: '+str(today_max_temp)+'C/'+str(today_min_temp)+'C\n')
        # if contact["inputs"]["hum"] == 1:
        #     mes += ('Hum: '+str(today_max_hum)+'/'+str(today_min_hum)+'\n')
        # if contact["inputs"]["rain"] == 1:
        #     mes += ('Rain: '+str(today_rain)+'mm\n\n')
        # mes += ('TOMORROW\n')
        # if contact["inputs"]["temp"] == 1:
        #     mes += ('Temp: '+str(tom_max_temp)+'C/'+str(tom_min_temp)+'C\n')
        # if contact["inputs"]["hum"] == 1:
        #     mes += ('Hum: '+str(tom_max_hum)+'/'+str(tom_min_hum)+'\n')
        # if contact["inputs"]["rain"] == 1:
        #     mes += ('Rain: '+str(tom_rain)+'mm')
        if yestValues != False:
            mes += ('YESTERDAY\n')
        if contact["inputs"]["temp"] == 1 and yestValues != False:
            mes += ('T: '+str(yest_max_temp)+'/'+str(yest_min_temp)+' | ')
        if contact["inputs"]["hum"] == 1 and yestValues != False:
            mes += ('H: '+str(yest_max_hum)+'/'+str(yest_min_hum)+' | ')
        if contact["inputs"]["rain"] == 1 and yestValues != False:
            mes += ('R: '+str(yest_rain)+'mm\n\n')
        mes += ('TODAY\n')
        if contact["inputs"]["temp"] == 1:
            mes += ('T: '+str(today_max_temp)+'/'+str(today_min_temp)+' | ')
        if contact["inputs"]["hum"] == 1:
            mes += ('H: '+str(today_max_hum)+'/'+str(today_min_hum)+' | ')
        if contact["inputs"]["rain"] == 1:
            mes += ('R: '+str(today_rain)+'mm\n\n')
        mes += ('TOMORROW\n')
        if contact["inputs"]["temp"] == 1:
            mes += ('T: '+str(tom_max_temp)+'/'+str(tom_min_temp)+' | ')
        if contact["inputs"]["hum"] == 1:
            mes += ('H: '+str(tom_max_hum)+'/'+str(tom_min_hum)+' | ')
        if contact["inputs"]["rain"] == 1:
            mes += ('R: '+str(tom_rain)+'mm')

    def sendSMS(apikey, numbers, message, unicode, schedule_time):
        params = {'apiKey':apikey, 'numbers': numbers, 'message' : message, 'sender':'TXTLCL', 'unicode': unicode, 'schedule_time': schedule_time}
        f = urllib2.urlopen('http://api.textlocal.in/send/?'
            + urllib.urlencode(params))
        return (f.read(), f.code)

    if testing == True:
        nums = "".join(str(n)+"," for n in contact["numbers"])+"+919654315871,+917011479828,+918459499599,+919810208119"
    else:
        nums = "".join(str(n)+"," for n in contact["numbers"])

    print nums
    print mes
    today           = datetime(datetime.now().year,datetime.now().month,datetime.now().day,9,15) - timedelta(hours = 5, minutes = 30)
    schedule_time   = time.mktime(today.timetuple())
    r, code         = sendSMS('mnpbat79E4I-h5eoJDsq1UHHiTJeAiqi3euEPsLdJl', nums, mes, 1, schedule_time)
    resp = json.loads(r)
    print resp
    try:
        responses = farmers.find_one({"id": id})["responses"]
    except:
        responses = []
    if resp["status"] == "success":
        responses.append({"ts": datetime.now(), "response": resp["batch_id"], "cost": resp["cost"], "num_messages": resp["num_messages"]})
        try:
            inDND = resp["inDND"]
        except:
            inDND = []
        if testing == True:
            cost = resp["cost"]-4*(resp["cost"]/resp["num_messages"])
            print cost
        else:
            cost = resp["cost"]
    else:
        inDND = []
        cost = 0

    farmers.update({
          'id': id
        },{
          '$set': {
            'responses': responses,
            'inDND': inDND,
          },
          '$inc': {
            'credits': -cost
          }
        }, upsert=False, multi=False)