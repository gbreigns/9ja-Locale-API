import json
import pprint
from api.model.db import connect_to_db


# Connect to database
client = connect_to_db()

database = client.locale

# Open JSON file
try:
    with open("api/data/nigeria-data.json", "r") as json_file:
        data = json.load(json_file)
        # collection = database.data
        # collection.insert_many(data)
except Exception as e:
    print(e)


try:
    with open("api/data/dataset.json", "r") as json_file:
        local_government = json.load(json_file)
        collection = database.local_government
        # collection.insert_many(local_government)
except Exception as e:
    print(e)


# Create a new collection for geopolitical zones
geopolitical_zones = database.regions

local_governments = database.local_governments


# Get distinct geopolitical zones with their corresponding states
try:
    geopolitical_zones_states = collection.aggregate(
        [{"$group": {"_id": "$geo_politcal_zone", "states": {"$addToSet": "$state"}}}]
    )

    # Insert geopolitical zones and their corresponding states into the new collection
    for geopolitical_zone in geopolitical_zones_states:
        region = {
            "geo_political_zone": geopolitical_zone["_id"],
            "states": geopolitical_zone["states"],
        }
        # geopolitical_zones.insert_one(region)

except Exception as e:
    print(e)

# try:
#     for lgas in data:
#         state = collection.find_one({"state": lgas["state"]})

#         if state:
#             local_government_area = {
#                 "lga": lgas["lgas"],
#                 "state_id": state["_id"],
#                 "state": state["state"],
#             }
#             # local_governments.insert_one(local_government_area)
#         else:
#             print("State not found")
# except Exception as e:
#     print(e)


# Update local government with state id
try:
    lga = collection.aggregate(
        [{"$lookup": {
            "from": "local_governments", 
            "localField": "state", 
            "foreignField": "state", 
            "as": "states"}
            },
            {
                "$addFields": {
                    "state_id": {
                        "$arrayElemAt": ["$states._id", 0]
                    }
                }
            }
        ]
    )

    for local_government in lga:
        # print(local_government)
        local_government.update_one({"lga": local_government["lga"]}, {"$set": {"state_id": local_government["state_id"]}})
        # pass
except Exception as e:
    print(e)

    

# client.close()
