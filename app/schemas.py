# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class MovieBase(BaseModel):
    title: str
    description: str
    release_year: int
    genre: str
    director: Optional[str] = None
    imdb_score: Optional[float] = None

class MovieCreate(MovieBase):
    pass

class MovieResponse(MovieBase):
    id: str

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    release_year: Optional[int] = None
    genre: Optional[str] = None
    director: Optional[str] = None
    imdb_score: Optional[float] = None
class UserBase(BaseModel):
    username:str
    email: EmailStr
    
    
class UserCreate(UserBase):
    password : str
    
    
class UserResponse(BaseModel):
    role : str
        
class Token(BaseModel):
    access_token : str
    token_type: str
    
class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None