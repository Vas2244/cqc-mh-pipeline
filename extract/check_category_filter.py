import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("CQC_API_KEY")

# list London locations whose main category is mental health or substance misuse
url = "https://api.service.cqc.org.uk/public/v1/locations"
headers = {"Ocp-Apim-Subscription-Key": api_key}
params = {
    "region": "London",
    "primaryInspectionCategoryName": [
        "Mental health - community & residential - NHS",
        "Mental health - community & hospital - independent",
        "Community substance misuse",
        "Residential substance misuse",
    ],
    "perPage": 5,
}

response = requests.get(url, headers=headers, params=params, timeout=30)
print(response.status_code)

data = response.json()
print(data["total"])

# check first one is a mental health service
location_id = data["locations"][0]["locationId"]
detail = requests.get(url + "/" + location_id, headers=headers, timeout=30)

print(detail.json()["name"])
print(detail.json()["inspectionCategories"])

# commments
# - used the primary category so I only get services that are only mental health, non primary are general that also offers MH
# - got the category names from CQC's locations csv (the docs didn't list them)
# - NHS mental health only: 85 London locations. all four categories: 339
# - checked one: the Tavistock Centre came back as mental health (I referred patients here!)
