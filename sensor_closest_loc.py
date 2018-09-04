# Version 1
from Queue import PriorityQueue
from geopy.distance import vincenty
import config

# Defining database values:
db = config.get_db()

# Locations collection:
lat_lng = db.ids


# Get all locations
def get_locations():
    result = list(lat_lng.find({}, {"lt": 1, "ln": 1, "name": 1, "_id": 0}))
    return result

# Get the closest location to the given latitude and longitude
def closest_loc(lat, lng):
    locations = get_locations()
    close_dis = float('inf')
    close_loc = None
    for location in locations:
        p1 = (location["lat"], location["lng"])
        p2 = (lat, lng)

        # Uncomment preferred distance calculation algorithm
        # Vincenty is slower but more accurate
        dis = round(((vincenty(p1, p2).meters) / 1000.0), 1)
        # dis = round(((great_circle(p1, p2).meters)/1000.0),1)

        if dis < close_dis:
            close_dis = dis
            close_loc = location

            # print str(dis) + ": " + str(location)

    # print close_dis
    return close_loc

# Get priority queue of closest locations to the given latitude and longitude
# result is a queue of tuples of the form: (Distance, Location)
def closest_loc_queue(lat, lng):
    loc_queue = PriorityQueue()
    locations = get_locations()
    for location in locations:
        p1 = (location["lt"], location["ln"])
        p2 = (lat, lng)

        # Uncomment preferred distance calculation algorithm
        # Vincenty is slower but more accurate
        dis = round(((vincenty(p1, p2).meters) / 1000.0), 1)
        # dis = round(((great_circle(p1, p2).meters)/1000.0),1)

        loc_queue.put((dis, location))
    return loc_queue
