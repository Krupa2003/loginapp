from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        orm_mode = True
