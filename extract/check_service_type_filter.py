import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("CQC_API_KEY")

# list London locations that offer a mental health or substance misuse service type
url = "https://api.service.cqc.org.uk/public/v1/locations"
headers = {"Ocp-Apim-Subscription-Key": api_key}
params = {
    "region": "London",
    "gacServiceTypeDescription": [
        "Hospital services for people with mental health needs, learning disabilities and problems with substance misuse",
        "Community based services for people with mental health needs",
        "Community based services for people who misuse substances",
        "Residential substance misuse treatment and/or rehabilitation service",
    ],
    "perPage": 5,
}

response = requests.get(url, headers=headers, params=params, timeout=30)
print(response.status_code)

data = response.json()
print(data["total"])

# check the first one
location_id = data["locations"][0]["locationId"]
detail = requests.get(url + "/" + location_id, headers=headers, timeout=30)

print(detail.json()["name"])
print(detail.json()["gacServiceTypes"])

# Quirk comments
# - wanted to compare with the category filter so tried service types too
# - used the names from the CQC csv first but got 0 back
# - printed one record and saw each service type has a name and a longer description
# - filter is called gacServiceTypeDescription so tried the descriptions instead, that worked
# - 459 London locations this way (category filter gave 339)
# - so service type picks up more, anything that offers MH not just mainly MH
# - both fields are in every record anyway so can extract this way and narrow down later
