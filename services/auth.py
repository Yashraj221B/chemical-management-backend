from passlib.context import CryptContext
from db import users_collection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_user(username: str, password: str) -> bool:
    user = users_collection.find_one({"username": username})
    if not user:
        return False
    return pwd_context.verify(password, user["password"])

def create_user(username: str, password: str):
    if users_collection.find_one({"username": username}):
        return False  # Already exists
    hashed = pwd_context.hash(password)
    users_collection.insert_one({
        "username": username,
        "password": hashed
    })
    return True
