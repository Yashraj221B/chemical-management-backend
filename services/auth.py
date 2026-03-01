from db import users_collection
from services.security import hash_password, verify_password

def verify_user(username: str, password: str) -> bool:
    user = users_collection.find_one({"username": username})
    if not user:
        return False
    return verify_password(password, user["password"])

def create_user(username: str, password: str):
    if users_collection.find_one({"username": username}):
        return False  # Already exists
    hashed = hash_password(password)
    users_collection.insert_one({
        "username": username,
        "password": hashed
    })
    return True
