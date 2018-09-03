from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import config

def yobi(sensor_uploads):
    # Adding up sensor rainfall for individual days:
    dates = []
    values = []
    try:
        curr_date = datetime.strptime(sensor_uploads[0]["_id"], '%Y-%m-%d %H:%M:%S')
    except:
        curr_date = sensor_uploads[0]["_id"]
    curr_date_rainfall = 0.0
    # for every data point
    for i in range(0, sensor_uploads.__len__()):
        # if the day is the same
        if isinstance(sensor_uploads[i]['_id'], basestring) == True:
            ts = datetime.strptime(sensor_uploads[i]['_id'], '%Y-%m-%d %H:%M:%S')
        else:
            ts = sensor_uploads[i]['_id']
        if ts.date() == curr_date.date():
            curr_date_rainfall += float(sensor_uploads[i]["r"][0])
        # if it's a new day:
        else:
            # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
            # Accounting for
            dates.append(curr_date)
            values.append(config.get_sensor_rain_calibration(curr_date_rainfall))
            curr_date_rainfall = float(sensor_uploads[i]["r"][0])
            try:
                curr_date = datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S')
            except:
                curr_date = sensor_uploads[i]["_id"]

    return dates, values

def yobiPro(sensor_uploads):
    # Adding up sensor rainfall for individual days:
    dates = []
    values = []
    uptime = []
    downtime =[]
    downtime_dates = []
    curr_date = datetime.strptime(sensor_uploads[0]["_id"], '%Y-%m-%d %H:%M:%S')
    curr_date_ = datetime.strptime(sensor_uploads[0]["_id"], '%Y-%m-%d %H:%M:%S')
    curr_date_rainfall = 0.0
    curr_date_uptime = timedelta(0,0)
    curr_date_downtime = timedelta(0,0)
    # for every data point
    for i in range(0, sensor_uploads.__len__()):     
            if datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S').date() == curr_date.date():  
                if len(sensor_uploads[i]["r"])!=0:                           
                    curr_date_rainfall += float(sensor_uploads[i]["r"][0])
                    if i>0:
                        if datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S').date() == datetime.strptime(sensor_uploads[i-1]["_id"], '%Y-%m-%d %H:%M:%S').date():
                            curr_date_uptime +=  datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S') - datetime.strptime(sensor_uploads[i-1]["_id"], '%Y-%m-%d %H:%M:%S')
                        else:
                            curr_date_uptime = timedelta(0,0)
                elif len(sensor_uploads[i]["r"])==0:   
                    if i>0:
                        #print datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S') 
                        if datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S').date() == datetime.strptime(sensor_uploads[i-1]["_id"], '%Y-%m-%d %H:%M:%S').date():
                            curr_date_downtime +=  datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S') - datetime.strptime(sensor_uploads[i-1]["_id"], '%Y-%m-%d %H:%M:%S')
                        else:
                            curr_date_downtime = timedelta(0,0)

            # if it's a new day:
            else: #if curr_date.date() > datetime(2016, 8, 16, 12, 0, 0).date():
                # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
                # Accounting for
                if len(sensor_uploads[i]["r"])!=0:
                    dates.append(curr_date.date())
                    values.append(config.get_sensor_rain_calibration(curr_date_rainfall))
                    uptime.append(curr_date_uptime)
                    downtime.append(curr_date_downtime)
                    curr_date_rainfall = float(sensor_uploads[i]["r"][0])
                    curr_date = datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S')
                    curr_date_uptime = timedelta(0,0)
                    curr_date_downtime = timedelta(0,0)
                else:
                    curr_date_downtime +=  datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S') - datetime.strptime(sensor_uploads[i-1]["_id"], '%Y-%m-%d %H:%M:%S')
                    
    return dates, values, uptime, downtime

def aw(aw_timestamps):
    # Adding up AW rainfall for morning / evening for an individual day:
    dates = []
    values =[]

    for i in range(0, aw_timestamps.__len__() / 2):
        dates.append(datetime.strptime(aw_timestamps[2 * i]['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))
        aw_rain = (float(aw_timestamps[2 * i]["rain"]) + float(aw_timestamps[2 * i + 1]["rain"]))
        values.append(aw_rain)

    return dates, values

def sm(sm_timestamps):
    # Adding up SM rainfall data:
    dates = []
    values = []

    curr_date = datetime.strptime(sm_timestamps[0]["timestamp"][0:10], '%Y-%m-%d')
    # for every data point
    curr_date_rainfall = []
    for i in range(0, sm_timestamps.__len__()):
        # if the day is the same
        if datetime.strptime(sm_timestamps[i]["timestamp"][0:10], '%Y-%m-%d').date() == curr_date.date():
            curr_date_rainfall.append(float(sm_timestamps[i]["rain"]))
        # if it's a new day:
        else:
            # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
            # Accounting for
            dates.append(curr_date)
            try:
                values.append(curr_date_rainfall[-1])
            except:
                values.append(0)
            curr_date_rainfall = float(sm_timestamps[i]["rain"])
            curr_date = datetime.strptime(sm_timestamps[i]["timestamp"][0:10], '%Y-%m-%d')
            curr_date_rainfall = []

    return dates, values

def wrf(wrf_timestamps):
    # Adding up WRF rainfall data:
    dates = []
    wrf_max = []
    wrf_min = []

    for timestamp in wrf_timestamps:
        dates.append(datetime.strptime(timestamp['date'], '%Y-%m-%d'))
        try:
            wrf_max.append(float(timestamp['rmax']))
        except:
            wrf_max.append(245)
        try:
            wrf_min.append(float(timestamp['rmin']))
        except:
            wrf_min.append(245)

    return dates, wrf_max, wrf_min

def imd(imd_timestamps):
    # Adding up IMD rainfall data:
    dates = []
    values = []
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
            dates.append(curr_date)
            values.append(curr_date_rainfall)
            curr_date = imd_timestamps[i]["ts"]

    return dates, values

def imdhist(timestamps):
    # Taking the average of IMD historical data
    dates = []
    values = []
    lats = []
    longs = []
    for timestamp in timestamps:
        if timestamp["_id"] != "":
            dates.append(timestamp['_id'])
            values.append(timestamp['val'])
            lats.append(timestamp['lat'])
            longs.append(timestamp['long'])

    #ts = pd.Series({"vals": values, "dates": dates, "lats": lats,"longs": longs })

    '''values = ts.groupby([ts.index.month, ts.index.day]).mean()
    vals = values.as_matrix()
    days = values.index.tolist()
    dates = []
    for day in days:

        # Getting around the leap year bug (strptime doesn't take 
        # leap years, unless you specific a year) by enforcing a 
        # year that has a leap year
        
        try:
            dates.append(datetime.strptime(str(day[0])+" "+str(day[1])+" 2016", '%m %d %Y'))
        except:
            continue'''

    return dates, values, lats, longs

def stddevs(timestamps):
    # Taking the average of IMD historical data
    dates = []
    values = []

    for timestamp in timestamps:
        if timestamp["_id"] != "":
            dates.append(timestamp['_id'])
            values.append(timestamp['val'])
    
    ts = pd.Series(values, dates)
    values = ts.groupby([ts.index.month, ts.index.day])
    #this is super shitty. there must be a mean method on a groupby object.
    vals = []
    stddev = []
    for value in values:
        if value[0] == (2, 29):
            continue
        else:
            for v in list(value)[1]:
                vals.append(v[0])
            stddev.append(np.std(vals))
    dates = []
    for value in values:
        if value[0] == (2, 29):
            continue
        else:
            dates.append(datetime.strptime(str(value[0][0])+" "+str(value[0][1])+" 2016", '%m %d %Y'))
    return dates, stddev

def imdhist_avg(timestamps):
    # Taking the average of IMD historical data
    dates = []
    values = []

    for timestamp in timestamps:
        if timestamp["_id"] != "":
            dates.append(timestamp['_id'])
            values.append(timestamp['val'])

    
    ts = pd.Series(values, dates)
    values = ts.groupby([ts.index.month, ts.index.day])
    print values
    vals = values.as_matrix()
    days = values.index.tolist()
    dates = []
    for day in days:
        # Getting around the leap year bug (strptime doesn't take 
        # leap years, unless you specific a year) by enforcing a 
        # year that has a leap year
        try:
            dates.append(datetime.strptime(str(day[0])+" "+str(day[1])+" 2016", '%m %d %Y'))
        except:
            continue
    for day in days:
        # Getting around the leap year bug (strptime doesn't take 
        # leap years, unless you specific a year) by enforcing a 
        # year that has a leap year
        try:
            dates.append(datetime.strptime(str(day[0])+" "+str(day[1])+" 2017", '%m %d %Y'))
        except:
            continue
    for val in vals:
        vals.append(val)
    
    return dates, vals



def imdhist_temp(timestamps):
    # Taking the average of IMD historical data
    dates = []
    values = []
    for timestamp in timestamps:
        if timestamp["_id"] != "":
            dates.append(timestamp['_id'])
            values.append(timestamp['val'][0])

    return dates, values

def yobi_temp(sensor_uploads):
    dates = []
    values = []
    curr_date = datetime.strptime(sensor_uploads[0]["_id"], '%Y-%m-%d %H:%M:%S')
    curr_date_temp = 0.0
    curr_temp_array = []
    # for every data point
    for i in range(0, sensor_uploads.__len__()):
        # if the day is the same
        if datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S').date() == curr_date.date():
            curr_temp_array.append(sensor_uploads[i]["t"][0])
            curr_date_temp = np.mean(curr_temp_array)
        # if it's a new day:
        else:
            # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
            # Accounting for
            dates.append(curr_date.date())
            values.append(float(curr_date_temp))
            curr_date_temp = 0.0
            curr_temp_array = []
            curr_date = datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S')

    return dates, values

def sm_temp(sensor_uploads):
    dates = []
    values = []
    curr_date = datetime.strptime(str(sensor_uploads[0]["timestamp"][0:19]), '%Y-%m-%d %H:%M:%S').date()
    #curr_date_temp = 0.0
    #curr_temp_array = []
    # for every data point
    for i in range(0, sensor_uploads.__len__()):
        if datetime.strptime(str(sensor_uploads[i]["timestamp"][0:19]), '%Y-%m-%d %H:%M:%S').date() != curr_date:
            dates.append(datetime.strptime(str(sensor_uploads[i]["timestamp"][0:19]), '%Y-%m-%d %H:%M:%S').date())
            values.append(int(sensor_uploads[i]['lowtemp']))
        curr_date = datetime.strptime(str(sensor_uploads[i]["timestamp"][0:19]), '%Y-%m-%d %H:%M:%S').date()

    return dates, values

def wrf_temp(sensor_uploads):
    dates = []
    values = []
    values_low = []
    for i in range(0, sensor_uploads.__len__()):
        dates.append(datetime.strptime(str(sensor_uploads[i]["date"]), '%Y-%m-%d').date())
        values.append(float(sensor_uploads[i]['tmax']))
        values_low.append(float(sensor_uploads[i]['tmin']))

    return dates, values, values_low 

def power(times, sensor_uploads):
    # Adding up sensor rainfall for individual days:
    dates  = []
    values = []
    curr_date = times[0]
    loads = []
    # for every data point
    for i in range(0, sensor_uploads.__len__()):
        # if the day is the same
        if times[i].date() == curr_date.date():
            loads.append(sensor_uploads[i])
        # if it's a new day:
        else:
            # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
            # Accounting for
            dates.append(curr_date.date())
            values.append(np.amax(loads))
            curr_date = times[i]
            loads = []
    print "std", np.std(values)
    print "avg", np.mean(values)
    print "vol", np.std(values)/np.mean(values)

    return dates, values

def min(times, sensor_uploads):
    # Adding up sensor rainfall for individual days:
    dates  = []
    values = []
    curr_date = times[0]
    loads = []
    # for every data point
    for i in range(0, sensor_uploads.__len__()):
        # if the day is the same
        if times[i].date() == curr_date.date():
            loads.append(sensor_uploads[i])
        # if it's a new day:
        else:
            # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
            # Accounting for
            dates.append(curr_date.date())
            values.append(np.amin(loads))
            curr_date = times[i]
            loads = []
    print "std", np.std(values)
    print "avg", np.mean(values)
    print "vol", np.std(values)/np.mean(values)

    return dates, values

def solar(sensor_uploads):
    # Adding up sensor rainfall for individual days:
    dates = []
    values = []
    try:
        curr_date = datetime.strptime(sensor_uploads[0]["_id"], '%Y-%m-%d %H:%M:%S')
    except:
        curr_date = sensor_uploads[0]["_id"]
    curr_date_rainfall = 0.0
    # for every data point
    for i in range(0, sensor_uploads.__len__()):
        # if the day is the same
        if isinstance(sensor_uploads[i]['_id'], basestring) == True:
            ts = datetime.strptime(sensor_uploads[i]['_id'], '%Y-%m-%d %H:%M:%S')
        else:
            ts = sensor_uploads[i]['_id']
        if ts.date() == curr_date.date():
            curr_date_rainfall += float(sensor_uploads[i]["s"][0])
        # if it's a new day:
        else:
            # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
            # Accounting for
            dates.append(curr_date)
            values.append(np.mean(curr_date_rainfall)*.2*9/5*24*365*.05*1000)
            curr_date_rainfall = float(sensor_uploads[i]["s"][0])
            try:
                curr_date = datetime.strptime(sensor_uploads[i]["_id"], '%Y-%m-%d %H:%M:%S')
            except:
                curr_date = sensor_uploads[i]["_id"]

    return dates, values