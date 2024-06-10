import pymongo
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_DB_URI = str(os.getenv("MONGO_DB_URI"))
MONGO_DB_NAME = str(os.getenv("MONGO_DB_NAME"))
MONGO_COLLECTION_NAME = str(os.getenv("MONGO_COLLECTION_NAME"))

mongo_client = pymongo.MongoClient(MONGO_DB_URI)
db = mongo_client[MONGO_DB_NAME]
listings_collection = db[MONGO_COLLECTION_NAME]

def get_listings(query_params):
    query = {}
    for key, value in query_params.items():
        if key in ["bedrooms", "bathrooms"]:
            query[key] = int(value)
        else:
            query[key] = value

    listings = listings_collection.find(query)
    print(listings)
    return list(listings)

# Example usage
params_san_francisco = {
    "city": "San Francisco",
    "state": "CA",
    "propertyType": "Apartment",
    "bedrooms": 1,
    "bathrooms": 1,
    "status": "Active",
}

listings = get_listings(params_san_francisco)
for listing in listings:
    print(listing)

def delete_documents():
    listings_collection.update_many({}, {"$unset": {"embedding": ""}})

delete_documents()

