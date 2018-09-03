from __future__ import  division
import numpy as np

import sklearn.linear_model as sp
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn import preprocessing
import sklearn.ensemble as en
from sklearn.metrics import mean_squared_error
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import SVR

from keras.models import Sequential
from keras import initializers, losses, metrics, optimizers
from keras.layers import Dense, Dropout, Activation, advanced_activations, Recurrent, LSTM
from keras.utils.np_utils import to_categorical
from keras.wrappers.scikit_learn import KerasRegressor

import numpy as np
import pandas as pd
import datetime
import math
import scipy.stats as stats

import comparison_funcs
import config
import dailysums
import weather_prediction

import pymongo
from numpy.random.mtrand import weibull
from pymongo import MongoClient
from bson.son import SON

from datetime import datetime, timedelta
import time

# from neupy import algorithms, layers, environment, estimators, plots


def linear(X,Y,x,y):
    reg = sp.LinearRegression(fit_intercept=True)
    reg.fit(X, Y)
    y_predict = reg.predict(x).flatten()
    rmse = RMSE(y=y, y_predict=y_predict)
    print "rmse: ", str(rmse)
    return y_predict

def linear_ridge(X,Y,x,y):
    reg = sp.RidgeCV(alphas=[0.001,0.01,0.1,1,10], fit_intercept=True, cv=10,gcv_mode='auto')
    reg.fit(X, Y)
    y_predict = reg.predict(x)
    rmse = RMSE(y=y, y_predict=y_predict)
    print "rmse: ", str(rmse)
    return y_predict

def svr_linear(X,Y,x,y):
    reg = GridSearchCV(SVR(kernel='linear'), cv=10,param_grid={"C":[1e0, 1e1, 1e2, 1e3], "degree":[1,2,3,4]})
    reg.fit(X, Y)
    y_predict = reg.predict(x)
    rmse = RMSE(y=y, y_predict=y_predict)
    print "rmse: ", str(rmse)
    return rmse, y_predict

def kernel_ridge_linear(X,Y,x,y):
    reg = GridSearchCV(KernelRidge(kernel='linear'), cv=10,param_grid={"alpha": [1e0,0.1,1e-2,1e-3],"degree":[1,2,3,4] })
    reg.fit(X, Y)
    y_predict = reg.predict(x)
    rmse = RMSE(y=y, y_predict=y_predict)
    print "rmse: ", str(rmse)
    return y_predict

def DT(X,Y,x,y):
    #reg = DecisionTreeRegressor(max_depth=5)
    reg = GridSearchCV(DecisionTreeRegressor(), cv=10,param_grid={"max_depth":[4,5,6,7,8,9,10]})
    reg.fit(X, Y)
    y_predict = reg.predict(x)
    y_predict = abs(y_predict)
    #parameters = reg.get_params()
    #print parameters
    rmse = RMSE(y=y,y_predict=y_predict)
    print "rmse: ",str(rmse)
    return y_predict

def BDT(X,Y,x,y):
    #r = GridSearchCV(DecisionTreeRegressor(), cv=10, param_grid={"max_depth": [ 5, 6, 7, 8, 9, 10, 15, 20]})
    reg = GridSearchCV(en.AdaBoostRegressor(base_estimator=DecisionTreeRegressor()), cv=10, param_grid={"n_estimators":[100],"learning_rate":[0.01],"loss":['exponential']})
    #reg = en.AdaBoostRegressor(base_estimator=r, n_estimators=50, learning_rate=0.01, loss='exponential')
    reg.fit(X, Y)
    y_predict = reg.predict(x)
    y_predict = abs(y_predict)
    rmse = RMSE(y=y, y_predict=y_predict)
    print "rmse: ", str(rmse)
    return y_predict



def rft(X,Y,x,y=None):
    #r = GridSearchCV(DecisionTreeRegressor(), cv=10, param_grid={"max_depth": [4, 5, 6, 7, 8, 9, 10]})
    #reg = GridSearchCV(en.AdaBoostRegressor(base_estimator=r), cv=5,param_grid={"n_estimators":[10,20,50,70,100],"learning_rate":[0.01,0.1,1,10],"loss":['linear','square','exponential']})
	if y==None:
		reg = en.RandomForestRegressor(n_estimators=100)
		reg.fit(X, Y)
		err_down, err_up = pred_ints(reg, x, percentile=90)
		y_predict = reg.predict(x)
		return err_down, err_up, y_predict
	else:
	    reg = en.RandomForestRegressor(n_estimators=100)
	    reg.fit(X, Y)
	    err_down, err_up = pred_ints(reg, x, percentile=90)
	    truth = y
	    correct = 0.
	    for i, val in enumerate(truth):
	    	if err_down[i] <= val <= err_up[i]:
	    		correct += 1
	    				
	   	#print "observations falling in the prediction interval: ", str(correct/len(truth))
	    y_predict = reg.predict(x)
	    rmse = RMSE(y=y, y_predict=y_predict)
	    print "rmse: ", str(rmse)
	    return err_down, err_up, y_predict


def nn_model(X,Y,x,y):
    hidden1_num_units = 150
    hidden2_num_units = 50
    hidden3_num_units = 15
    #hidden4_num_units = 50
    in_dim = X.shape[1]
    print "input dimension: ", str(in_dim)
    step0 = time.time()
    model = Sequential()
    model.add(Dense(hidden1_num_units, input_dim=in_dim, activation='relu'))
    model.add(Dropout(0.6))
    model.add(Dense(hidden2_num_units, input_dim=hidden1_num_units, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(hidden3_num_units, input_dim=hidden2_num_units, activation='relu'))
    model.add(Dropout(0.4))
    model.add(Dense(1,input_dim=hidden3_num_units, activation='linear'))
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
    #model = KerasRegressor(build_fn=model, epochs=20, batch_size=200)
    #reg = en.AdaBoostRegressor(base_estimator = model)
    step1 = time.time()
    print "3a: Model built(%ss)" % (round((step1 - step0), 1))


    model.fit(x=X, y=Y, epochs=15, validation_split=0.1, batch_size=100)
    #reg.fit(X,Y)
    step2 = time.time()
    print "3b: Model trained (%ss)" % (round((step2 - step1), 1))

    y_predict = model.predict(x)
    #y_predict = reg.predict(x)
    step3 = time.time()
    print "3b: Predictions made (%ss)" % (round((step3 - step2), 1))

    rmse = calcnew.RMSE(y=y, y_predict=y_predict)
    print "rmse: ", str(rmse)
    fig, ax = plt.subplots()
    ax.scatter(y, y_predict)
    ax.plot([y.max(), y.min()], [y.max(), y.min()], 'r--')
    ax.set_xlabel('Actual')
    ax.set_ylabel('Predicted')
    plt.title('NN')
    plt.show()
    return y_predict

'''
def svr_linear_iter(X,Y,x,y):
	rmse, y_predict = svr_linear(X,Y,x,y)
	i=1
	while rmse > 1.0 or i<6:
		print i
		train_X = np.column_stack((X,y_predict))
		rmse, y_predict = svr_linear(train_X,Y,x,y)
		i = i + 1
	return rmse, y_predict
'''
def RMSE(y, y_predict):
    y = np.asarray(y)
    y_predict = np.asarray(y_predict)
    return np.sqrt(((y_predict - y)**2).mean())

def pred_ints(model, X, percentile=95):
    err_down = []
    err_up = []
    for x in range(len(X)):
        preds = []
        for pred in model.estimators_:
            preds.append(pred.predict(X[x])[0])
        err_down.append(np.percentile(preds, (100 - percentile) / 2. ))
        err_up.append(np.percentile(preds, 100 - (100 - percentile) / 2.))
    return err_down, err_up

def find_months(dates):
    months=[]
    for i in range(0,len(dates)):
        months.append(dates[i].month)
    return months

def find_date(dates):
    date=[]
    for i in range(0,len(dates)):
        date.append(dates[i].day)
    return date

def find_year(dates):
    years=[]
    for i in range(0,len(dates)):
        years.append(dates[i].year)
    return years

def find_monthlymean(dates,vals):
    mean_monthly=[]
    curr_month = dates[0].month
    index = []
    x = []
    for i in range(0,len(dates)):
        if dates[i].month==curr_month:
            x.append(vals[i])
        else:
            mean_monthly.append(np.mean(x))
            #print str(np.mean(x)),",   ", str(dates[i-1])
            index.append(i-1)
            del x[:]
        curr_month = dates[i].month

    mean_monthly.append(np.mean(x))
    index.append(i)
    return mean_monthly

def find_yearlymean(dates,vals):
    mean_yearly=[]
    curr_year = dates[0].year
    index = []
    x=[]
    for i in range(0,len(dates)):
        if dates[i].year==curr_year:
            x.append(vals[i])
        else:
            mean_yearly.append(np.mean(x))
            #print str(np.mean(x)),",   ", str(dates[i].year)
            index.append(i-1)
            del x[:]
        curr_year = dates[i].year
    mean_yearly.append(np.mean(x))
    index.append(i)
    return mean_yearly

def means(dates, vals):
    mean_monthly = find_monthlymean(dates, vals)
    mean_yearly  = find_yearlymean(dates, vals)
    M_mean=[]
    Y_mean=[]
    curr_month = dates[0].month
    curr_year = dates[0].year
    j=0
    for i in range(0,len(dates)):
        if dates[i].month==curr_month:
            M_mean.append(mean_monthly[j])
        else:
            j=j+1
            M_mean.append(mean_monthly[j])
        curr_month = dates[i].month
    k=0
    for i in range(0, len(dates)):
        if dates[i].year==curr_year:
            Y_mean.append(mean_yearly[k])
        else:
            j=j+1
            Y_mean.append(mean_yearly[k])
        curr_year = dates[i].year
    return M_mean, Y_mean


def longestSubstringFinder(string1, string2):
    answer = ""
    len1, len2 = len(string1), len(string2)
    for i in range(len1):
        match = ""
        for j in range(len2):
            if (i + j < len1 and string1[i + j] == string2[j]):
                match += string2[j]
            else:
                if (len(match) > len(answer)): answer = match
                match = ""
    return answer


def get_features_2(date, val, lat, long, location_num, total_locations, percent_train_data, date_predict=datetime.now().date(), lt_=None, lng_=None):
    db = config.get_db()
    sensors = db.sensors
    sensors.create_index("id")
    dates = []
    vals = []
    lats = []
    longs = []
    # take only those datapoints for which data is not missing for any of the lat longs
    for i in range(0, val.__len__()):
        if len(val[i]) == total_locations:
            dates.append(date[i])
            vals.append(val[i])
            lats.append(lat[i])
            longs.append(long[i])

    #get only the date part of datetime
    for i in range(0, dates.__len__()):
        dates[i] = dates[i].date()

    #curr_date = datetime.now().date()
    '''d = []
    curr_date = date_predict
    for i in range(0,3):
        d.append (curr_date - timedelta(1))
        curr_date = curr_date - timedelta(1)'''


    if lt_!= None and lng_!=None:
        x = [float('nan'), float('nan'), float('nan'), float('nan')]
        util_x = [float('nan'), float('nan'), float('nan'), float('nan')]
        lts = [lt_, lt_, lt_, lt_]
        lngs = [lng_, lng_, lng_, lng_]

        stations_id = []
        stations_id.append(7)
        #n = len(lats[0])
        #df = comparison_funcs.closest_loc(n=n, lat=lt_, lng=lng_)
        #ID = df["ID"]
        #for other nearest locations(grid)
        #for id_ in ID:
        totaldata = []
        totaldata_ids = []
        totaldata.append(-1)
        totaldata_ids.append(-1)

        for i in range(0,total_locations):
            if i != location_num:
                step0 = time.time()
                lt = lats[0][i]
                lng = longs[0][i]
                df = comparison_funcs.closest_loc(lat=lt, lng=lng)
                ID = list(df["ID"])    

                while True: ####################
                    while True:
                        if (ID[0] in stations_id)==False:
                            id_ = ID[0]
                            break
                        else:
                            z = ID[0]
                            #print "deleting", str(z)
                            stations_id.append(z)
                            del ID[0]

                    if id_ in totaldata_ids:
                        index = totaldata_ids.index(id_)
                        yobidata = totaldata[index]
                        #print "Yobi %d found" % (id_)
                    else:
                        step00 = time.time()
                        #get data from last three days
                        pipeline = [
                                    { "$match": { "id": int(id_), "ts": {"$gt": str(date_predict - timedelta(4)), "$lt": str(date_predict) } } },
                                    { "$group": { "_id": "$ts", "t": { "$push": "$t2" } } },
                                    { "$sort" : SON([("_id", 1)]) }
                                    ]
                        yobidata = list(sensors.aggregate(pipeline, allowDiskUse = True))
                        totaldata_ids.append(id_)
                        totaldata.append(yobidata)
                        step1 = time.time()
                        #print "Loaded Yobi %d : (%ss)" % (id_,(round((step1 - step00), 1)))

                    if len(yobidata)!=0:
                        yobi_data = []
                        for q in yobidata:
                            if len(q["_id"])>=18 and len(q["t"])!=0:
                                q["_id"] = str(q["_id"])
                                yobi_data.append(q) 
                        if len(yobi_data)!=0:
                            yobi_dates, yobi_vals = dailysums.yobi_temp(yobi_data)
                            if len(yobi_vals)!=0:
                                #print "Yobi %d OK" % (id_)
                                break
                            else:
                                stations_id.append(id_)
                        else:
                            stations_id.append(id_)
                            #print " Yobi %d -- not useful" %(id_)
                    else:
                        stations_id.append(id_)
                        #print " Yobi %d -- not useful" % (id_)

                #check if temp values are zero
                yobi__vals = []
                for i in range(0,len(yobi_vals)):
                    if yobi_vals[i]==0 or math.isnan(yobi_vals[i]):
                        yobi__vals.append(np.mean(x))
                    else:
                        yobi__vals.append(yobi_vals[i])
                yobi_dates.reverse()
                yobi__vals.reverse() 
                if len(yobi__vals)>=3:
                    x.append(yobi__vals[0])
                    x.append(yobi__vals[1])
                    x.append(yobi__vals[2])
                    util_x.append(float('nan'))
                    util_x.append(yobi__vals[0])
                    util_x.append(yobi__vals[1])
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)

                elif len(yobi__vals)==1:
                    x.append(yobi__vals[0])
                    x.append(yobi__vals[0])
                    x.append(yobi__vals[0])
                    util_x.append(float('nan'))
                    util_x.append(yobi__vals[0])
                    util_x.append(yobi__vals[0])
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)

                elif len(yobi__vals)==2:
                    x.append(yobi__vals[0])
                    x.append(yobi__vals[1])
                    x.append(np.mean(yobi__vals))
                    util_x.append(float('nan'))
                    util_x.append(yobi__vals[0])
                    util_x.append(yobi__vals[1])
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)

        #for location itself
        step0 = time.time()
        _df = comparison_funcs.closest_loc(lat=lt_, lng=lng_)
        ID_ = list(_df["ID"]) 
        # id__ = comparison_funcs.get_nearest_loc_id(lat=lt_, lng=lng_)
        while True:
            if ID[0] in stations_id:
                del ID[0]
            else:
                id__ = ID[0]
                break

        if id__ in totaldata_ids:
            index = totaldata_ids.index(id__)
            yobi_data = totaldata[index]
            #print "Yobi %d found" % (id__)
        else:
            step0 = time.time()
            pipeline = [
                            { "$match": { "id": int(id__), "ts": {"$gt": str(date_predict-timedelta(4)), "$lt": str(date_predict)} } },
                            { "$group": { "_id": "$ts", "t": { "$push": "$t2" } } },
                            { "$sort" : SON([("_id", 1)]) }
                        ]
            yobi_data = list(sensors.aggregate(pipeline, allowDiskUse = True))
            step1 = time.time()
            #print "Loaded Yobi %d : (%ss)" % (id__,(round((step1 - step0), 1)))

        # convert dates into string objects
        for i in range(0,len(yobi_data)): 
            yobi_data[i]["_id"] = str(yobi_data[i]["_id"])  

        yobi_dates, yobi_vals = dailysums.yobi_temp(yobi_data)
        yobi_dates.reverse()
        yobi_vals.reverse()
        x[0] = yobi_vals[0]
        x[1] = yobi_vals[1]
        x[2] = yobi_vals[2]
        x[3] = np.mean(yobi_vals[0:3])
        util_x[0] = float('nan')
        util_x[1] = yobi_vals[0]
        util_x[2] = yobi_vals[1]
        util_x[3] = np.nanmean(util_x)

        x = np.matrix(x)
        x = x.reshape(1,-1) #only one sample


    #other features
    vals = np.asarray(vals)
    rows = vals.shape[0]
    cols = vals.shape[1]
    #dataframe
    data = pd.DataFrame({"dates": dates})

    data.insert(len(data.columns),str(location_num),vals[:,location_num])
    #rolling mean
    rolmean = data.rolling(window=3).mean()
    rolmean = np.asarray(rolmean.iloc[:,1])

    for i in range(0, 2):
        rolmean[i] = 0.0

    rolmean = np.asarray(rolmean)
    train_len = int(math.floor(len(vals) * (percent_train_data)))
    
    vals_7 = (vals[0:(len(vals) - 7), location_num])  # -7
    vals_6 = (vals[1:(len(vals) - 6), location_num])  # -6
    vals_5 = (vals[2:(len(vals) - 5), location_num])  # -5
    vals_4 = (vals[3:(len(vals) - 4), location_num])  # -4
    vals_3 = (vals[4:(len(vals) - 3), location_num])  # -3
    vals_2 = (vals[5:(len(vals) - 2), location_num])  # -2
    vals_1 = (vals[6:(len(vals) - 1), location_num])  # -1
    vals_0 = (vals[7:len(vals), location_num])  # y for training
    ordinal_dates = data.iloc[:, 0].apply(lambda x: x.toordinal())
    ordinal_dates = np.asarray(ordinal_dates)
    train_len = int(math.floor(len(vals_0) * (percent_train_data)))
    #rolmean[6:len(vals) - 1], ordinal_dates[7:len(vals)],
    X = np.column_stack((vals_1, vals_2, vals_3, rolmean[6:len(vals) - 1]))

    for i in range(0, total_locations):
        if i != location_num:
            X = np.column_stack((X, vals[6:(len(vals)-1), i], vals[5:(len(vals)-2), i], vals[4:(len(vals)-3), i]))

    X = np.column_stack((X,vals_0))
    X = np.column_stack((X, dates[7:len(vals)]))
    X = np.matrix(X)

    if lt_!= None and lng_!=None:
        XX = np.matrix(X[:,0:X.shape[1]-2])
        YY = np.asarray(np.matrix(X[:,(X.shape[1]-2)]).T)  
        YY = YY.reshape(-1,1)  
        #print YY
        #print x.shape[1]
        #print XX.shape[1]
        #print x.shape[0]
        #print XX.shape[0]
        #print YY.shape[0]
        #print len(YY)
        return XX, YY, x, util_x, lts, lngs, stations_id

    else:
        XX = np.matrix(X[0:train_len,0:X.shape[1]-2])
        YY = np.asarray(np.matrix(X[0:train_len,(X.shape[1]-2)]).T)
        xx = np.matrix(X[train_len:, 0:X.shape[1] - 2])
        yy = np.asarray(np.matrix(X[train_len:, (X.shape[1] - 2)]).T)
        dd = np.asarray(np.matrix(X[train_len:, (X.shape[1] - 1)]).T)
        return XX, YY, xx, yy, dd



def get_features_r(date, val, lat, long, location_num, total_locations, percent_train_data, date_predict=datetime.now().date(), lt_=None, lng_=None):
    db = config.get_db()
    sensors = db.sensors
    sensors.create_index("id")
    dates = []
    vals = []
    lats = []
    longs = []
    # take only those datapoints for which data is not missing for any of the lat longs
    for i in range(0, val.__len__()):
        if len(val[i]) == total_locations:
            dates.append(date[i])
            vals.append(val[i])
            lats.append(lat[i])
            longs.append(long[i])

    #get only the date part of datetime
    for i in range(0, dates.__len__()):
        dates[i] = dates[i].date()

    months = find_months(dates)

    if lt_!= None and lng_!=None:
        x = [float('nan'), float('nan'), float('nan'), float('nan'), float('nan'), float('nan'), float('nan')]
        util_x = [float('nan'), float('nan'), float('nan'),float('nan'), float('nan'), float('nan'), float('nan')]
        lts = [lt_, lt_, lt_, lt_, lt_, lt_, lt_]
        lngs = [lng_, lng_, lng_, lng_, lng_, lng_, lng_]

        stations_id = []
        stations_id.append(7)
        totaldata = []
        totaldata_ids = []
        totaldata.append(-1)
        totaldata_ids.append(-1)

        for i in range(0,total_locations):
            if i != location_num:
                step0 = time.time()
                lt = lats[0][i]
                lng = longs[0][i]
                df = comparison_funcs.closest_loc(lat=lt, lng=lng)
                ID = list(df["ID"])    

                while True:
                    while True:
                        if (ID[0] in stations_id)==False:
                            id_ = ID[0]
                            break
                        else:
                            z = ID[0]
                            stations_id.append(z)
                            del ID[0]

                    if id_ in totaldata_ids:
                        index = totaldata_ids.index(id_)
                        yobidata = totaldata[index]
                    else:
                        step00 = time.time()
                        #get data from last FIVE days
                        pipeline = [
                                    { "$match": { "id": int(id_), "ts": {"$gt": str(date_predict - timedelta(6)), "$lt": str(date_predict) } } },
                                    { "$group": { "_id": "$ts", "r": { "$push": "$r" } } },
                                    { "$sort" : SON([("_id", 1)]) }
                                    ]
                        yobidata = list(sensors.aggregate(pipeline, allowDiskUse = True))
                        totaldata_ids.append(id_)
                        totaldata.append(yobidata)
                        step1 = time.time()
                        #print "Loaded Yobi %d : (%ss)" % (id_,(round((step1 - step00), 1)))

                    if len(yobidata)!=0: #might be useful 
                        yobi_data = []
                        for q in yobidata:
                            if len(q["_id"])>=18 and len(q["r"])!=0:
                                #if math.isnan(q["r"])==False:
                                q["_id"] = str(q["_id"])
                                yobi_data.append(q) 

                        if len(yobi_data)!=0: #might be useful
                            yobi_dates, yobi_vals, a, b = dailysums.yobi(yobi_data)
                            if len(yobi_vals)>=4: #useful data
                                #print "Yobi %d OK" % (id_)
                                break
                            else: #not useful - add to stations_id
                                stations_id.append(id_)
                                #print " Yobi %d -- not useful" %(id_)
                        else: #not useful -  add to stations_id
                            stations_id.append(id_)
                            #print " Yobi %d -- not useful" %(id_)
                    else: #not useful - add to stations_id
                        stations_id.append(id_)
                        #print " Yobi %d -- not useful" % (id_)

                yobi__vals=[]
                #check if rainfall values are NaN
                for i in range(0,len(yobi_vals)):
                    if math.isnan(yobi_vals[i]):
                        yobi__vals.append(0.0)
                    else:
                        yobi__vals.append(yobi_vals[i])
                yobi_dates.reverse()
                yobi__vals.reverse() 

                #print yobi__vals
                #print yobi_dates

                if len(yobi__vals)>=5:
                    for j in range(0,5):
                        if math.isnan(yobi__vals[i]):
                            x.append(0.0)
                        else:
                            x.append(yobi__vals[i])
                    #x.append(yobi__vals[0])
                    #x.append(yobi__vals[1])
                    #x.append(yobi__vals[2])
                    #x.append(yobi__vals[3])
                    #x.append(yobi__vals[4])
                    util_x.append(float('nan'))
                    for j in range(0,4):
                        if math.isnan(yobi__vals[i]):
                            util_x.append(0.0)
                        else:
                            util_x.append(yobi__vals[i])
                    #util_x.append(yobi__vals[0])
                    #util_x.append(yobi__vals[1])
                    #util_x.append(yobi__vals[2])
                    #util_x.append(yobi__vals[3])
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)

                elif len(yobi__vals)==4:
                    for j in range(0,4):
                        if math.isnan(yobi__vals[i]):
                            x.append(0.0)
                        else:
                            x.append(yobi__vals[i])
                    #x.append(yobi__vals[0])
                    #x.append(yobi__vals[1])
                    #x.append(yobi__vals[2])
                    #x.append(yobi__vals[3])
                    x.append(np.mean(yobi__vals))
                    util_x.append(float('nan'))
                    for j in range(0,4):
                        if math.isnan(yobi__vals[i]):
                            util_x.append(0.0)
                        else:
                            util_x.append(yobi__vals[i])
                    #util_x.append(yobi__vals[0])
                    #util_x.append(yobi__vals[1])
                    #util_x.append(yobi__vals[2])
                    #util_x.append(yobi__vals[3])
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)

                elif len(yobi__vals)==3:
                    for j in range(0,3):
                        if math.isnan(yobi__vals[i]):
                            x.append(0.0)
                        else:
                            x.append(yobi__vals[i])
                    #x.append(yobi__vals[0])
                    #x.append(yobi__vals[1])
                    #x.append(yobi__vals[2])
                    x.append(np.mean(yobi__vals))
                    x.append(np.mean(yobi__vals))
                    util_x.append(float('nan'))
                    for j in range(0,3):
                        if math.isnan(yobi__vals[i]):
                            util_x.append(0.0)
                        else:
                            util_x.append(yobi__vals[i])
                    util_x.append(np.mean(yobi__vals))
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)

                elif len(yobi__vals)==2:
                    for j in range(0,2):
                        if math.isnan(yobi__vals[i]):
                            x.append(0.0)
                        else:
                            x.append(yobi__vals[i])
                    #x.append(yobi__vals[0])
                    #x.append(yobi__vals[1])
                    x.append(np.mean(yobi__vals))
                    x.append(np.mean(yobi__vals))
                    x.append(np.mean(yobi__vals))
                    util_x.append(float('nan'))
                    for j in range(0,2):
                        if math.isnan(yobi__vals[i]):
                            util_x.append(0.0)
                        else:
                            util_x.append(yobi__vals[i])
                    #util_x.append(yobi__vals[0])
                    #util_x.append(yobi__vals[1])
                    util_x.append(np.mean(yobi__vals))
                    util_x.append(np.mean(yobi__vals))
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)

                elif len(yobi__vals)==1:
                    if math.isnan(yobi__vals[0]):
                        x.append(0.0)
                    else:
                        x.append(yobi__vals[0])
                    #x.append(yobi__vals[0])
                    x.append(np.mean(yobi__vals))
                    x.append(np.mean(yobi__vals))
                    x.append(np.mean(yobi__vals))
                    x.append(np.mean(yobi__vals))
                    util_x.append(float('nan'))
                    if math.isnan(yobi__vals[0]):
                        util_x.append(0.0)
                    else:
                        util_x.append(yobi__vals[0])
                    util_x.append(np.mean(yobi__vals))
                    util_x.append(np.mean(yobi__vals))
                    util_x.append(np.mean(yobi__vals))
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
                    lts.append(lt)
                    lngs.append(lng)
            #print x

        #for location itself
        step0 = time.time()
        _df = comparison_funcs.closest_loc(lat=lt_, lng=lng_)
        ID_ = list(_df["ID"]) 
        # id__ = comparison_funcs.get_nearest_loc_id(lat=lt_, lng=lng_)
        while True:
            if ID[0] in stations_id:
                del ID[0]
            else:
                id__ = ID[0]
                break

        if id__ in totaldata_ids:
            index = totaldata_ids.index(id__)
            yobi_data = totaldata[index]
            #print "Yobi %d found" % (id__)
        else:
            step0 = time.time()
            pipeline = [
                            { "$match": { "id": int(id__), "ts": {"$gt": str(date_predict-timedelta(6)), "$lt": str(date_predict)} } },
                            { "$group": { "_id": "$ts", "r": { "$push": "$r" } } },
                            { "$sort" : SON([("_id", 1)]) }
                        ]
            yobi_data = list(sensors.aggregate(pipeline, allowDiskUse = True))
            step1 = time.time()
            #print "Loaded Yobi %d : (%ss)" % (id__,(round((step1 - step0), 1)))

        # convert dates into string objects
        for i in range(0,len(yobi_data)): 
            yobi_data[i]["_id"] = str(yobi_data[i]["_id"])  

        yobi_dates, yobi_vals, a, b = dailysums.yobi(yobi_data)
        yobi_dates.reverse()
        yobi_vals.reverse()
        x[0] = yobi_vals[0]
        x[1] = yobi_vals[1]
        x[2] = yobi_vals[2]
        x[3] = yobi_vals[3]
        x[4] = yobi_vals[4]
        x[5] = np.mean(yobi_vals[0:3])
        x[6] = datetime.now().date().month
        print yobi_dates
        print yobi__vals
        util_x[0] = float('nan')
        util_x[1] = yobi_vals[0]
        util_x[2] = yobi_vals[1]
        util_x[3] = yobi_vals[2]
        util_x[4] = yobi_vals[3]
        util_x[5] = np.nanmean(util_x)
        util_x[6] = datetime.now().date().month

        x = np.matrix(x)
        x = x.reshape(1,-1) #only one sample

    #other features
    vals = np.asarray(vals)
    rows = vals.shape[0]
    cols = vals.shape[1]
    #dataframe
    data = pd.DataFrame({"dates": dates})

    data.insert(len(data.columns),str(location_num),vals[:,location_num])
    #rolling mean
    rolmean = data.rolling(window=3).mean()
    rolmean = np.asarray(rolmean.iloc[:,1])

    for i in range(0, 2):
        rolmean[i] = 0.0

    rolmean = np.asarray(rolmean)
    train_len = int(math.floor(len(vals) * (percent_train_data)))
    
    vals_7 = (vals[0:(len(vals) - 7), location_num])  # -7
    vals_6 = (vals[1:(len(vals) - 6), location_num])  # -6
    vals_5 = (vals[2:(len(vals) - 5), location_num])  # -5
    vals_4 = (vals[3:(len(vals) - 4), location_num])  # -4
    vals_3 = (vals[4:(len(vals) - 3), location_num])  # -3
    vals_2 = (vals[5:(len(vals) - 2), location_num])  # -2
    vals_1 = (vals[6:(len(vals) - 1), location_num])  # -1
    vals_0 = (vals[7:len(vals), location_num])  # y for training
    ordinal_dates = data.iloc[:, 0].apply(lambda x: x.toordinal())
    ordinal_dates = np.asarray(ordinal_dates)
    train_len = int(math.floor(len(vals_0) * (percent_train_data)))
    #rolmean[6:len(vals) - 1], ordinal_dates[7:len(vals)],
    X = np.column_stack((vals_1, vals_2, vals_3, vals_4, vals_5, rolmean[6:len(vals) - 1], months[7:len(vals)] ))

    for i in range(0, total_locations):
        if i != location_num:
            X = np.column_stack((X, vals[6:(len(vals)-1), i], vals[5:(len(vals)-2), i], vals[4:(len(vals)-3), i], vals[3:(len(vals)-4), i], vals[2:(len(vals)-5), i], ))

    X = np.column_stack((X,vals_0))
    X = np.column_stack((X, dates[7:len(vals)]))
    X = np.matrix(X)

    if lt_!= None and lng_!=None:
        XX = np.matrix(X[:,0:X.shape[1]-2])
        YY = np.asarray(np.matrix(X[:,(X.shape[1]-2)]).T)  
        YY = YY.reshape(-1,1)  
        #print YY
        #print x.shape[1]
        #print XX.shape[1]
        #print x.shape[0]
        #print XX.shape[0]
        #print YY.shape[0]
        #print len(YY)
        return XX, YY, x, util_x, lts, lngs

    else:
        XX = np.matrix(X[0:train_len,0:X.shape[1]-2])
        YY = np.asarray(np.matrix(X[0:train_len,(X.shape[1]-2)]).T)
        xx = np.matrix(X[train_len:, 0:X.shape[1] - 2])
        yy = np.asarray(np.matrix(X[train_len:, (X.shape[1] - 2)]).T)
        dd = np.asarray(np.matrix(X[train_len:, (X.shape[1] - 1)]).T)
        return XX, YY, xx, yy, dd