from pydantic import BaseModel, ConfigDict, Field, config
from typing import Optional
from datetime import datetime



class RegisterRequest(BaseModel):
    """"What a client sends us to register a new user."""
    name: str = Field(
        min_length=1, max_length=100,
        description="User's name",
        examples=["Kodjo Kohn"]
    )
    email: str = Field(
        max_length=255,
        description="User's email",
        examples=["KodjoKohn@yahoo.fr"]
    )
    password: str = Field(
        min_length=8, max_length=72,
        description="User's password",
        examples=["Kodjohn65!"]
    )




class UserResponse(BaseModel):
    """"What we send back after storing a new user."""
    id: int
    name: str
    email: str
    is_active: bool
    created_at: Optional[datetime] = None



    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra = {
            "example": {
                "id": 1,
                "name":"Kodjo Kohn" ,
                "email": "KodjoKohn@yahoo.fr",
                "is_active": True,
                "created_at":  "2026-09-06T0:30:00",         
            }
        },
    )