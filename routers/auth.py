from fastapi import APIRouter, HTTPException
from models.user import User
from services import user_service
from auth.auth_handler import create_access_token

from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: User):
    created = user_service.create_user(user)
    if not created:
        raise HTTPException(status_code=400, detail="User already exists")
    return {"message": "User created"}

@router.post("/login")
def login(login_data: LoginRequest):
    user = user_service.get_user_by_username(login_data.username)
    if not user or not user_service.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
