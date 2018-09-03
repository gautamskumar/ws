from __future__ import division
import datetime
from ctypes._endian import _other_endian
import pandas as pd
import numpy as np
import math
import decimal

from datetime import datetime, timedelta, time
import time

import pymongo
from numpy.random.mtrand import weibull
from pymongo import MongoClient
from bson.son import SON

import config
import calc
import dailysums

def normalize(list):
    array = []
    for l in list:
    	array.append((l-np.mean(list))/np.mean(list))
    return array

def get_prediction(dates, other_dates, other_vals):
    vals = []

    for i in range(0, len(dates)):
        if dates[i] in other_dates:
            j = other_dates.index(dates[i])
            vals.append(other_vals[j])

    return vals


def getData(sensorDates, otherDates, sensorArray, weatherArray):
    try:
        sensorValues = []
        weatherDates = []
        dates = []
        firmValues = []

    #weatherdates < sensordates
        for date in otherDates:
            weatherDates.append(date.date())
        print weatherDates
        for i in range(0, sensorDates.__len__()):
            if sensorDates[i].date() in weatherDates:
                j = weatherDates.index(sensorDates[i].date())
                dates.append(sensorDates[i].date())
                firmValues.append(weatherArray[j])
                sensorValues.append(sensorArray[i])
    except:
        pass

    return dates, sensorValues, firmValues


def error(sensorDates, sensorArray, weatherArray):
    errors = []

    for i in range(0,sensorDates.__len__()):
        errors.append(float(weatherArray[i]) - sensorArray[i])
    return errors


def weights(errors):

    wts = []
    for i in range(0,errors.__len__()):
        if errors[i]!=0:
            w = 1 / float(((errors[i])*(errors[i])))
        else:
            w = 1
        wts.append(w)

    M = max(wts)
    m = min(wts)
    weights = []
    for i in range(0, wts.__len__()):
        if wts[i] != 1:
            x = float(wts[i] - m)/float(M-m)
        else:
            x = 1
        weights.append(x*100)
    return weights


def other_wrt_sensor(data):
    #when sensors are ZERO
    dates = []
    sensorVals = []
    otherVals = []

    for i in range(0,data.shape[0]):
        if data.YobiValues[i]==0 :
            dates.append(data.Dates[i])
            sensorVals.append(data.YobiValues[i])
            otherVals.append(data.otherValue[i])

    return dates, sensorVals, otherVals


def sensor_wrt_other(data):
    # when sensors are ZERO
    dates = []
    sensorVals = []
    otherVals = []

    for i in range(0, data.shape[0]):
        if data.otherValue[i] == 0:
            dates.append(data.Dates[i])
            sensorVals.append(data.YobiValues[i])
            otherVals.append(data.otherValue[i])

    return dates, sensorVals, otherVals


def calc_freq(vals):
    n = max(vals)

    freq = [0]*(n+1)
    for i in range(0,vals.__len__()):
        j = vals[i]
        freq[j] = freq[j] + 1

    frequency = []
    values = []
    for i in range(0,freq.__len__()):
        if freq[i]!=0:
            frequency.append(freq[i])
            values.append(i)

    return values, frequency


def classify(yobivals, othervals):
    rain1 = [] #does not rain
    rain0 = [] #rains
    yobi1 =[]
    yobi0 = []
    X = []
    Y = []

    for i in range(0,yobivals.__len__()):
        if yobivals[i]<=0.4: #if it does not rain
            rain1.append(othervals[i])
            yobi1.append(yobivals[i])

        else: #if it rains
            rain0.append(othervals[i])
            yobi0.append(yobivals[i])

    for i in range(0, rain1.__len__()):
        X.append(rain1[i])
        Y.append(1) #does not rain

    for i in range(0, rain0.__len__()):
        X.append(rain0[i])
        Y.append(0) #rains

    '''rains = pd.DataFrame({"rain0":rain0, "yobi":yobi0})
    rainsno = pd.DataFrame({"rain1": rain1, "yobi": yobi1})'''
    return X, Y


def error_percent(dates, sensorvals, othervals):
    errors = []
    yobivals = []
    ovals = []
    d = []
    for i in range(0,sensorvals.__len__()):
        #if sensorvals[i]!=0:
            #if sensorvals[i]<1: print str(sensorvals[i]), ",  ", str(othervals[i])
        if sensorvals[i]>=1 & abs(sensorvals[i] - othervals[i])>25 :
            x = (float((othervals[i]-sensorvals[i])/sensorvals[i]))*100
            #if x<2000:
            errors.append(x)
            yobivals.append(sensorvals[i])
            ovals.append(othervals[i])
            d.append(dates[i])

    return d, errors#, yobivals, ovals


def removeOutliers(dates, yobivals, othervals):
    yobi = []
    ovals = []
    d = []
    '''for i in range(0, yobivals.__len__()):
        if abs(yobivals[i]-othervals[i])<=15.0:
            yobi.append(yobivals[i])
            ovals.append(othervals[i])
            d.append(dates[i])'''

    for i in range(0, yobivals.__len__()):
        if yobivals[i]>=1.0 and abs(yobivals[i] - othervals[i])>35.0:
            err_p = (float((othervals[i] - yobivals[i]) / yobivals[i])) * 100
            if err_p<3000:
                yobi.append(yobivals[i])
                ovals.append(othervals[i])
                d.append(dates[i])
        else:
            err_abs = abs(yobivals[i] - othervals[i])
            if err_abs<=35.0:
                yobi.append(yobivals[i])
                ovals.append(othervals[i])
                d.append(dates[i])

    return d, yobi, ovals


def combine(dates1, dates2, vals1, vals2, yobi1, yobi2):
    len1 = len(dates1)
    len2 = len(dates2)
    dates_output = []
    vals = []
    yobivals = []

    if len1>len2:
        for i in range(0,len(dates2)):
            if dates2[i] in dates1:
                j = dates1.index(dates2[i])
                dates_output.append(dates2[i])
                x = math.sqrt( ((vals1[j])*(vals1[j])) + ((vals2[i])*(vals2[i])) )
                yobivals.append(yobi2[i])
                vals.append(x)
    else:
        for i in range(0,len(dates1)):
            if dates1[i] in dates2:
                j = dates2.index(dates1[i])
                dates_output.append(dates1[i])
                x = math.sqrt( ((vals2[j])*(vals2[j])) + ((vals1[i])*(vals1[i])) )
                yobivals.append(yobi1[i])
                vals.append(x)

    return dates_output, vals, yobivals


def wrfCombined(wrfMax, wrfMin, sensorVals, dates):
    wrf = []
    for i in range(0, len(wrfMax)):
        x = math.sqrt(((wrfMax[i]) * (wrfMax[i])) + ((wrfMin[i]) * (wrfMin[i])))
        wrf.append(x)

    '''error_max = error(dates, sensorVals, wrfMax)
    error_min = error(dates, sensorVals, wrfMin)
    wts_max = 100*weights(error_max)
    wts_min = 100*weights(error_min)
    

    for i in range(0, sensorVals.__len__()):
        #if wts_min[i]==0: print str(wts_min[i]), ", ", str(i)," max"
        #if wts_max[i] == 0: print str(wts_max[i]),", ", str(i)," min"
        x = float(wts_max[i]*wrfMax[i] + wts_min[i]*wrfMin[i])/float(wts_max[i] + wts_min[i])
        wrf.append(x)
'''
    return wrf


def freq_dist(sensorvals, othervals, dates, n):
    vals1=[]
    dates1=[]
    for i in range(0, len(othervals)):
        if othervals[i] == n:
            vals1.append(sensorvals[i])
            dates1.append(dates[i])

    return vals1


def calc_probab(sensorvals, vals):
    prob = []
    v = []
    temp_sensorvals = []
    temp_vals = []
    while len(vals)!=0:
        predicted_val = vals[0]
        v.append(predicted_val)
        print "predicted value:", str(predicted_val)
        x=0 #no. of times same value is predicted
        r0=0 #no. of times no rain
        r1=0 #no. of times rains
        for i in range(0,len(vals)):
            if vals[i]== predicted_val:
                x = x+1 #number of times the same value is predicted
                if sensorvals[i]==0: r0 = r0 + 1 #no. of times no rain
                else: r1 = r1 + 1 #no.of times rain
            #print "x: ",str(x),",   r0: ",str(r0),",   r1: ",str(r1)
        p = r0/x
        prob.append(p)

        for i in range(0,len(vals)):
            if vals[i] != predicted_val:
                temp_sensorvals.append(sensorvals[i])
                temp_vals.append(vals[i])

        del vals[:]
        del sensorvals[:]

        for i in range(0, len(temp_vals)):
            vals.append(temp_vals[i])
            sensorvals.append(temp_sensorvals[i])

        del temp_sensorvals[:]
        del temp_vals[:]

    return  prob, v


def RMSE(y, y_predict):
    y = np.asarray(y)
    y_predict = np.asarray(y_predict)
    return np.sqrt(((y_predict - y)**2).mean())


def get_imdh_data(lat, long, n, variable):
    #get list of lat longs
    start_lat = lat - 0.25*n
    end_lat = lat + 0.25*n
    start_long = long - 0.25 * n
    end_long = long + 0.25 * n
    a1_lat = np.arange(start_lat, lat, 0.25)
    a2_lat = np.arange(lat, (end_lat+0.25), 0.25)
    a1_long = np.arange(start_long, long, 0.25)
    a2_long = np.arange(long, (end_long + 0.25), 0.25)
    lats = list(a1_lat) + list(a2_lat)
    longs = list(a1_long) + list(a2_long)

    ''' start_lat = lat - 1 * n
    end_lat = lat + 1 * n
    start_long = long - 1 * n
    end_long = long + 1 * n
    a1_lat = np.arange(start_lat, lat, 1)
    a2_lat = np.arange(lat, (end_lat + 1), 1)
    a1_long = np.arange(start_long, long, 1)
    a2_long = np.arange(long, (end_long + 1), 1)
    lats = list(a1_lat) + list(a2_lat)
    longs = list(a1_long) + list(a2_long) '''

    # extract data from database online
    db = config.get_db()
    imdhist = db.imdhist
    imdhist.create_index("lt")
    # 25.0,25.25,25.5,25.75,26.00  92.0,92.25,92.5,92.75,93.0
    pipeline = [
        {"$match": {"id": variable, "lt": {"$in": lats }, "ln": {"$in": longs }}},
        {"$group": {"_id": "$ts", "val": {"$push": "$val"}, "lat": {"$push": "$lt"}, "long": {"$push": "$ln"} }},
        {"$sort": SON([("_id", 1)])}
    ]

    imdh = list(imdhist.aggregate(pipeline, allowDiskUse=True))

    '''
    pipeline_temp = [
        {"$match": {"id": "t", "lt": {"$in": lats}, "ln": {"$in": longs}}},
        {"$group": {"_id": "$ts", "val": {"$push": "$val"}, "lat": {"$push": "$lt"}, "long": {"$push": "$ln"}}},
        {"$sort": SON([("_id", 1)])}
    ]

    imdh_temp = list(imdhist.aggregate(pipeline_temp, allowDiskUse=True))'''

    return imdh


def get_location_num_index(lt, ln, lat, long):
    n = 0
    for i in range(0,len(lat)):
        if lat[i]==lt and long[i]==ln:
            n = i

    return n

def get_total_locs(lat):
    total_locs = len(lat[0])
    for i in range(1,len(lat)):
        if len(lat[i])>total_locs:
            total_locs = len(lat[i])
            print str(len(lat[i])), ", ", str(i)

    return total_locs


def calc_uptime(id, ids, sensors, d):
    #### first chunk to get meta data on the weather station
    dates = []
    for i in range(0, d.__len__()):
        dates.append(datetime.strptime(d[i], "%Y-%m-%d"))


    step0 = time.time()
    ids.create_index("id")
    sensors.create_index("ts")
    sensor = ids.find_one({'id': int(id)})
    step1 = time.time()
    print "Uptime: 1: Data Loaded... (%ss)" % (round((step1 - step0), 1))
    name         = sensor["name"]    
    lat          = sensor["lt"]
    lon          = sensor["ln"]
    mob_no       = sensor["ph"]
    carrier      = sensor["carrier"]
    f            = int(sensor["freq"])

    #### second chunk to actually calculate the uptime 
    misses=0
    hangs=0
    attempts=0
    uploads=0
    htimes=[]
    hvals=[]
    for i in range(0, dates.__len__()):
        if i > 0:
            diff = dates[i] - dates[i-1]
            # Misses
            if diff < timedelta(minutes=(10*f+1)) and diff > timedelta(minutes=(f+1)):
                misses   += round(diff.total_seconds()/(60*f),0) - 1
                attempts += round(diff.total_seconds()/(60*f),0)
                uploads  += 1
                mtimes.append(dates[i])
                mvals.append(misses)
            # Hangs
            elif diff > timedelta(minutes=(10*f+.5)):
                hangs    += 1
                attempts += 1
                uploads  += 1
                htimes.append(dates[i])
                hvals.append(hangs)
            # Uploads
            else:
                attempts += 1
                uploads  += 1
    
    in_field  = dates[-1] - dates[0]
    pct       = round(100*uploads/attempts, 2)
    uptime    = round(100*uploads/(in_field.total_seconds()/(60*f)), 2)
    analytics = {"id": id, "name": name, "last_update": dates[-1], "uptime": uptime, 
                "infield_days": in_field.days, "pct": pct, "attempts": format(int(attempts), ","), 
                "uploads": format(uploads, ","), "misses": format(int(misses), ","), "hangs": hangs, 
                "htimes": htimes, "lt": lat, "ln": lon, "mob_no": mob_no, "carrier": carrier, 
                "freq": str(f)}

    return analytics

def error(sensorDates, otherDates, sensorArray, weatherArray):
    try: 
        sumValues = []
        sensorValues = []
        weatherDates = []
        dates = []
        diffs = []
        stds = []
        avgs = []
        for date in otherDates:
            weatherDates.append(date.date())
        for i in range(0, sensorDates.__len__()):
            if sensorDates[i].date() in weatherDates:
                j = weatherDates.index(sensorDates[i].date())
                dates.append(sensorDates[i].date())
                diffs.append(float(weatherArray[j]) - sensorArray[i])
                stds.append(np.std(diffs))
                avgs.append(np.mean(diffs))
    except:
        pass

    values = {'errors':diffs,'avgs':avgs,'stds':stds}
    return dates, values

def imdSort(t, forecast, obs):
    if forecast == 0:
        t["vals"][0] +=1
    elif forecast <= 10:
        t["vals"][1] += 1
    elif 10 < forecast <= 25:
        t["vals"][2] += 1
    elif 25 < forecast <= 50:
        t["vals"][3] += 1
    elif 50 < forecast <= 100:
        t["vals"][4] += 1
    elif 100 < forecast:
        t["vals"][5] += 1
    error = forecast - obs
    t["errors"].append(error)

def imdError(sensorDates, otherDates, sensorArray, weatherArray):
    try: 
        sumValues = []
        sensorValues = []
        weatherDates = []
        for date in otherDates:
            weatherDates.append(date.date())
        for i in range(0, sensorDates.__len__()):
            if sensorDates[i].date() in weatherDates:
                ## this is only getting the last index value -- not the average of them
                j = weatherDates.index(sensorDates[i].date())
                ##
                sumValues.append(int(weatherArray[j]))
                sensorValues.append(sensorArray[i])
    except:
        pass

    diffs = np.array(sumValues) - np.array(sensorValues)

    comp = {
        "0": {
            "vals": [0,0,0,0,0,0],
            "errors": []
            },
        "1to10": {
            "vals": [0,0,0,0,0,0],
            "errors": []
            },
        "11to25": {
            "vals": [0,0,0,0,0,0],
            "errors": []
            },
        "26to50": {
            "vals": [0,0,0,0,0,0],
            "errors": []
            },
        "51to100": {
            "vals": [0,0,0,0,0,0],
            "errors": []
            },
        "gt100": {
            "vals": [0,0,0,0,0,0],
            "errors": []
            }
        }

    for i in range(0, sumValues.__len__()):
        if sensorValues[i] == 0:
            entry = comp["0"]
            imdSort(entry, sumValues[i], sensorValues[i])
        if 0 < sensorValues[i] <= 10:
            entry = comp["1to10"]
            imdSort(entry, sumValues[i], sensorValues[i])
        if 10 < sensorValues[i] <= 25:
            entry = comp["11to25"]
            imdSort(entry, sumValues[i], sensorValues[i])
        if 25 < sensorValues[i] <= 50:
            entry = comp["26to50"]
            imdSort(entry, sumValues[i], sensorValues[i])
        if 50 < sensorValues[i] <= 100:
            entry = comp["51to100"]
            imdSort(entry, sumValues[i], sensorValues[i])
        if 100 < sensorValues[i]:
            entry = comp["gt100"]
            imdSort(entry, sumValues[i], sensorValues[i])

    return [diffs, comp]

def imdMetrics(comp):
    a = comp['0']['vals'][0]
    A = sum(comp['0']['vals'])

    h = comp['1to10']['vals'][1]
    B = sum(comp['1to10']['vals'])

    o = comp['11to25']['vals'][2]
    C = sum(comp['11to25']['vals'])

    v = comp['26to50']['vals'][3]
    D = sum(comp['26to50']['vals'])

    ac = comp['51to100']['vals'][4]
    E = sum(comp['51to100']['vals'])

    aj = comp['gt100']['vals'][5]
    F = sum(comp['gt100']['vals'])

    G = comp['0']['vals'][0] + comp['1to10']['vals'][0] + comp['11to25']['vals'][0] + comp['26to50']['vals'][0] + comp['51to100']['vals'][0] + comp['gt100']['vals'][0]

    H = comp['0']['vals'][1] + comp['1to10']['vals'][1] + comp['11to25']['vals'][1] + comp['26to50']['vals'][1] + comp['51to100']['vals'][1] + comp['gt100']['vals'][1]

    I = comp['0']['vals'][2] + comp['1to10']['vals'][2] + comp['11to25']['vals'][2] + comp['26to50']['vals'][2] + comp['51to100']['vals'][2] + comp['gt100']['vals'][2]

    J = comp['0']['vals'][3] + comp['1to10']['vals'][3] + comp['11to25']['vals'][3] + comp['26to50']['vals'][3] + comp['51to100']['vals'][3] + comp['gt100']['vals'][3]

    K = comp['0']['vals'][4] + comp['1to10']['vals'][4] + comp['11to25']['vals'][4] + comp['26to50']['vals'][4] + comp['51to100']['vals'][4] + comp['gt100']['vals'][4]

    L = comp['0']['vals'][5] + comp['1to10']['vals'][5] + comp['11to25']['vals'][5] + comp['26to50']['vals'][5] + comp['51to100']['vals'][5] + comp['gt100']['vals'][5]

    T = G + H + I + J + K + L

    print "a: ", a, "h: ", h, "o: ", o, "v: ", v, "ac: ", ac, "aj: ", aj, "T: ", T, "A: ", A, "G: ", G, "B: ", B, "H: ", H, "C: ", C, "I: ", I, "D: ", D, "J: ", J, "E: ", E, "K: ", K, "F: ", F, "L: ", L
    try:
    	PC = (float((a+h+o+v+ac+aj))/float(T))*100
    except:
    	PC = "Error"
    try:
    	HSS_num = (float((a+h+o+v+ac+aj))-float((A*G+B*H+C*I+D*J+E*K+F*L)))/float(T)
    	HSS_den = (float(T)-float((A*G+B*H+C*I+D*J+E*K+F*L)))/float(T)
    	HSS = HSS_num/HSS_den
    except:
    	HSS = "Error"
    
    print PC
    print HSS

    return {"PC": PC, "HSS": HSS}

def findLocation(coords):
        imd_coords = []
        for coord in coords:
            int = round(coord*2)
            if int % 2 == 1:
                int = float(int/2)
                imd_coords.append(int)
            else:
                int = float((int + 1)/2)
                imd_coords.append(int)
        return imd_coords

def find25Locations(coords):
        imd_coords = []
        for coord in coords:
            int = round(coord*4)/4
            imd_coords.append(int)
        return imd_coords

def movingAvg(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

# aw_errors = imdError(dates, aw_dates, sum_rainfall, aw_rainfall)
# print aw_errors[0]
# print aw_errors[1]