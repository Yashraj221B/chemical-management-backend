from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    username: str
    email: str
    first_name: str = ""
    last_name: str = ""
    password_hash: str = ""
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        validate_by_name = True 
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
