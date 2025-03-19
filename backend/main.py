# main.py
from fastapi import FastAPI, Depends, HTTPException, status ,Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
from bson import ObjectId
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, ValidationError  # Add this

load_dotenv()  # Load .env file

from fastapi.middleware.cors import CORSMiddleware  # Add this import

app = FastAPI(root_path="/api")
from mangum import Mangum
handler = Mangum(app)

# Add CORS middleware BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (temporary for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# The rest of your existing code...

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = "movie_db"
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Security setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv("SECRET_KEY", "5ba6d2ba997729a5a8ed909ffd2d483d395401ceacb43dff82272c73cb010958")

# Models
class User(BaseModel):
    username: str
    email: EmailStr
    disabled: bool = False
    role: str = "user"

class UserInDB(User):
    hashed_password: str

class Movie(BaseModel):
    title: str
    year: int
    genre: str
    director: str
    cast: list[str]
    rating: float
    description: Optional[str] = None

class MovieInDB(Movie):
    id: str

# Create indexes
@app.on_event("startup")
async def create_indexes():
    await db.movies.create_index([("title", TEXT), ("genre", TEXT), ("director", TEXT)])

# Auth functions
# Replace the existing get_current_user function with:
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserInDB(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Routes
# Update login endpoint
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_doc = await db.users.find_one({"username": form_data.username})
    if not user_doc:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Password verification
    if not verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": user_doc["username"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/movies/", response_model=MovieInDB)
async def create_movie(movie: Movie, admin: User = Depends(get_admin_user)):
    movie_dict = movie.dict()
    result = await db.movies.insert_one(movie_dict)
    return {**movie_dict, "id": str(result.inserted_id)}

@app.get("/movies/", response_model=list[MovieInDB])
async def get_movies(search: Optional[str] = None):
    if search:
        query = {"$text": {"$search": search}}
        movies = await db.movies.find(query).to_list(100)
    else:
        movies = await db.movies.find().to_list(100)
    return [{"id": str(m["_id"]), **m} for m in movies]


@app.put("/movies/{movie_id}", response_model=MovieInDB)
async def update_movie(movie_id: str, movie: Movie, admin: User = Depends(get_admin_user)):
    movie_dict = movie.dict()
    await db.movies.update_one({"_id": ObjectId(movie_id)}, {"$set": movie_dict})
    updated_movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"id": str(updated_movie["_id"]), **updated_movie}


@app.get("/movies/{movie_id}", response_model=MovieInDB)
async def get_movie(movie_id: str):
    movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"id": str(movie["_id"]), **movie}


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


@app.post("/register/", response_model=User)
async def register_user(
    username: str,
    password: str,
    email: EmailStr,
    admin: User = Depends(get_admin_user)
):
    # Check if user exists
    if await db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = get_password_hash(password)
    user_data = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": "user",
        "disabled": False
    }
    
    result = await db.users.insert_one(user_data)
    return {**user_data, "id": str(result.inserted_id)}


# Add below your security setup
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


from jose import jwt
from datetime import datetime, timedelta, timezone

# Add under security setup
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Test cases (save as test_main.py)
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_movies():
    response = client.get("/movies/")
    assert response.status_code == 200

def test_search_movies():
    response = client.get("/movies/?search=action")
    assert response.status_code == 200
"""
