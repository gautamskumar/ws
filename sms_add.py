#!/usr/bin/env python
import time 
import datetime
from datetime import datetime,timedelta
import urllib
import urllib2

def SMSadd():
    timestamp = int(time.time())

    # print(timestamp)
    def getMessages(apikey, inboxID):
        params = {'apiKey':apikey, 'inbox_id' : inboxID,'min_time':timestamp-600,'max_time':timestamp }
        f = urllib2.urlopen('http://api.textlocal.in/get_messages/?'
            + urllib.urlencode(params))
        return (f.read(), f.code)
    resp, code = getMessages('mnpbat79E4I-h5eoJDsq1UHHiTJeAiqi3euEPsLdJl','10')
    # print (resp)
    reslist = str(resp).split('"')
    temp =[]
    for i in reslist:
        if 'HK9D7' in i:
            temp.append(i[6:])
    dates=[]
    for i in range(len(reslist)):
        if 'date' in reslist[i]:
            dates.append(reslist[i+2])

    # print temp
    # print dates 

    # temp = ["'id':6,'t1':30,'t2':32,'h':50,'w':20,'r':0,'p':1,'s':3,'lt':25.571778,'ln':91.89559"]
    msgs = []

    for i in temp:
        k = list(i)
        for j in range(len(k)):
            if(k[j]=="'"):
                k[j] = '"'
                # print(j)
            if(k[j])=='\\':
                k[j] = ''
        # msgs.append(str(''.join(k)+',"ts":'+"'"+dates[n]+"'"))
        msgs.append(''.join(k))
        
    print msgs 
    #inserting into enigmatic-caverns
    from pymongo import MongoClient
    import json    # or `import simplejson as json` if on Python < 2.6

    client = MongoClient('mongodb://heroku_bnjrx3s8:ra6mg5rivid9dm2r38u0nvr74g@ds019085-a0.mlab.com:19085,ds019085-a1.mlab.com:19085/heroku_bnjrx3s8?replicaSet=rs-ds019085')
    db = client.heroku_bnjrx3s8
    sensors = db.sensors
    n = 1
    # for every data:   
    for row in msgs:
        # print row 
        obj = json.loads('{' + row + '}')    # obj now contains a dict of the data
        # obj['ts'] = str(datetime.now() + timedelta(hours=5, minutes=30))[0:19]
        obj['ts'] = dates[n]
        n+=1
        print obj
        count = 0
        # check for timestamp redudancies
        if sensors.find({'id':obj['id'], 'ts':obj['ts']}).count() == 0:
                valDict = obj
                valDict.pop('', None)
                count += 1
                sensors.insert_one(valDict)
                print count

SMSadd()