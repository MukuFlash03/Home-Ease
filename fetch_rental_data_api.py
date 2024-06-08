import requests
import pymongo
import os
from dotenv import load_dotenv
import logging
# from urllib.parse import urlencode

# Load environment variables from .env file
load_dotenv()

RENT_CAST_API_KEY = str(os.getenv("RENT_CAST_API_KEY"))
MONGO_DB_URI = str(os.getenv("MONGO_DB_URI"))
MONGO_DB_NAME = str(os.getenv("MONGO_DB_NAME"))
MONGO_COLLECTION_NAME = str(os.getenv("MONGO_COLLECTION_NAME"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

mongo_client = pymongo.MongoClient(MONGO_DB_URI)
db = mongo_client[MONGO_DB_NAME]
listings_collection = db[MONGO_COLLECTION_NAME]

def fetch_listings(query_params):
    base_url = "https://api.rentcast.io/v1/listings/rental/long-term"
        
    headers = {
        "accept": "application/json",
        "X-Api-Key": RENT_CAST_API_KEY
    }

    params = {
        "city": query_params.get("city", "San Francisco"),
        "state": query_params.get("state", "CA"),
        "propertyType": query_params.get("propertyType", "Apartment"),
        "bedrooms": query_params.get("bedrooms", "1"),
        "bathrooms": query_params.get("bathrooms", "1"),
        "status": query_params.get("status", "Active"),
        "limit": query_params.get("limit", "5")
    }

    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching listings: {e}")
        return []

params_san_francisco = {
    "city": "San Francisco",
    "state": "CA",
    "propertyType": "Apartment",
    "bedrooms": "1",
    "bathrooms": "1",
    "status": "Active",
    "limit": "5"
}

def insert_listings_to_collection(listings, collection):
    for listing in listings:
        try:
            collection.insert_one(listing)
            logging.info(f"Inserted listing: {listing['id']}")
        except pymongo.errors.PyMongoError as e:
            logging.error(f"Error inserting listing {listing['id']}: {e}")

listings = fetch_listings(params_san_francisco)
print(listings)

insert_listings_to_collection(listings_collection)


