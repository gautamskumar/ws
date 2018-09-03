import pymongo
import math
from pymongo import MongoClient

# MongoDB Configuration data
def get_db():

    client = MongoClient(
        'mongodb://heroku_bnjrx3s8:ra6mg5rivid9dm2r38u0nvr74g@ds019085-a0.mlab.com:19085,ds019085-a1.mlab.com:19085/heroku_bnjrx3s8?replicaSet=rs-ds019085')
    db = client.heroku_bnjrx3s8
    return db

# Google Maps API key
def get_maps_api_key():
    return "AIzaSyAI6Rl5MO_htYUgemf5MUdFHfULFlKc-0M"

# States to target
def get_target_states():
    return ["Andhra Pradesh","Arunachal Pradesh","Assam","Chattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh",
            "Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Nagaland","Odissa","Punjab","Rajasthan",
            "Sikkim","Tamil Nadu","Uttar Pradesh","West Bengal","Uttarakhand","Bihar","Daman and Diu",
            "Meghalaya","Jammu and Kashmir","Tripura","Mizoram","Manipur","Puducherry","Chandigarh", "Delhi"]

# Days for which to scrape accuweather data:
def aw_max_days():
    return 5

def get_sensor_rain_calibration(day_sum):
    return day_sum * 0.1
    #2714

def get_sensor_wind_calibration(day_sum):
    return round(day_sum / 8,1)

def get_sensor_solar_calibration(day_sum):
    if day_sum <= 0:
        return 0
    else:
        return round(day_sum*180, 2) 

def get_sensor_power_calibration(day_sum):
    return round((day_sum/10-10)*2, 2)

# def get_sensor_temp_calibration(val, solar):
#     return (val - solar/150)

def imd_states():
    return ["Andhra Pradesh","Arunachal Pradesh","Assam","Chattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh",
            "Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Nagaland","Orissa","Punjab","Rajasthan",
            "Sikkim","Tamil Nadu","Uttar Pradesh","West Bengal","Uttarakhand","Delhi","Bihar","Daman and Diu",
            "Meghalaya","Jammu and Kashmir","Tripura","Mizoram","Manipur","Puducherry","Chandigarh","Bhutan"]