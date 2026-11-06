import os
import time

import requests
from dotenv import load_dotenv

# load my API key from the .env file
load_dotenv()
api_key = os.getenv("CQC_API_KEY")

url = "https://api.service.cqc.org.uk/public/v1/locations"
headers = {"Ocp-Apim-Subscription-Key": api_key}

# the four service types I chose (see check_service_type_filter.py)
service_types = [
    "Hospital services for people with mental health needs, learning disabilities and problems with substance misuse",
    "Community based services for people with mental health needs",
    "Community based services for people who misuse substances",
    "Residential substance misuse treatment and/or rehabilitation service",
]


# part 1: collect all the location IDs, page by page
location_ids = []
page = 1

while True:
    params = {
        "region": "London",
        "gacServiceTypeDescription": service_types,
        "perPage": 100,
        "page": page,
    }
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # add every ID on this page to my list
    for location in data["locations"]:
        location_ids.append(location["locationId"])

    # stop once I've reached the last page
    if page >= data["totalPages"]:
        break
    page = page + 1

print("IDs found:", len(location_ids), "of", data["total"])


# part 2: get each location's full record and save it

os.makedirs("data/raw", exist_ok=True)

for location_id in location_ids:
    file_path = "data/raw/" + location_id + ".json"

    if os.path.exists(file_path):
        continue

    # get the full record,  try again (up to 3 times) if CQC is busy or has a server error
    for attempt in range(3):
        detail = requests.get(url + "/" + location_id, headers=headers, timeout=30)
        if detail.status_code == 429 or detail.status_code >= 500:
            time.sleep(5)
        else:
            break

    # stop if it still didn't work
    detail.raise_for_status()

    # save as CQC sent
    with open(file_path, "w") as f:
        f.write(detail.text)

    # short pause to not overload CQC
    time.sleep(0.2)

print("done")


# comments
# - uses the service type filter (459 London locations), see check_service_type_filter.py
# - collects the IDs page by page (100 per page), then one detail call per ID
# - saves each record as it came back, one file per location in data/raw
# - skips files that are already there, so if it stops you can just run it again
#   (I hit ctrl+c halfway by accident, re-ran it and it carried on)
