import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("CQC_API_KEY")

# list the locations
url = "https://api.service.cqc.org.uk/public/v1/locations"
headers = {"Ocp-Apim-Subscription-Key": api_key}
params = {"region": "London", "perPage": 5}

response = requests.get(url, headers=headers, params=params, timeout=30)

print(response.status_code)
data = response.json()
print(data.keys())

# looking inside the nested location list
location_id = data["locations"][0]["locationId"]
print(location_id)

# get full details for that London location by using Get Location By Id
detail_url = url + "/" + location_id
detail = requests.get(detail_url, headers=headers, timeout=30)

print(detail.status_code)
print(detail.json().keys())
print(detail.json()["region"])
print(detail.json()["type"])
print(detail.json()["name"])

# Quirks
# - the region filter worked, a real location's region came back as London
# - Get Locations (the list call) doesn't give the full details but only ID, name and postcode,
#   so I need to call Get Location By Id for each location ID to get the full record
# - the list call returns results in pages (page, totalPages, nextPageUri)
