from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=128)


class UserResponse(BaseModel):
    username: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
