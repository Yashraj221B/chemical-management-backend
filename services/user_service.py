from db import users_collection
from models.user import User
from datetime import datetime, timezone
from services.security import hash_password as secure_hash_password
from services.security import verify_password as secure_verify_password

def get_user_by_username(username: str):
    user = users_collection.find_one({"username": username})
    return User(**user) if user else None

def get_user_by_email(email: str):
    user = users_collection.find_one({"email": email})
    return User(**user) if user else None

def verify_password(plain_password, hashed_password):
    return secure_verify_password(plain_password, hashed_password)

def hash_password(password):
    return secure_hash_password(password)

def create_user(user_data):
    if get_user_by_username(user_data.username) or get_user_by_email(user_data.email):
        return None

    user_dict = user_data.dict()
    user_dict["password_hash"] = hash_password(user_dict["password_hash"])
    user_dict["created_at"] = datetime.now(timezone.utc)
    user_dict["updated_at"] = datetime.now(timezone.utc)
    result = users_collection.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return User(**user_dict)
    
def update_user(user_id, user_data):
    user_dict = user_data.dict()
    user_dict["updated_at"] = datetime.utcnow()
    users_collection.update_one({"_id": user_id}, {"$set": user_dict})
    return get_user_by_username(user_dict["username"])
