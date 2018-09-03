# Python dependencies for pulling data
import urllib2
import json

# API Gateway 1
# Better for Pandas

import pandas as pd

# Getting the data from the server, and storing it into a large JSON object
y 			= urllib2.urlopen('http://www.yobi.tech/pandas-api?user=[USERNAME]&password=[PASSWORD]&id=[ID NO]')
yobibyte    = json.loads(y.read())

# Name of the weather station location
name        = yobibyte["meta"][0]["name"]
# Latitude of weather station location
latitude    = yobibyte["meta"][0]["lt"]
# Longitude of weather station location
longitude   = yobibyte["meta"][0]["ln"]
# When the weather station was installed
installDate = yobibyte["meta"][0]["installDate"]

# Converting uploads into pandas DataFrame
df = pd.DataFrame(yobibyte["uploads"])