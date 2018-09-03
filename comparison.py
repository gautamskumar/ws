@app.route('/comparison/<id>', methods=["GET", "POST"])
def comparison(id):

    # fetch data for that id
    sensor_data = list(sensors.find({'id': int(id)}).sort('ts', pymongo.ASCENDING))

    data = []
    dates = []  # %Y-%m-%d %H:%M:%S
    temps = []
    humidities = []
    rainfall = []
    windspeed = []
    pressures = []
    signals = []

    sensor = (ids.find_one({'id': int(id)}))

    name = sensor["name"]
    aw_deets = sensor["aw"]
    sm_deets = sensor["sm"]
    wrf_deets = sensor["wrf"]

    # /////Getting WRF data

    wrf_c_loc = wrf_deets[0][1]
    print "WRF closest location: " + str(wrf_c_loc)

    wrf_dates = []
    wrf_temps = []
    wrf_rainfall_max = []
    wrf_rainfall_min = []

    regx = re.compile("(.*)" + wrf_c_loc, re.IGNORECASE)
    wrf_timestamps = list(wrf.find({'loc': regx, "n_predict": 1}, {"_id": 0}).sort('date', pymongo.ASCENDING))

    for timestamp in wrf_timestamps:
        wrf_dates.append(datetime.strptime(timestamp['date'], '%Y-%m-%d'))
        wrf_rainfall_max.append(timestamp['rmax'])
        wrf_rainfall_min.append(timestamp['rmin'])

    # print str(wrf_dates)
    # print str(wrf_rainfall_min)
    # print str(wrf_rainfall_max)
    # /////

    # /////Getting Skymet data

    sm_c_loc = sm_deets[0][1]
    print "Skymet closest location: " + str(sm_c_loc)

    sm_dates = []
    sm_temps = []
    sm_rainfall = []

    sm_timestamps = list(
        sm.find({'loc': sm_c_loc.lower(), "n_predict": 1}).sort('timestamp', pymongo.ASCENDING))

    if len(sm_timestamps) < 1:
        sm_timestamps = list(
            sm.find({'loc': sm_c_loc, "n_predict": 1}).sort('timestamp', pymongo.ASCENDING))

    for timestamp in sm_timestamps:
        sm_dates.append(datetime.strptime(timestamp['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))
        sm_rainfall.append(timestamp['rain'])
    
    # /////

    # /////Getting Accuweather data

    aw_c_loc = aw_deets[0][1]
    print "Accuweather closest location: " + str(aw_c_loc)

    aw_dates = []
    aw_temps = []
    aw_rainfall = []

    aw_timestamps = list(
        aw.find({'loc': aw_c_loc.lower(), "n_predict": 2}).sort('timestamp', pymongo.ASCENDING))

    if len(aw_timestamps) < 1:
        aw_timestamps = list(
            aw.find({'loc': aw_c_loc, "n_predict": 2}).sort('timestamp', pymongo.ASCENDING))

    # for timestamp in aw_timestamps:
        # print timestamp

    # Iterating over found timestamps as pairs
    for i in range(0, aw_timestamps.__len__() / 2):
        aw_dates.append(datetime.strptime(aw_timestamps[2 * i]['timestamp'], '%Y-%m-%d %H:%M:%S.%f'))

        # print aw_timestamps[2 * i]
        aw_rain = (float(aw_timestamps[2 * i]["rain"]) + float(aw_timestamps[2 * i + 1]["rain"]))
        # print aw_rainfall
        aw_rainfall.append(aw_rain)

    # Extract Data from JSON Objects into arrays
    for elem in sensor_data:
        if 't1' in elem:
            dates.append(datetime.strptime(elem['ts'], '%Y-%m-%d %H:%M:%S'))
            temps.append(elem['t1'])
            humidities.append(elem['h'])
            rainfall.append(elem['r'])
            windspeed.append(elem['w'])
            pressures.append(elem['p'])

    # Adding up rainfall for individual days:
    sum_rainfall = []
    sum_rainfall_dates = []
    curr_date = dates[0]
    curr_date_rainfall = 0.0
    # for every data point
    for i in range(0, dates.__len__()):
        # if the day is the same
        if dates[i].date() == curr_date.date():
            curr_date_rainfall += float(rainfall[i])
        # if it's a new day:
        else:
            # print "day over: " + str(curr_date) + ": " + str(curr_date_rainfall)
            # Accounting for
            sum_rainfall.append(config.get_sensor_rain_calibration(curr_date_rainfall))
            sum_rainfall_dates.append(curr_date)
            curr_date_rainfall = 0.0
            curr_date = dates[i]

    # trace_data(dates, rainfall, "Rain (mm)")

    trace_data(sum_rainfall_dates, sum_rainfall, "Rain (mm)", data)
    trace_data(aw_dates, aw_rainfall, "AW Rain (mm)", data)
    trace_data(sm_dates, sm_rainfall, "SM Rain (mm)", data)
    trace_data(wrf_dates, wrf_rainfall_max, "WRF Rain (mm) (Max)", data)
    trace_data(wrf_dates, wrf_rainfall_min, "WRF Rain (mm) (Min)", data)

    # print "AW Error Mean:    " + str(aw_mean)
    # print "AW Error Std Dev: " + str(aw_stdev)
    # print "SM Error Mean:    " + str(sm_mean)
    # print "SM Error Std Dev: " + str(sm_stdev)

    # wrf_min_mean = np.mean(wrf_min_errors)
    # wrf_min_stdev = np.std(wrf_min_errors)

    # wrf_max_mean = np.mean(wrf_max_errors)
    # wrf_max_stdev = np.std(wrf_max_errors)

    start = str(dates[0].date())
    end = str(dates[-1].date())

    title = 'Analytics for ' + name + ' (' + start + ' - ' + end + ')'

    layout = go.Layout(
        title=title,
        font=dict(family='HelveticaNeue-Medium', size=14, color='#D0D0D0'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data=data, layout=layout)
    plot_url = py.plot(fig, filename='test 101', auto_open=False)

    return render_template('comparison.html',
        id = id, name = name,
        aw_loc = str(aw_c_loc), aw_km = str(aw_deets[0][0]), 
        aw_mean = aw_mean, aw_stdev = aw_stdev, aw_obs = aw_obs, 
        sm_loc = str(sm_c_loc), sm_km = str(sm_deets[0][0]), 
        sm_mean = sm_mean, sm_stdev = sm_stdev, sm_obs = sm_obs, 
        wrf_loc = str(wrf_c_loc), wrf_km = str(wrf_deets[0][0]),
        wrf_min_mean = wrf_min_mean, wrf_min_stdev = wrf_min_stdev, wrf_min_obs = wrf_min_obs, 
        wrf_max_mean = wrf_max_mean, wrf_max_stdev = wrf_max_stdev, wrf_max_obs = wrf_max_obs,
        awcomp = awcomp, awPC = awPC, awHSS = awHSS,
        smcomp = smcomp, smPC = smPC, smHSS = smHSS,
        wmincomp = wmincomp, wminPC = wminPC, wminHSS = wminHSS,
        wmaxcomp = wmaxcomp, wmaxPC = wmaxPC, wmaxHSS = wmaxHSS)