from pydantic import BaseModel, Field, ConfigDict, field_validator




class LoginRequest(BaseModel):
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

    @field_validator("email")
    @classmethod
    def email_needs(cls, v):
        if "@" not in v:
            raise ValueError("must be a valid email address")
        return v 





class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra = {
            "examples": [
                {
                    "access_token": "lKJsOlGcioPnIKUxoihj9gjRthNGYlB",
                    "token_type": "bearer",  
                }       
            ]
        }
    )
        
