import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client.chemicals_db
# db = client.chemical_inventory
chemicals_collection = db.chemicals
users_collection = db.users
shelves_collection = db.shelves